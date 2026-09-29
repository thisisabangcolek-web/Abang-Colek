"""Collection coverage manifest for ABANGCOLEK forensic backfill."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import COVERAGE_FILE

class CoverageStatus(str, Enum):
    COMPLETE_VERIFIED="COMPLETE_VERIFIED"
    COMPLETE_WITHIN_API_SCOPE="COMPLETE_WITHIN_API_SCOPE"
    PARTIAL_PLATFORM_LIMIT="PARTIAL_PLATFORM_LIMIT"
    PARTIAL_AUTH_LIMIT="PARTIAL_AUTH_LIMIT"
    PARTIAL_DELETED_CONTENT="PARTIAL_DELETED_CONTENT"
    PARTIAL_UNKNOWN="PARTIAL_UNKNOWN"
    OWNER_EXPORT_REQUIRED="OWNER_EXPORT_REQUIRED"
    BLOCKED_AUTH="BLOCKED_AUTH"
    NOT_STARTED="NOT_STARTED"
    ERROR="ERROR"

class CoverageTracker:
    DEFAULT_OUTPUT=COVERAGE_FILE
    def __init__(self,output_path:Optional[Path]=None):
        self.output_path=Path(output_path or self.DEFAULT_OUTPUT); self.output_path.parent.mkdir(parents=True,exist_ok=True); self.entries=[]; self._load_existing()
    def _load_existing(self):
        if self.output_path.exists():
            try: self.entries=json.loads(self.output_path.read_text(encoding="utf-8")).get("sources",[])
            except Exception: self.entries=[]
    def register_source(self,platform:str,source_name:str,status:CoverageStatus,record_count:int=0,notes:str="",data_origin:str="UNKNOWN",**extra)->Dict[str,Any]:
        entry={"platform":platform,"account":source_name,"source_name":source_name,"status":status.value,"record_count":record_count,"data_origin":data_origin,"posts_recovered":int(extra.pop("posts_recovered",0)),"comments_recovered":int(extra.pop("comments_recovered",0)),"replies_recovered":int(extra.pop("replies_recovered",0)),"media_recovered":int(extra.pop("media_recovered",0)),"oldest_recovered_at":extra.pop("oldest_recovered_at",None),"newest_recovered_at":extra.pop("newest_recovered_at",None),"pagination_exhausted":bool(extra.pop("pagination_exhausted",False)),"owner_export_imported":bool(extra.pop("owner_export_imported",False)),"known_gaps":extra.pop("known_gaps",[]),"notes":notes,"last_updated":datetime.now(timezone.utc).isoformat(),**extra}
        for i,x in enumerate(self.entries):
            if x.get("platform")==platform and (x.get("account") or x.get("source_name"))==source_name:
                self.entries[i]=entry; self._save(); return entry
        self.entries.append(entry); self._save(); return entry
    def _save(self):
        data={"schema_version":"3.0.0","generated_at":datetime.now(timezone.utc).isoformat(),"total_sources":len(self.entries),"sources":self.entries}
        tmp=self.output_path.with_suffix(".tmp"); tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8"); tmp.replace(self.output_path)
    def get_summary(self):
        by={}
        for e in self.entries: by[e["status"]]=by.get(e["status"],0)+1
        return {"total_sources":len(self.entries),"by_status":by,"sources":self.entries}