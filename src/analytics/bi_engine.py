"""Deterministic evidence analytics with explicit product-readiness gates."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import COVERAGE_FILE, DATA_DIR
from src.jev.taxonomy import RootCauseStatus
from src.models.record_kind import RecordKind


class BusinessIntelligenceEngine:
    DEFAULT_NORMALIZED_DIR=DATA_DIR/"normalized_v4"; DEFAULT_DECISIONS_FILE=DATA_DIR/"jev"/"live_decisions_v4.json"
    DEFAULT_METRICS_FILE=DATA_DIR/"analytics"/"bi_metrics_v4.json"; DEFAULT_COVERAGE_FILE=COVERAGE_FILE

    def __init__(self, normalized_dir:Optional[Path]=None, decisions_file:Optional[Path]=None, metrics_file:Optional[Path]=None,
                 coverage_file:Optional[Path]=None, workflow_validation_file:Optional[Path]=None, prd_approval_file:Optional[Path]=None,
                 raw_dir:Optional[Path]=None):
        self.normalized_dir=Path(normalized_dir or self.DEFAULT_NORMALIZED_DIR); self.decisions_file=Path(decisions_file or self.DEFAULT_DECISIONS_FILE)
        self.metrics_file=Path(metrics_file or self.DEFAULT_METRICS_FILE); self.coverage_file=Path(coverage_file or self.DEFAULT_COVERAGE_FILE)
        self.workflow_validation_file=Path(workflow_validation_file or DATA_DIR/"validation"/"workflow_validation.json")
        self.prd_approval_file=Path(prd_approval_file or DATA_DIR/"validation"/"prd_approval.json")
        self.raw_dir=Path(raw_dir) if raw_dir else None
        self.normalized_records:List[Dict[str,Any]]=[]; self.decisions_list:List[Dict[str,Any]]=[]; self.coverage={}; self.run_meta={}; self.lineage_errors=[]

    @staticmethod
    def _read_json(path:Path,default):
        try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
        except Exception: return default

    def load_data(self):
        self.normalized_records=[]
        if self.normalized_dir.exists():
            for f in sorted(self.normalized_dir.glob("*.json")):
                item=self._read_json(f,{})
                if item.get("authoritative") is not True or item.get("synthetic") is True or item.get("capture_verified") is not True:
                    raise RuntimeError(f"Invalid normalized evidence: {f}")
                self.normalized_records.append(item)
        decision_doc=self._read_json(self.decisions_file,{})
        self.run_meta={k:decision_doc.get(k) for k in ("run_id","input_fingerprint","generated_at","schema_version")}
        self.decisions_list=[]
        by_norm={x.get("normalized_id"):x for x in self.normalized_records}; self.lineage_errors=[]
        for d in decision_doc.get("decisions",[]):
            if d.get("authoritative") is not True or d.get("decision_engine")!="TYPESAFE_JEV": raise RuntimeError("BI refuses non-authoritative JEV decision")
            n=by_norm.get(d.get("normalized_id"))
            if not n or n.get("capture_id")!=d.get("capture_id") or n.get("source_raw_hash")!=d.get("source_raw_hash") or n.get("platform")!=d.get("source_platform"):
                self.lineage_errors.append(d.get("decision_id")); continue
            self.decisions_list.append(d)
        self.coverage=self._read_json(self.coverage_file,{})

    def compute_total_counts(self):
        posts=[n for n in self.normalized_records if n.get("record_kind")==RecordKind.POST.value]
        comments=[n for n in self.normalized_records if n.get("record_kind") in {RecordKind.COMMENT.value,RecordKind.REPLY.value}]
        interactions=[d for d in self.decisions_list if d.get("evaluation_type")=="interaction"]
        inquiry_intents={"PURCHASE","PRICE_QUERY","STOCK_QUERY","LOCATION_QUERY","DELIVERY_QUERY","PRODUCT_QUERY","CUSTOMIZATION"}
        inquiry_breakdown=Counter(d.get("classified",{}).get("customer_intent") for d in interactions if d.get("classified",{}).get("customer_intent") in inquiry_intents)
        complaints=[d for d in self.decisions_list if d.get("evaluation_type")=="complaint"]
        complaint_signals=[d for d in self.decisions_list if d.get("evaluation_type")=="complaint_signal"]
        page_signals=[d for d in self.decisions_list if d.get("evaluation_type")=="page_intent_signal"]
        return {"total_posts":len(posts),"total_comments":len(comments),"total_structured_comments_replies":len(comments),"total_customer_message_classifications":len(interactions),
                "total_inquiries":sum(inquiry_breakdown.values()),"inquiry_breakdown":dict(inquiry_breakdown),"total_complaints":len(complaints),
                "total_page_complaint_signals":len(complaint_signals),"total_page_intent_signals":len(page_signals),
                "total_normalized_records":len(self.normalized_records),"total_jev_decisions":len(self.decisions_list),"lineage_errors":len(self.lineage_errors)}

    def compute_channel_breakdown(self):
        counts=Counter()
        for d in self.decisions_list:
            if d.get("evaluation_type")!="content": continue
            channel=d.get("classified",{}).get("sales_channel")
            if channel and channel!="UNKNOWN": counts[channel]+=1
        total=sum(counts.values()); pct={k:round(v*100/total,1) for k,v in counts.items()} if total else {}
        return {"channels":dict(counts),"percentages":pct,"primary_channel":counts.most_common(1)[0][0] if counts else "UNKNOWN"}

    def compute_complaint_clustering(self):
        actual={}; signals={}
        for d in self.decisions_list:
            bucket=actual if d.get("evaluation_type")=="complaint" else signals if d.get("evaluation_type")=="complaint_signal" else None
            if bucket is None: continue
            issue=d.get("classified",{}).get("issue_class") or "UNKNOWN"
            row=bucket.setdefault(issue,{"count":0,"capture_ids":[],"content_ids":[]}); row["count"]+=1
            row["capture_ids"].append(d.get("capture_id")); row["content_ids"].append(d.get("content_id"))
        return {"structured_customer_complaints":actual,"page_level_complaint_signals":signals,
                "root_cause_safety_invariant":{"status":RootCauseStatus.UNDETERMINED.value,"verified_root_causes":0}}

    def compute_business_signals(self):
        counts=Counter(); evidence=defaultdict(list)
        for d in self.decisions_list:
            if d.get("evaluation_type")!="business_signal": continue
            for key,value in d.get("classified",{}).items():
                if value is True: counts[key]+=1; evidence[key].append(d.get("capture_id"))
        return {
            "signal_counts": dict(counts),
            "evidence_capture_ids": dict(evidence),
            "total_variants_cataloged": counts.get("signal_new_variant", 0),
        }

    def compute_business_eras(self):
        years=sorted({str(n.get("published_at",""))[:4] for n in self.normalized_records if str(n.get("published_at",""))[:4].isdigit()})
        return [] if len(years)<3 else [{"status":"PROPOSED_REQUIRES_ANALYSIS","observed_years":years,"note":"No era boundary asserted without change-point analysis and human review."}]

    def _gates(self):
        workflow=self._read_json(self.workflow_validation_file,{})
        approval=self._read_json(self.prd_approval_file,{})
        workflows=workflow.get("workflows",[]) if isinstance(workflow,dict) else []
        validated=[x for x in workflows if x.get("status") in {"VALIDATED","PILOT_READY"}]
        integrity_pass=not self.lineage_errors and all(n.get("capture_verified") is True for n in self.normalized_records)
        evidence_usable=integrity_pass and bool(self.normalized_records) and bool(self.decisions_list)
        workflow_sufficiency=bool(validated)
        internal_validation=bool(validated) and all(x.get("owner_or_team_validated") is True for x in validated)
        human_approval=approval.get("approved") is True and bool(approval.get("approved_by"))
        return {"integrity":integrity_pass,"evidence_usability":evidence_usable,"workflow_sufficiency":workflow_sufficiency,
                "internal_validation":internal_validation,"human_prd_approval":human_approval,
                "ready_for_prd":all((integrity_pass,evidence_usable,workflow_sufficiency,internal_validation,human_approval))}

    def run_all(self):
        self.load_data(); gates=self._gates()
        output={"engine_version":"4.0.0","generated_at":datetime.now(timezone.utc).isoformat(),"run_id":self.run_meta.get("run_id"),
                "input_fingerprint":self.run_meta.get("input_fingerprint"),"evidence_only":True,"gates":gates,
                "coverage_summary":{"total_sources":self.coverage.get("total_sources",len(self.coverage.get("sources",[]))),
                                    "status_counts":dict(Counter(x.get("status") for x in self.coverage.get("sources",[])))},
                "authoritative_for_prd":gates["ready_for_prd"],"total_counts":self.compute_total_counts(),
                "channel_breakdown":self.compute_channel_breakdown(),"complaint_clusters":self.compute_complaint_clustering(),
                "business_eras":self.compute_business_eras(),"business_signals":self.compute_business_signals()}
        output["status"] = (
            "READY_FOR_PRD" if gates["ready_for_prd"]
            else "READY_FOR_DISCOVERY" if gates["evidence_usability"]
            else "BLOCKED_INTEGRITY" if not gates["integrity"]
            else "PARTIAL_EVIDENCE_ONLY"
        )
        self.metrics_file.parent.mkdir(parents=True,exist_ok=True); tmp=self.metrics_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8"); tmp.replace(self.metrics_file); return output

    def run_analytics(self): return self.run_all()


BusinessIntelligenceEngineV2=BusinessIntelligenceEngine

if __name__=="__main__": print(json.dumps(BusinessIntelligenceEngine().run_all(),indent=2,ensure_ascii=False))
