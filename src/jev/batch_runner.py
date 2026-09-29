"""Authoritative JEV batch runner with stable IDs and exact lineage."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.config import DATA_DIR, NORMALIZER_VERSION, RAW_DIR
from src.evidence.integrity import business_interpretation_usable, evidence_quality_score, validate_raw_record
from src.jev.engine import JevEngine
from src.jev.taxonomy import RootCauseStatus
from src.models.record_kind import RecordKind


class JevBatchRunner:
    DEFAULT_RAW_DIR = RAW_DIR
    DEFAULT_NORMALIZED_DIR = DATA_DIR / "normalized_v4"
    DEFAULT_OUTPUT_FILE = DATA_DIR / "jev" / "live_decisions_v4.json"

    def __init__(self, raw_dir: Optional[Path] = None, normalized_dir: Optional[Path] = None,
                 output_file: Optional[Path] = None, engine: Optional[JevEngine] = None,
                 force_fallback: bool = False):
        self.raw_dir=Path(raw_dir or self.DEFAULT_RAW_DIR); self.normalized_dir=Path(normalized_dir or self.DEFAULT_NORMALIZED_DIR)
        self.output_file=Path(output_file or self.DEFAULT_OUTPUT_FILE); self.engine=engine or JevEngine(force_fallback=force_fallback)
        self.force_fallback=force_fallback; self.total_raw_captures_loaded=0; self.duplicate_snapshots_suppressed=0; self.unusable_captures_suppressed=0

    def load_raw_sources(self) -> List[Dict[str, Any]]:
        from src.evidence.identity import ids_for_record
        captures=[]
        if not self.raw_dir.exists(): return captures
        for path in sorted(self.raw_dir.glob("*.json")):
            rec=json.loads(path.read_text(encoding="utf-8")); verification=validate_raw_record(rec,require_authoritative=True)
            rec["_filepath"]=str(path); rec["_verification"]=verification; rec["_ids"]=ids_for_record(rec)
            captures.append(rec)
        self.total_raw_captures_loaded=len(captures)
        eligible=[r for r in captures if business_interpretation_usable(r)]
        self.unusable_captures_suppressed=len(captures)-len(eligible)
        best: Dict[str, Dict[str, Any]]={}
        for rec in eligible:
            cid=rec["_ids"]["content_id"]
            if cid not in best or evidence_quality_score(rec)>evidence_quality_score(best[cid]): best[cid]=rec
        selected=sorted(best.values(),key=lambda r:r["_ids"]["content_id"])
        self.duplicate_snapshots_suppressed=max(0,len(eligible)-len(selected))
        return selected

    @staticmethod
    def _deep_text(value: Any) -> str:
        if isinstance(value,str): return value.strip()
        if isinstance(value,dict):
            for key in ("text","caption","message","description","video_description","title","content"):
                if key in value:
                    text=JevBatchRunner._deep_text(value[key])
                    if text: return text
            for child in value.values():
                text=JevBatchRunner._deep_text(child)
                if text: return text
        if isinstance(value,list):
            for child in value:
                text=JevBatchRunner._deep_text(child)
                if text: return text
        return ""

    @staticmethod
    def _extract_text(record: Dict[str, Any]) -> str:
        payload=record.get("raw_payload",{})
        if isinstance(payload,str): return payload.strip()
        if not isinstance(payload,dict): return ""
        for key in ("text","caption","message","video_description","description","visible_text","title"):
            value=payload.get(key)
            if isinstance(value,str) and value.strip(): return value.strip()
        if "export_payload" in payload: return JevBatchRunner._deep_text(payload["export_payload"])
        return JevBatchRunner._deep_text(payload)

    def normalize_verified_records(self, raw_records: List[Dict[str, Any]], *, run_id: Optional[str]=None, input_fingerprint: Optional[str]=None) -> List[Dict[str, Any]]:
        from src.evidence.identity import ids_for_record
        self.normalized_dir.mkdir(parents=True,exist_ok=True)
        items=[]
        for raw in raw_records:
            text=self._extract_text(raw)
            if not text: continue
            ids=raw.get("_ids") or ids_for_record(raw)
            item={
                "schema_version":"4.0.0", "normalizer_version":NORMALIZER_VERSION, "run_id":run_id, "input_fingerprint":input_fingerprint,
                "normalized_id":ids["normalized_id"], "content_id":ids["content_id"], "capture_id":ids["capture_id"],
                "source_id":raw.get("source_id"), "source_native_id":raw.get("source_native_id"), "source_raw_hash":raw["raw_hash"],
                "platform":raw.get("source_platform"), "source_type":raw.get("source_type","raw_record"), "record_kind":ids["record_kind"],
                "text":text, "published_at":raw.get("published_at",""), "captured_at":raw.get("captured_at",""),
                "source_url":raw.get("source_url",""), "collector":raw.get("collector"),
                "payload_hash_verified":True, "capture_verified":bool(raw.get("_verification",{}).get("capture_verified")),
                "claim_verified":False, "provenance_verified":True, "authoritative":True, "synthetic":False,
            }
            items.append(item)
            (self.normalized_dir/f"{item['normalized_id']}.json").write_text(json.dumps(item,indent=2,ensure_ascii=False),encoding="utf-8")
        return items

    @staticmethod
    def _assert_live(result: Dict[str, Any]) -> Dict[str, Any]:
        if result.get("authoritative") is not True or result.get("decision_engine")!="TYPESAFE_JEV":
            raise RuntimeError("Authoritative JEV run refused non-live decision")
        model=result.get("model_resolved") or result.get("model")
        if not isinstance(model,str) or not model or "fallback" in model.lower():
            raise RuntimeError("Authoritative JEV response has no valid resolved model")
        if not isinstance(result.get("answers"),dict) or not result["answers"]:
            raise RuntimeError("Authoritative JEV response has no validated answers")
        return result

    @staticmethod
    def _confidence(result: Dict[str, Any], keys: List[str]) -> Optional[float]:
        values=[]
        for key in keys:
            answer=(result.get("answers") or {}).get(key,{})
            if isinstance(answer.get("confidence"),(int,float)): values.append(float(answer["confidence"]))
            elif isinstance(answer.get("noul"),(int,float)): values.append(abs(float(answer["noul"])-0.5)*2.0)
        return round(sum(values)/len(values),4) if values else None

    def _wrap(self, run_id: str, norm: Dict[str, Any], kind: str, result: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        result=self._assert_live(result)
        return {
            "decision_id":f"dec_{kind}_{uuid4().hex[:12]}", "run_id":run_id,
            "source_evidence_id":norm["capture_id"], "content_id":norm["content_id"], "capture_id":norm["capture_id"],
            "source_native_id":norm.get("source_native_id"), "source_raw_hash":norm["source_raw_hash"], "normalized_id":norm["normalized_id"],
            "source_platform":norm.get("platform"), "record_kind":norm.get("record_kind"), "evaluation_type":kind,
            "taxonomy_version":self.engine.taxonomy_version, "question_set_version":result.get("question_set_version"),
            "prompt_version":result.get("prompt_version"), "model_requested":result.get("model_requested"),
            "model":result.get("model_resolved") or result.get("model"), "model_resolved":result.get("model_resolved") or result.get("model"),
            "decision_engine":"TYPESAFE_JEV", "authoritative":True, "cached":bool(result.get("cached")),
            "source_execution":result.get("source_execution"), "evaluated_at":result.get("evaluated_at"),
            "confidence":self._confidence(result,keys), "answers":{k:result["answers"][k] for k in keys},
            "classified":{k:(result.get("classified") or {}).get(k) for k in keys}, "usage":result.get("usage",{}),
            "timestamp":datetime.now(timezone.utc).isoformat(),
        }

    def run_all(self, *, run_id: Optional[str] = None, raw_records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        selected=raw_records if raw_records is not None else self.load_raw_sources()
        rid=run_id or f"jev_run_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}_{uuid4().hex[:6]}"
        input_fingerprint=hashlib.sha256("\n".join(sorted(r["raw_hash"] for r in selected)).encode()).hexdigest() if selected else None
        normalized=self.normalize_verified_records(selected,run_id=rid,input_fingerprint=input_fingerprint)
        decisions=[]
        for norm in normalized:
            text=norm["text"]; bundle=self.engine.evaluate_bundle(text,metadata={"record_kind":norm["record_kind"],"platform":norm.get("platform")})
            cls=bundle.get("classified",{})
            def add(kind,keys):
                view=dict(bundle); view["classified"]={k:cls[k] for k in keys}; decisions.append(self._wrap(rid,norm,kind,view,keys))
            add("content",["is_commercial","brand","business_function","sales_channel","exposes_production"])
            add("business_signal",["signal_new_variant","signal_new_territory","signal_mobile_team","signal_recruitment"])
            rk=norm.get("record_kind")
            if rk in {RecordKind.COMMENT.value,RecordKind.REPLY.value}:
                add("interaction",["customer_intent","is_purchase_intent","is_location_query","is_complaint"])
                if cls["is_complaint"]:
                    add("complaint",["is_complaint","issue_class","possible_process_stage","requires_immediate_review"])
                    decisions[-1]["root_cause_status"]=RootCauseStatus.UNDETERMINED.value; decisions[-1]["root_cause_rule_enforced"]=True
            elif rk==RecordKind.POST.value:
                add("page_intent_signal",["customer_intent","is_purchase_intent","is_location_query","is_complaint"])
                if cls["is_complaint"]:
                    add("complaint_signal",["is_complaint","issue_class","possible_process_stage","requires_immediate_review"])
                    decisions[-1]["root_cause_status"]=RootCauseStatus.UNDETERMINED.value; decisions[-1]["root_cause_rule_enforced"]=True
        output={
            "run_id":rid,"generated_at":datetime.now(timezone.utc).isoformat(),"schema_version":"4.0.0","authoritative":True,
            "decision_engine":"TYPESAFE_JEV" if decisions else "NOT_RUN","status":"COMPLETE" if decisions else "BLOCKED_NO_EVIDENCE",
            "input_fingerprint":input_fingerprint,"total_raw_captures_loaded":self.total_raw_captures_loaded or len(selected),
            "unusable_captures_suppressed":self.unusable_captures_suppressed,"duplicate_snapshots_suppressed":self.duplicate_snapshots_suppressed,
            "total_raw_processed":len(selected),"total_normalized_processed":len(normalized),"normalized_file_count":len(list(self.normalized_dir.glob('*.json'))),
            "total_decisions":len(decisions),"decisions":decisions,
        }
        self.output_file.parent.mkdir(parents=True,exist_ok=True); tmp=self.output_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8"); tmp.replace(self.output_file)
        return output


JevBatchRunnerV2=JevBatchRunner


def main():
    result=JevBatchRunner(force_fallback=False).run_all()
    print(json.dumps({k:result[k] for k in ("status","total_raw_processed","total_normalized_processed","normalized_file_count","total_decisions")},indent=2))


if __name__=="__main__": main()
