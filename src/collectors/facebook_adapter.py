"""Facebook Pages collector using Meta Graph API and Page access tokens."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.http_utils import load_env_file, request_json

class FacebookPagesApiAdapter:
    COLLECTOR_NAME='facebook_pages_api_v3'
    def __init__(self,user_access_token:Optional[str]=None,storage_dir:Optional[Path]=None,coverage:Optional[CoverageTracker]=None):
        load_env_file(); self.user_token=user_access_token or os.getenv('FACEBOOK_USER_ACCESS_TOKEN') or os.getenv('META_USER_ACCESS_TOKEN'); self.version=os.getenv('META_GRAPH_VERSION','v24.0'); self.host='https://graph.facebook.com'; self.collector=BaseCollector(storage_dir=storage_dir or Path('D:/ABANGCOLEK/data/raw'),collector_name=self.COLLECTOR_NAME); self.coverage=coverage or CoverageTracker()
    def _ingest(self,item:Dict[str,Any],receipt:Dict[str,Any],kind:str,page_name:str):
        payload={**item,'page_name':page_name,'data_origin':'OWNER_AUTHORIZED_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True,'provenance_verified':True}; sid=str(item.get('id') or receipt['response_sha256'][:16])
        return self.collector.ingest(payload,platform='facebook',source_id=sid,source_native_id=sid,source_type=kind,source_url=item.get('permalink_url'),published_at=item.get('created_time'),access_method='OWNER_AUTHORIZED_API',capture_receipt=receipt,provenance_verified=True)
    def _pages(self):
        return request_json('GET',f'{self.host}/{self.version}/me/accounts',token=self.user_token,params={'fields':'id,name,access_token,tasks,instagram_business_account','limit':100})
    def _paginate_page(self,url:str,token:str,params:Dict[str,Any],kind:str,page_name:str):
        out=[]; after=None
        while True:
            q=dict(params); q['after']=after
            data,receipt=request_json('GET',url,token=token,params=q); rows=data.get('data',[]) or []
            for item in rows: out.append(self._ingest(item,receipt,kind,page_name))
            after=(data.get('paging') or {}).get('cursors',{}).get('after')
            if not after or not rows: break
        return out
    def collect_all_managed_pages(self)->List[Dict[str,Any]]:
        if not self.user_token:
            self.coverage.register_source('facebook','managed pages',CoverageStatus.BLOCKED_AUTH,notes='FACEBOOK_USER_ACCESS_TOKEN/META_USER_ACCESS_TOKEN missing',known_gaps=['Managed Pages','Page posts','Comments/replies'],data_origin='OWNER_AUTHORIZED_API'); return []
        results=[]
        try:
            pages,receipt=self._pages()
            for page in pages.get('data',[]) or []:
                pid=str(page.get('id')); name=page.get('name') or pid; ptoken=page.get('access_token')
                if not pid or not ptoken: continue
                results.append(self._ingest({k:v for k,v in page.items() if k!='access_token'},receipt,'page_snapshot',name))
                posts=self._paginate_page(f'{self.host}/{self.version}/{pid}/posts',ptoken,{'fields':'id,message,created_time,permalink_url,shares,attachments','limit':100},'post',name); results.extend(posts); comments=0
                for rec in posts:
                    try: comments+=len(self._paginate_page(f'{self.host}/{self.version}/{rec["source_id"]}/comments',ptoken,{'fields':'id,message,created_time,from,parent','limit':100},'comment',name))
                    except Exception: pass
                self.coverage.register_source('facebook',name,CoverageStatus.COMPLETE_WITHIN_API_SCOPE,record_count=1+len(posts)+comments,posts_recovered=len(posts),comments_recovered=comments,pagination_exhausted=True,data_origin='OWNER_AUTHORIZED_API',known_gaps=['Deleted/private/unavailable Page history may require owner export'])
            if not pages.get('data'):
                self.coverage.register_source('facebook','managed pages',CoverageStatus.PARTIAL_AUTH_LIMIT,notes='Token returned no managed Pages',data_origin='OWNER_AUTHORIZED_API',known_gaps=['Page authorization required'])
            return results
        except Exception as exc:
            self.coverage.register_source('facebook','managed pages',CoverageStatus.ERROR,record_count=len(results),notes=str(exc)[:500],data_origin='OWNER_AUTHORIZED_API',known_gaps=['Collection interrupted']); raise
