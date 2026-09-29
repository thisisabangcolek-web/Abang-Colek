"""Evidence-only deterministic business intelligence. No synthetic fallbacks or invented minima."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.evidence.integrity import validate_raw_record
from src.jev.taxonomy import RootCauseStatus


class BusinessIntelligenceEngine:
    DEFAULT_RAW_DIR = Path("D:/ABANGCOLEK/data/raw")
    DEFAULT_NORMALIZED_DIR = Path("D:/ABANGCOLEK/data/normalized_v2")
    DEFAULT_DECISIONS_FILE = Path("D:/ABANGCOLEK/data/jev/live_decisions.json")
    DEFAULT_METRICS_FILE = Path("D:/ABANGCOLEK/data/analytics/bi_metrics_v2.json")
    DEFAULT_COVERAGE_FILE = Path("D:/ABANGCOLEK/data/coverage/collection_manifest.json")

    def __init__(self, raw_dir: Optional[Path] = None, normalized_dir: Optional[Path] = None,
                 decisions_file: Optional[Path] = None, metrics_file: Optional[Path] = None,
                 coverage_file: Optional[Path] = None):
        self.raw_dir = Path(raw_dir or self.DEFAULT_RAW_DIR)
        self.normalized_dir = Path(normalized_dir or self.DEFAULT_NORMALIZED_DIR)
        self.decisions_file = Path(decisions_file or self.DEFAULT_DECISIONS_FILE)
        self.metrics_file = Path(metrics_file or self.DEFAULT_METRICS_FILE)
        self.coverage_file = Path(coverage_file or self.DEFAULT_COVERAGE_FILE)
        self.raw_records: List[Dict[str, Any]] = []
        self.normalized_records: List[Dict[str, Any]] = []
        self.decisions_list: List[Dict[str, Any]] = []
        self.coverage: Dict[str, Any] = {}

    def load_data(self) -> None:
        self.raw_records = []
        if self.raw_dir.exists():
            for f in sorted(self.raw_dir.glob("*.json")):
                with open(f, "r", encoding="utf-8") as fp:
                    item = json.load(fp)
                validate_raw_record(item, require_authoritative=True)
                self.raw_records.append(item)

        self.normalized_records = []
        if self.normalized_dir.exists():
            for f in sorted(self.normalized_dir.glob("*.json")):
                with open(f, "r", encoding="utf-8") as fp:
                    item = json.load(fp)
                if item.get("synthetic") is True or item.get("authoritative") is not True:
                    raise RuntimeError(f"Non-authoritative normalized record blocked: {f}")
                self.normalized_records.append(item)

        self.decisions_list = []
        if self.decisions_file.exists():
            with open(self.decisions_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            for d in data.get("decisions", []):
                if d.get("authoritative") is not True or d.get("decision_engine") != "TYPESAFE_JEV":
                    raise RuntimeError("BI refuses non-authoritative or fallback JEV decision")
                self.decisions_list.append(d)

        self.coverage = {}
        if self.coverage_file.exists():
            with open(self.coverage_file, "r", encoding="utf-8") as fp:
                self.coverage = json.load(fp)

    def compute_total_counts(self) -> Dict[str, Any]:
        posts = [n for n in self.normalized_records if str(n.get("record_type", "")).lower() in {"post", "public_post", "social_post", "video", "owner_export"}]
        comments = [n for n in self.normalized_records if "comment" in str(n.get("record_type", "")).lower() or "reply" in str(n.get("record_type", "")).lower()]
        complaints = [d for d in self.decisions_list if d.get("evaluation_type") == "complaint"]
        intents = Counter()
        for d in self.decisions_list:
            if d.get("evaluation_type") == "interaction":
                intent = d.get("classified", {}).get("customer_intent")
                if intent and intent != "UNKNOWN":
                    intents[intent] += 1
        return {
            "total_posts": len(posts),
            "total_comments": len(comments),
            "total_complaints": len(complaints),
            "total_inquiries": sum(intents.values()),
            "inquiry_breakdown": dict(intents),
            "total_raw_evidence_records": len(self.raw_records),
            "total_normalized_records": len(self.normalized_records),
            "total_jev_decisions": len(self.decisions_list),
        }

    def compute_channel_breakdown(self) -> Dict[str, Any]:
        counts = Counter()
        for d in self.decisions_list:
            if d.get("evaluation_type") != "content":
                continue
            channel = d.get("classified", {}).get("sales_channel")
            if channel and channel != "UNKNOWN":
                counts[channel] += 1
        total = sum(counts.values())
        percentages = {k: round(v * 100.0 / total, 1) for k, v in counts.items()} if total else {}
        return {"channels": dict(counts), "percentages": percentages,
                "primary_channel": counts.most_common(1)[0][0] if counts else "UNKNOWN"}

    def compute_complaint_clustering(self) -> Dict[str, Any]:
        clusters: Dict[str, Dict[str, Any]] = {}
        for d in self.decisions_list:
            if d.get("evaluation_type") != "complaint":
                continue
            issue = d.get("classified", {}).get("issue_class") or "UNKNOWN"
            c = clusters.setdefault(issue, {"count": 0, "evidence_ids": [], "issue_class": issue})
            c["count"] += 1
            c["evidence_ids"].append(d.get("source_evidence_id"))
        return {
            "issue_clusters": clusters,
            "root_cause_safety_invariant": {"status": RootCauseStatus.UNDETERMINED.value,
                                             "verified_root_causes": 0},
        }

    def compute_business_eras(self) -> List[Dict[str, Any]]:
        # Era boundaries require longitudinal change-point evidence. Never hard-code them.
        years = sorted({str(n.get("published_at", ""))[:4] for n in self.normalized_records if str(n.get("published_at", ""))[:4].isdigit()})
        if len(years) < 3:
            return []
        return [{"status": "PROPOSED_REQUIRES_ANALYSIS", "observed_years": years,
                 "note": "No deterministic era boundary asserted without change-point analysis."}]

    def compute_business_signals(self) -> Dict[str, Any]:
        signals = Counter()
        evidence = defaultdict(list)
        for d in self.decisions_list:
            if d.get("evaluation_type") != "business_signal":
                continue
            for key, value in d.get("classified", {}).items():
                if value is True:
                    signals[key] += 1
                    evidence[key].append(d.get("source_evidence_id"))
        return {"signal_counts": dict(signals), "evidence_ids": dict(evidence),
                "total_variants_cataloged": 0, "discovered_product_variants": []}

    def _coverage_ready(self) -> bool:
        sources = self.coverage.get("sources", []) if isinstance(self.coverage, dict) else []
        return bool(sources) and all(s.get("status") in {"COMPLETE_VERIFIED", "COMPLETE_WITHIN_API_SCOPE"} for s in sources)

    def run_all(self) -> Dict[str, Any]:
        self.load_data()
        output = {
            "engine_version": "3.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "evidence_only": True,
            "coverage_ready": self._coverage_ready(),
            "authoritative_for_prd": self._coverage_ready() and bool(self.raw_records),
            "total_counts": self.compute_total_counts(),
            "channel_breakdown": self.compute_channel_breakdown(),
            "complaint_clusters": self.compute_complaint_clustering(),
            "business_eras": self.compute_business_eras(),
            "business_signals": self.compute_business_signals(),
        }
        output["status"] = "READY_FOR_DISCOVERY" if output["authoritative_for_prd"] else "PARTIAL_EVIDENCE_ONLY"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return output

    def run_analytics(self) -> Dict[str, Any]:
        return self.run_all()


BusinessIntelligenceEngineV2 = BusinessIntelligenceEngine

if __name__ == "__main__":
    print(json.dumps(BusinessIntelligenceEngine().run_all(), indent=2, ensure_ascii=False))
