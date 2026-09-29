"""Optional live JEV classification of redacted local discovery leads."""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from src.config import DATA_DIR, LOCAL_DISCOVERY_ENABLED
from src.jev.engine import JevEngine

SOURCE=DATA_DIR/"local_discovery"/"candidates.json"
OUTPUT=DATA_DIR/"jev"/"local_discovery_decisions.json"
URL_SEEDS=DATA_DIR/"local_discovery"/"public_url_seeds.json"

def _now(): return datetime.now(timezone.utc).isoformat()
def _candidate_text(item:dict)->str:
    if item.get("candidate_type")=="browser_history_url": return f"Discovery URL: {item.get('url','')}\nPage title: {item.get('title','')}"
    return f"Local project artifact: {item.get('path','')}\nRedacted excerpt:\n{item.get('excerpt','')}"

def main(enabled:bool|None=None)->dict:
    enabled=LOCAL_DISCOVERY_ENABLED if enabled is None else bool(enabled)
    if not enabled: return {"status":"DISABLED","count":0,"authoritative_for_business_truth":False,"models":{}}
    if not SOURCE.exists(): return {"status":"NO_DISCOVERY_DATA","count":0,"authoritative_for_business_truth":False,"models":{}}
    payload=json.loads(SOURCE.read_text(encoding="utf-8")); candidates=payload.get("candidates",[]); engine=JevEngine(force_fallback=False)
    decisions=[]; public_urls=[]
    for idx,item in enumerate(candidates,start=1):
        result=engine.evaluate_bundle(_candidate_text(item)[:6000],metadata={"lane":"LOCAL_DISCOVERY_ONLY","candidate_type":item.get("candidate_type")})
        decisions.append({"discovery_id":f"local_{idx:04d}","candidate_type":item.get("candidate_type"),
                          "source_authoritative":False,"business_fact_authoritative":False,"decision_engine":"TYPESAFE_JEV",
                          "model":result.get("model_resolved") or result.get("model"),"classified":result.get("classified",{}),
                          "answers":result.get("answers",{}),"root_cause_status":"UNDETERMINED","candidate":item,"evaluated_at":_now()})
        if item.get("candidate_type")=="browser_history_url" and item.get("url"): public_urls.append(item["url"])
    summary={"generated_at":_now(),"status":"COMPLETE" if decisions else "NO_DISCOVERY_DATA","authoritative_for_business_truth":False,
             "decision_engine":"TYPESAFE_JEV" if decisions else "NOT_RUN","count":len(decisions),
             "models":dict(Counter(d["model"] for d in decisions)),"candidate_types":dict(Counter(d["candidate_type"] for d in decisions)),
             "brands":dict(Counter(d["classified"].get("brand","UNKNOWN") for d in decisions)),
             "business_functions":dict(Counter(d["classified"].get("business_function","UNKNOWN") for d in decisions)),"decisions":decisions}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    URL_SEEDS.parent.mkdir(parents=True,exist_ok=True); URL_SEEDS.write_text(json.dumps({"generated_at":_now(),"urls":sorted(set(public_urls))},indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="decisions"},indent=2,ensure_ascii=False)); return summary

if __name__=="__main__": main(enabled=True)
