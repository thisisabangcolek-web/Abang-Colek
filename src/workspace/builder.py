"""Build a static human-review workspace from one processing run."""
from __future__ import annotations
import html, json
from pathlib import Path
from typing import Any, Dict, List

class DiscoveryWorkspaceBuilder:
    def __init__(self,workspace_dir:Path):
        self.root=Path(workspace_dir); self.root.mkdir(parents=True,exist_ok=True)
    @staticmethod
    def _excerpt(text:str,limit:int=600)->str:
        text=" ".join(str(text or "").split()); return text[:limit]+("…" if len(text)>limit else "")
    def build(self,raw_records:List[Dict[str,Any]],normalized:List[Dict[str,Any]],decision_payload:Dict[str,Any],coverage:Dict[str,Any],run_id:str)->Dict[str,Any]:
        by_capture={n["capture_id"]:n for n in normalized}; raw_by_hash={r.get("raw_hash"):r for r in raw_records}
        decisions=decision_payload.get("decisions",[]); by_capture_decisions={}
        for d in decisions: by_capture_decisions.setdefault(d.get("capture_id"),[]).append(d)
        source_library=[]
        for n in normalized:
            raw=raw_by_hash.get(n.get("source_raw_hash"),{})
            source_library.append({"capture_id":n["capture_id"],"content_id":n["content_id"],"normalized_id":n["normalized_id"],
                                   "platform":n.get("platform"),"record_kind":n.get("record_kind"),"source_url":n.get("source_url"),
                                   "published_at":n.get("published_at"),"captured_at":n.get("captured_at"),"collector":n.get("collector"),
                                   "excerpt":self._excerpt(n.get("text")),"raw_hash":n.get("source_raw_hash"),
                                   "capture_verified":n.get("capture_verified"),"decision_count":len(by_capture_decisions.get(n["capture_id"],[])),
                                   "capture_state":(raw.get("raw_payload") or {}).get("capture_state") if isinstance(raw.get("raw_payload"),dict) else None})
        claims=[]
        for d in decisions:
            classified=d.get("classified") or {}
            claims.append({"claim_id":d.get("decision_id"),"epistemic_type":"CLASSIFICATION","evaluation_type":d.get("evaluation_type"),
                           "capture_id":d.get("capture_id"),"content_id":d.get("content_id"),"source_url":by_capture.get(d.get("capture_id"),{}).get("source_url"),
                           "classified":classified,"confidence":d.get("confidence"),"model":d.get("model_resolved") or d.get("model"),
                           "status":"UNREVIEWED","reviewer":None,"review_note":None,"supports_business_fact":False})
        brands={}
        for d in decisions:
            if d.get("evaluation_type")!="content": continue
            brand=(d.get("classified") or {}).get("brand")
            if brand and brand!="UNKNOWN": brands.setdefault(brand,[]).append(d.get("capture_id"))
        entity_review=[{"entity_type":"BRAND_MENTION","name":name,"status":"REQUIRES_HUMAN_CONFIRMATION",
                        "evidence_capture_ids":sorted(set(ids)),"relationship_claim":None} for name,ids in sorted(brands.items())]
        source_status=[{"platform":s.get("platform"),"source":s.get("account") or s.get("source_name"),"status":s.get("status"),
                        "posts":s.get("posts_recovered",0),"comments":s.get("comments_recovered",0),"replies":s.get("replies_recovered",0),
                        "known_gaps":s.get("known_gaps",[])} for s in coverage.get("sources",[])]
        business_questions=[
            ("ORDER_FLOW","How is one real order received, confirmed, fulfilled and closed?"),
            ("STOCK_OWNERSHIP","Who owns stock at HQ, agent, event and customer handoff points?"),
            ("AGENT_RESTOCK","How are agents/resellers approved, restocked and reconciled?"),
            ("COMPLAINT_TRACE","How is a complaint linked to product, order, stock lot or batch?"),
            ("PRODUCTION_TRACE","What records exist from supplier/fruit lot through preparation, packing and QC?"),
            ("TRANSPORT_TRACE","How is stock dispatched, transported, handed over and received?"),
            ("EVENT_CREW","How are locations/events, stock and crew scheduled and reconciled?"),
            ("PAYMENT_CLOSE","How are cash/COD/online payments verified and closed?"),
        ]
        coverage_matrix=[{"question_id":qid,"question":question,"status":"INTERNAL_VALIDATION_REQUIRED",
                          "supporting_capture_ids":[],"missing_evidence":"Owner/team walkthrough plus real transaction records"} for qid,question in business_questions]
        interview_board=[{"question_id":x["question_id"],"question":x["question"],"owner_answer":None,"supporting_evidence_ids":[],
                          "contradicting_evidence_ids":[],"workflow_steps":[],"exceptions":[],"validated_by":None,"validated_at":None,
                          "status":"NOT_STARTED"} for x in coverage_matrix]
        payloads={"source_library.json":source_library,"claim_ledger.json":claims,"coverage_matrix.json":{"sources":source_status,"business_questions":coverage_matrix},
                  "entity_review.json":entity_review,"interview_board.json":interview_board}
        for name,obj in payloads.items(): (self.root/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8")
        rows="".join(f"<tr><td>{html.escape(str(x['platform']))}</td><td>{html.escape(str(x['record_kind']))}</td><td>{html.escape(x['excerpt'])}</td><td><a href='{html.escape(x.get('source_url') or '#')}'>source</a></td><td>{x['decision_count']}</td></tr>" for x in source_library)
        page=f"""<!doctype html><html><head><meta charset='utf-8'><title>ABANGCOLEK Evidence Review</title><style>body{{font-family:Arial,sans-serif;margin:24px;max-width:1500px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;vertical-align:top}}th{{background:#f4f4f4}}code{{background:#f3f3f3;padding:2px 4px}}</style></head><body><h1>ABANGCOLEK Evidence Review</h1><p>Run <code>{html.escape(run_id)}</code>. Machine classifications are not business facts until reviewed.</p><p>Sources: {len(source_library)} | JEV decision views: {len(decisions)} | Claims awaiting review: {len(claims)}</p><p>See JSON files in this folder for claim ledger, entity review, coverage matrix and interview board.</p><table><thead><tr><th>Platform</th><th>Kind</th><th>Evidence excerpt</th><th>Original</th><th>JEV views</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
        (self.root/"index.html").write_text(page,encoding="utf-8")
        summary={"run_id":run_id,"sources":len(source_library),"claims":len(claims),"entity_reviews":len(entity_review),"business_questions":len(coverage_matrix),"index":str((self.root/'index.html').resolve())}
        (self.root/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8"); return summary
