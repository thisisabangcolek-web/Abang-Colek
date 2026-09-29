"""Facebook Pages collector with explicit per-scope coverage semantics."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from src.config import DATA_DIR, RAW_DIR
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.http_utils import load_env_file, request_json

class FacebookPagesApiAdapter:
    COLLECTOR_NAME="facebook_pages_api_v4"
    def __init__(self,user_access_token:Optional[str]=None,storage_dir:Optional[Path]=None,coverage:Optional[CoverageTracker]=None):
        load_env_file(); self.user_token=user_access_token or os.getenv("FACEBOOK_USER_ACCESS_TOKEN") or os.getenv("META_USER_ACCESS_TOKEN")
        self.version=os.getenv("META_GRAPH_VERSION","v24.0"); self.host="https://graph.facebook.com"
        self.collector=BaseCollector(storage_dir=storage_dir or RAW_DIR,collector_name=self.COLLECTOR_NAME); self.coverage=coverage or CoverageTracker()
    @staticmethod
    def _validate(data:Any)->Dict[str,Any]:
        if not isinstance(data,dict): raise RuntimeError("Meta Graph response is not an object")
        if data.get("error"): raise RuntimeError(f"Meta Graph error envelope: {data['error']}")
        return data
    def _ingest(self,item:Dict[str,Any],receipt:Dict[str,Any],kind:str,page_name:str):
        payload={**item,"page_name":page_name,"data_origin":"OWNER_AUTHORIZED_API","evidence_class":"RAW_EVIDENCE","synthetic":False,"authoritative":True,"provenance_verified":True}
        sid=str(item.get("id") or receipt["response_sha256"][:16])
        return self.collector.ingest(payload,platform="facebook",source_id=sid,source_native_id=sid,source_type=kind,source_url=item.get("permalink_url"),published_at=item.get("created_time"),access_method="OWNER_AUTHORIZED_API",capture_receipt=receipt,provenance_verified=True)
    def _paginate(self,url:str,token:str,params:Dict[str,Any],kind:str,page_name:str)->Tuple[List[Dict[str,Any]],bool]:
        out=[]; after=None; seen=set(); exhausted=False
        while True:
            q=dict(params)
            if after: q["after"]=after
            data,receipt=request_json("GET",url,token=token,params=q); data=self._validate(data); rows=data.get("data") or []
            if not isinstance(rows,list): raise RuntimeError("Meta paging data is not a list")
            for item in rows:
                if isinstance(item,dict): out.append(self._ingest(item,receipt,kind,page_name))
            next_after=((data.get("paging") or {}).get("cursors") or {}).get("after")
            next_url=(data.get("paging") or {}).get("next")
            if not rows or not next_url or not next_after:
                exhausted=True; break
            if next_after in seen: raise RuntimeError("Meta pagination cursor repeated")
            seen.add(next_after); after=next_after
        return out,exhausted
    def _managed_pages(self)->Tuple[List[Dict[str,Any]],bool]:
        pages=[]; after=None; seen=set(); exhausted=False
        while True:
            params={"fields":"id,name,access_token,tasks,instagram_business_account","limit":100}
            if after: params["after"]=after
            data,receipt=request_json("GET",f"{self.host}/{self.version}/me/accounts",token=self.user_token,params=params); data=self._validate(data)
            rows=data.get("data") or []
            if not isinstance(rows,list): raise RuntimeError("Managed Pages response data is not a list")
            for page in rows:
                if isinstance(page,dict): pages.append({"page":page,"receipt":receipt})
            next_after=((data.get("paging") or {}).get("cursors") or {}).get("after"); next_url=(data.get("paging") or {}).get("next")
            if not rows or not next_url or not next_after:
                exhausted=True; break
            if next_after in seen: raise RuntimeError("Managed Pages cursor repeated")
            seen.add(next_after); after=next_after
        return pages,exhausted
    def collect_all_managed_pages(self)->List[Dict[str,Any]]:
        if not self.user_token:
            self.coverage.register_source("facebook","managed pages",CoverageStatus.BLOCKED_AUTH,notes="FACEBOOK_USER_ACCESS_TOKEN/META_USER_ACCESS_TOKEN missing",known_gaps=["Managed Pages","Page posts","Comments/replies"],data_origin="OWNER_AUTHORIZED_API"); return []
        results=[]
        try:
            pages,pages_exhausted=self._managed_pages()
            if not pages:
                self.coverage.register_source("facebook","managed pages",CoverageStatus.PARTIAL_AUTH_LIMIT,notes="Token returned no managed Pages",data_origin="OWNER_AUTHORIZED_API",known_gaps=["Page authorization required"],pagination_exhausted=pages_exhausted); return []
            for wrapped in pages:
                page=wrapped["page"]; receipt=wrapped["receipt"]; pid=str(page.get("id") or ""); name=page.get("name") or pid; ptoken=page.get("access_token")
                if not pid or not ptoken: continue
                results.append(self._ingest({k:v for k,v in page.items() if k!="access_token"},receipt,"page_snapshot",name))
                posts,posts_exhausted=self._paginate(f"{self.host}/{self.version}/{pid}/posts",ptoken,{"fields":"id,message,created_time,permalink_url,shares,attachments","limit":100},"post",name)
                results.extend(posts); comments=0; comment_errors=0; comments_exhausted=True
                for rec in posts:
                    try:
                        rows,ok=self._paginate(f"{self.host}/{self.version}/{rec['source_id']}/comments",ptoken,{"fields":"id,message,created_time,from,parent","limit":100},"comment",name)
                        comments+=len(rows); comments_exhausted=comments_exhausted and ok
                    except Exception:
                        comment_errors+=1; comments_exhausted=False
                complete=pages_exhausted and posts_exhausted and comments_exhausted and comment_errors==0
                status=CoverageStatus.COMPLETE_WITHIN_API_SCOPE if complete else CoverageStatus.PARTIAL_PLATFORM_LIMIT
                gaps=["Deleted/private/unavailable Page history may require owner export"]
                if comment_errors: gaps.append(f"Comment collection failed for {comment_errors} posts")
                self.coverage.register_source("facebook",name,status,record_count=1+len(posts)+comments,posts_recovered=len(posts),comments_recovered=comments,pagination_exhausted=complete,data_origin="OWNER_AUTHORIZED_API",known_gaps=gaps,comment_errors=comment_errors)
            return results
        except Exception as exc:
            self.coverage.register_source("facebook","managed pages",CoverageStatus.ERROR,record_count=len(results),notes=str(exc)[:500],data_origin="OWNER_AUTHORIZED_API",known_gaps=["Collection interrupted"]); raise
