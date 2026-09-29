"""Create non-authoritative templates for owner/team workflow validation."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from src.config import DATA_DIR

WORKFLOW_FILE=DATA_DIR/"validation"/"workflow_validation.json"
APPROVAL_FILE=DATA_DIR/"validation"/"prd_approval.json"

QUESTIONS=[
    ("ORDER_FLOW","One real order from receipt to close"),
    ("STOCK_OWNERSHIP","Stock ownership and movement across HQ/agent/event/customer"),
    ("AGENT_RESTOCK","Agent/reseller approval, restock and reconciliation"),
    ("COMPLAINT_TRACE","Complaint to product/order/lot/batch trace"),
    ("PRODUCTION_TRACE","Supplier/fruit lot to preparation/pack/QC trace"),
    ("TRANSPORT_TRACE","Dispatch, transport, handover and receipt"),
    ("EVENT_CREW","Location/event, stock and crew scheduling/reconciliation"),
    ("PAYMENT_CLOSE","Cash/COD/online payment verification and close"),
]

def _now(): return datetime.now(timezone.utc).isoformat()
def ensure_validation_templates()->dict:
    WORKFLOW_FILE.parent.mkdir(parents=True,exist_ok=True)
    if not WORKFLOW_FILE.exists():
        workflows=[{"workflow_id":qid,"name":name,"status":"NOT_STARTED","owner_or_team_validated":False,
                    "example_transaction_id":None,"roles":[],"steps":[],"decisions":[],"exceptions":[],"documents_or_records":[],
                    "supporting_evidence_ids":[],"validated_by":None,"validated_at":None,"notes":None} for qid,name in QUESTIONS]
        WORKFLOW_FILE.write_text(json.dumps({"schema_version":"1.0.0","created_at":_now(),"workflows":workflows},indent=2,ensure_ascii=False),encoding="utf-8")
    if not APPROVAL_FILE.exists():
        APPROVAL_FILE.write_text(json.dumps({"schema_version":"1.0.0","approved":False,"approved_by":None,"approved_at":None,
                                             "scope":None,"notes":"Final PRD requires explicit human approval after validated workflow evidence."},indent=2),encoding="utf-8")
    return {"workflow_file":str(WORKFLOW_FILE),"approval_file":str(APPROVAL_FILE)}

if __name__=="__main__": print(json.dumps(ensure_validation_templates(),indent=2))
