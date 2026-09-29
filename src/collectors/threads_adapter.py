"""Meta Threads official API collector with full cursor backfill and reply provenance."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.http_utils import load_env_file, request_json

class ThreadsOfficialApiAdapter:
    COLLECTOR_NAME='threads_official_api_v3'; API_HOST='https://graph.threads.net'
    POST_FIELDS='id,media_product_type,media_type,permalink,username,text,timestamp,shortcode,is_quote_post,has_replies,alt_text,link_attachment_url'
    REPLY_FIELDS='id,text,timestamp,media_product_type,media_type,permalink,shortcode,username,is_quote_post,has_replies,is_reply,is_reply_owned_by_me,root_post,replied_to'
    def __init__(self,access_token:Optional[str]=None,storage_dir:Optional[Path]=None,coverage:Optional[CoverageTracker]=None):
        load_env_file(); self.access_token=access_token or os.getenv('THREADS_ACCESS_TOKEN') or os.getenv('META_THREADS_ACCESS_TOKEN')
        self.collector=BaseCollector(storage_dir=storage_dir or Path('D:/ABANGCOLEK/data/raw'),collector_name=self.COLLECTOR_NAME); self.coverage=coverage or CoverageTracker(); self.checkpoint_dir=Path('D:/ABANGCOLEK/data/coverage/checkpoints'); self.checkpoint_dir.mkdir(parents=True,exist_ok=True)
    def _ingest(self,item:Dict[str,Any],receipt:Dict[str,Any],source_type:str)->Dict[str,Any]:
        payload={**item,'data_origin':'OWNER_AUTHORIZED_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True,'provenance_verified':True}
        return self.collector.ingest(raw_data=payload,platform='threads',source_id=str(item['id']),source_native_id=str(item['id']),source_type=source_type,source_url=item.get('permalink'),published_at=item.get('timestamp'),access_method='OWNER_AUTHORIZED_API',capture_receipt=receipt,provenance_verified=True)
    def _save_checkpoint(self,name:str,data:Dict[str,Any])->None:
        p=self.checkpoint_dir/f'threads_{name}.json'; p.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    def _collect_replies(self,thread_id:str)->List[Dict[str,Any]]:
        results=[]; after=None; page=0
        while True:
            params={'fields':self.REPLY_FIELDS,'limit':50,'reverse':'false','after':after}
            data,receipt=request_json('GET',f'{self.API_HOST}/{thread_id}/replies',token=self.access_token,params=params); page+=1
            rows=data.get('data',[]) or []
            for item in rows: results.append(self._ingest(item,receipt,'reply'))
            after=(data.get('paging') or {}).get('cursors',{}).get('after')
            self._save_checkpoint(f'replies_{thread_id}',{'page':page,'after':after,'items':len(results),'updated_at':datetime.now(timezone.utc).isoformat()})
            if not after or not rows: break
        return results
    def collect_user_posts(self,user_id:str='me',limit:int=50,collect_replies:bool=True,max_pages:Optional[int]=None)->List[Dict[str,Any]]:
        account='@airpoolstylo' if user_id=='me' else str(user_id)
        if not self.access_token:
            self.coverage.register_source('threads',account,CoverageStatus.BLOCKED_AUTH,notes='THREADS_ACCESS_TOKEN/META_THREADS_ACCESS_TOKEN missing',known_gaps=['All owner-authorized Threads history','Replies and insights'],data_origin='OWNER_AUTHORIZED_API'); return []
        results=[]; reply_count=0; after=None; page=0; timestamps=[]
        try:
            while True:
                data,receipt=request_json('GET',f'{self.API_HOST}/{user_id}/threads',token=self.access_token,params={'fields':self.POST_FIELDS,'limit':min(max(limit,1),100),'after':after}); page+=1
                rows=data.get('data',[]) or []
                for item in rows:
                    results.append(self._ingest(item,receipt,'post'))
                    if item.get('timestamp'): timestamps.append(item['timestamp'])
                    if collect_replies and item.get('has_replies'):
                        reply_count+=len(self._collect_replies(str(item['id'])))
                after=(data.get('paging') or {}).get('cursors',{}).get('after')
                self._save_checkpoint('owner_posts',{'page':page,'after':after,'posts':len(results),'replies':reply_count,'updated_at':datetime.now(timezone.utc).isoformat()})
                if not after or not rows or (max_pages and page>=max_pages): break
            exhausted=not bool(after)
            status=CoverageStatus.COMPLETE_WITHIN_API_SCOPE if exhausted else CoverageStatus.PARTIAL_PLATFORM_LIMIT
            self.coverage.register_source('threads',account,status,record_count=len(results)+reply_count,posts_recovered=len(results),replies_recovered=reply_count,oldest_recovered_at=min(timestamps) if timestamps else None,newest_recovered_at=max(timestamps) if timestamps else None,pagination_exhausted=exhausted,data_origin='OWNER_AUTHORIZED_API',known_gaps=['Deleted/private/unexposed historical content requires owner export'] if exhausted else ['Pagination stopped before exhaustion'])
            return results
        except Exception as exc:
            self.coverage.register_source('threads',account,CoverageStatus.ERROR,record_count=len(results)+reply_count,posts_recovered=len(results),replies_recovered=reply_count,notes=str(exc)[:500],data_origin='OWNER_AUTHORIZED_API',known_gaps=['Collection interrupted']); raise
    def keyword_search(self,query:str,search_type:str='RECENT',since:Optional[str]=None,until:Optional[str]=None,max_pages:Optional[int]=None)->List[Dict[str,Any]]:
        if not self.access_token: return []
        results=[]; after=None; page=0
        while True:
            data,receipt=request_json('GET',f'{self.API_HOST}/keyword_search',token=self.access_token,params={'q':query,'search_type':search_type,'fields':self.POST_FIELDS,'limit':50,'since':since,'until':until,'after':after}); page+=1
            rows=data.get('data',[]) or []
            for item in rows: results.append(self._ingest(item,receipt,'public_search_post'))
            after=(data.get('paging') or {}).get('cursors',{}).get('after')
            if not after or not rows or (max_pages and page>=max_pages): break
        return results

ThreadsPublicSearchAdapter=ThreadsOfficialApiAdapter