"""Authoritative JEV batch runner. Production evidence only; no synthetic fallback."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.evidence.integrity import EvidenceIntegrityError, validate_raw_record
from src.jev.engine import JevEngine
from src.jev.taxonomy import RootCauseStatus

logger = logging.getLogger("JevBatchRunner")


class JevBatchRunner:
    DEFAULT_RAW_DIR = Path("D:/ABANGCOLEK/data/raw")
    DEFAULT_NORMALIZED_DIR = Path("D:/ABANGCOLEK/data/normalized_v2")
    DEFAULT_OUTPUT_FILE = Path("D:/ABANGCOLEK/data/jev/live_decisions.json")

    def __init__(self, raw_dir: Optional[Path] = None, normalized_dir: Optional[Path] = None,
                 output_file: Optional[Path] = None, engine: Optional[JevEngine] = None,
                 force_fallback: bool = False):
        self.raw_dir = Path(raw_dir or self.DEFAULT_RAW_DIR)
        self.normalized_dir = Path(normalized_dir or self.DEFAULT_NORMALIZED_DIR)
        self.output_file = Path(output_file or self.DEFAULT_OUTPUT_FILE)
        self.engine = engine or JevEngine(force_fallback=force_fallback)
        self.force_fallback = force_fallback
        self.total_raw_captures_loaded = 0
        self.duplicate_snapshots_suppressed = 0

    def load_raw_sources(self) -> List[Dict[str, Any]]:
        captures: List[Dict[str, Any]] = []
        if not self.raw_dir.exists():
            return captures
        for file_path in sorted(self.raw_dir.glob("*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                record = json.load(f)
            validate_raw_record(record, require_authoritative=True)
            record["_filepath"] = str(file_path)
            captures.append(record)
        self.total_raw_captures_loaded = len(captures)
        latest: Dict[tuple, Dict[str, Any]] = {}
        for record in captures:
            key = (
                record.get("source_platform"),
                record.get("source_id") or record.get("source_native_id"),
                record.get("collector"),
            )
            previous = latest.get(key)
            if previous is None or str(record.get("captured_at", "")) >= str(previous.get("captured_at", "")):
                latest[key] = record
        records = list(latest.values())
        self.duplicate_snapshots_suppressed = max(0, len(captures) - len(records))
        return records

    @staticmethod
    def _extract_text(record: Dict[str, Any]) -> str:
        payload = record.get("raw_payload", {})
        if isinstance(payload, str):
            return payload.strip()
        if not isinstance(payload, dict):
            return ""
        for key in ("text", "visible_text", "post_text", "video_description", "title", "caption", "description", "message"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("registration_record", "listing", "event_record"):
            value = payload.get(key)
            if isinstance(value, dict) and value:
                return json.dumps(value, ensure_ascii=False, sort_keys=True)
        return ""

    def normalize_verified_records(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        for old in self.normalized_dir.glob("*.json"):
            old.unlink()
        items: List[Dict[str, Any]] = []
        for raw in raw_records:
            text = self._extract_text(raw)
            if not text:
                continue
            item = {
                "normalized_id": f"norm_{raw['source_id']}",
                "source_id": raw["source_id"],
                "source_native_id": raw.get("source_native_id"),
                "source_raw_hash": raw["raw_hash"],
                "platform": raw.get("source_platform"),
                "record_type": raw.get("source_type", "raw_record"),
                "text": text,
                "published_at": raw.get("published_at", ""),
                "provenance_verified": True,
                "authoritative": True,
                "synthetic": False,
            }
            items.append(item)
            with open(self.normalized_dir / f"{item['normalized_id']}.json", "w", encoding="utf-8") as f:
                json.dump(item, f, indent=2, ensure_ascii=False)
        return items

    @staticmethod
    def _assert_live(decision: Dict[str, Any]) -> Dict[str, Any]:
        model = str(decision.get("model", ""))
        if not model or "fallback" in model.lower():
            raise RuntimeError("Authoritative JEV run refused non-live/fallback decision")
        decision["decision_engine"] = "TYPESAFE_JEV"
        decision["authoritative"] = True
        decision["model_resolved"] = model
        return decision

    def _wrap(self, run_id: str, norm: Dict[str, Any], kind: str, result: Dict[str, Any]) -> Dict[str, Any]:
        result = self._assert_live(result)
        return {
            "decision_id": f"dec_{kind}_{uuid4().hex[:10]}",
            "run_id": run_id,
            "source_evidence_id": norm["source_id"],
            "source_raw_hash": norm["source_raw_hash"],
            "normalized_id": norm["normalized_id"],
            "source_platform": norm.get("platform"),
            "evaluation_type": kind,
            "taxonomy_version": self.engine.taxonomy_version,
            "question_set_version": result.get("question_set_version", "2.0.0"),
            "model": result["model_resolved"],
            "decision_engine": "TYPESAFE_JEV",
            "authoritative": True,
            "cached": result.get("cached", False),
            "answers": result.get("answers", {}),
            "classified": result.get("classified", {}),
            "usage": result.get("usage", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def run_all(self) -> Dict[str, Any]:
        raw_records = self.load_raw_sources()
        normalized = self.normalize_verified_records(raw_records)
        run_id = f"jev_run_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}_{uuid4().hex[:6]}"
        decisions: List[Dict[str, Any]] = []
        for norm in normalized:
            text = norm["text"]
            rt = str(norm.get("record_type", "")).lower()
            bundle = self.engine.evaluate_bundle(text)
            cls = bundle.get("classified", {})

            def view(keys):
                out = dict(bundle)
                out["classified"] = {k: cls.get(k) for k in keys}
                return out

            decisions.append(self._wrap(run_id, norm, "content", view([
                "is_commercial", "brand", "business_function", "sales_channel", "exposes_production"
            ])))
            decisions.append(self._wrap(run_id, norm, "business_signal", view([
                "signal_new_variant", "signal_new_territory", "signal_mobile_team", "signal_recruitment"
            ])))

            if "comment" in rt or "reply" in rt or rt == "public_post_snapshot":
                decisions.append(self._wrap(run_id, norm, "interaction", view([
                    "customer_intent", "is_purchase_intent", "is_location_query", "is_complaint"
                ])))
                if cls.get("is_complaint"):
                    wrapped = self._wrap(run_id, norm, "complaint", view([
                        "is_complaint", "issue_class", "possible_process_stage", "requires_immediate_review"
                    ]))
                    wrapped["root_cause_status"] = RootCauseStatus.UNDETERMINED.value
                    wrapped["root_cause_rule_enforced"] = True
                    decisions.append(wrapped)

        output = {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "authoritative": True,
            "decision_engine": "TYPESAFE_JEV" if decisions else "NOT_RUN",
            "status": "COMPLETE" if decisions else "BLOCKED_NO_EVIDENCE",
            "total_raw_captures_loaded": self.total_raw_captures_loaded,
            "duplicate_snapshots_suppressed": self.duplicate_snapshots_suppressed,
            "total_raw_processed": len(raw_records),
            "total_normalized_processed": len(normalized),
            "total_decisions": len(decisions),
            "decisions": decisions,
        }
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.output_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        tmp.replace(self.output_file)
        return output


JevBatchRunnerV2 = JevBatchRunner


def main() -> None:
    result = JevBatchRunner(force_fallback=False).run_all()
    print(json.dumps({k: result[k] for k in ("status", "total_raw_processed", "total_decisions")}, indent=2))


if __name__ == "__main__":
    main()
