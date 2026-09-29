"""Meta Threads official API collector with full cursor backfill and reply provenance."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import DATA_DIR, RAW_DIR
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.http_utils import load_env_file, request_json

class ThreadsOfficialApiAdapter:
    COLLECTOR_NAME='threads_official_api_v3'; API_HOST='https://graph.threads.net'
    POST_FIELDS='id,media_product_type,media_type,permalink,username,text,timestamp,shortcode,is_quote_post,has_replies,alt_text,link_attachment_url'
    REPLY_FIELDS='id,text,timestamp,media_product_type,media_type,permalink,shortcode,username,is_quote_post,has_replies,is_reply,is_reply_owned_by_me,root_post,replied_to'
    def __init__(self,access_token:Optional[str]=None,storage_dir:Optional[Path]=None,coverage:Optional[CoverageTracker]=None):
        load_env_file(); self.access_token=access_token or os.getenv('THREADS_ACCESS_TOKEN') or os.getenv('META_THREADS_ACCESS_TOKEN')
        self.collector=BaseCollector(storage_dir=storage_dir or RAW_DIR,collector_name=self.COLLECTOR_NAME); self.coverage=coverage or CoverageTracker(); self.checkpoint_dir=DATA_DIR/'coverage'/'checkpoints'; self.checkpoint_dir.mkdir(parents=True,exist_ok=True)
    @staticmethod
    def _validate(data:Any)->Dict[str,Any]:
        if not isinstance(data,dict): raise RuntimeError('Threads response is not an object')
        if data.get('error'): raise RuntimeError(f"Threads API error envelope: {data['error']}")
        return data
    def _ingest(self,item:Dict[str,Any],receipt:Dict[str,Any],source_type:str)->Dict[str,Any]:
        payload={**item,'data_origin':'OWNER_AUTHORIZED_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True,'provenance_verified':True}
        return self.collector.ingest(raw_data=payload,platform='threads',source_id=str(item['id']),source_native_id=str(item['id']),source_type=source_type,source_url=item.get('permalink'),published_at=item.get('timestamp'),access_method='OWNER_AUTHORIZED_API',capture_receipt=receipt,provenance_verified=True)
    def _save_checkpoint(self,name:str,data:Dict[str,Any])->None:
        p=self.checkpoint_dir/f'threads_{name}.json'; p.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    def _collect_replies(self,thread_id:str)->tuple[List[Dict[str,Any]],bool]:
        results=[]; after=None; page=0; seen=set(); exhausted=False
        while True:
            params={'fields':self.REPLY_FIELDS,'limit':50,'reverse':'false'}
            if after: params['after']=after
            data,receipt=request_json('GET',f'{self.API_HOST}/{thread_id}/replies',token=self.access_token,params=params); data=self._validate(data); page+=1
            rows=data.get('data') or []
            if not isinstance(rows,list): raise RuntimeError('Threads replies data is not a list')
            for item in rows:
                if isinstance(item,dict): results.append(self._ingest(item,receipt,'reply'))
            next_after=((data.get('paging') or {}).get('cursors') or {}).get('after'); next_url=(data.get('paging') or {}).get('next')
            self._save_checkpoint(f'replies_{thread_id}',{'page':page,'after':next_after,'items':len(results),'updated_at':datetime.now(timezone.utc).isoformat()})
            if not rows or not next_url or not next_after:
                exhausted=True; break
            if next_after in seen: raise RuntimeError('Threads reply cursor repeated')
            seen.add(next_after); after=next_after
        return results,exhausted
    def collect_user_posts(self,user_id:str='me',limit:int=50,collect_replies:bool=True,max_pages:Optional[int]=None)->List[Dict[str,Any]]:
        account='@airpoolstylo' if user_id=='me' else str(user_id)
        if not self.access_token:
            self.coverage.register_source('threads',account,CoverageStatus.BLOCKED_AUTH,notes='THREADS_ACCESS_TOKEN/META_THREADS_ACCESS_TOKEN missing',known_gaps=['All owner-authorized Threads history','Replies and insights'],data_origin='OWNER_AUTHORIZED_API'); return []
        results=[]; reply_count=0; reply_errors=0; replies_exhausted=True; after=None; page=0; timestamps=[]; seen=set(); posts_exhausted=False; stop_reason=None
        try:
            while True:
                params={'fields':self.POST_FIELDS,'limit':min(max(limit,1),100)}
                if after: params['after']=after
                data,receipt=request_json('GET',f'{self.API_HOST}/{user_id}/threads',token=self.access_token,params=params); data=self._validate(data); page+=1
                rows=data.get('data') or []
                if not isinstance(rows,list): raise RuntimeError('Threads posts data is not a list')
                for item in rows:
                    if not isinstance(item,dict): continue
                    results.append(self._ingest(item,receipt,'post'))
                    if item.get('timestamp'): timestamps.append(item['timestamp'])
                    if collect_replies and item.get('has_replies'):
                        try:
                            replies,ok=self._collect_replies(str(item['id'])); reply_count+=len(replies); replies_exhausted=replies_exhausted and ok
                        except Exception:
                            reply_errors+=1; replies_exhausted=False
                next_after=((data.get('paging') or {}).get('cursors') or {}).get('after'); next_url=(data.get('paging') or {}).get('next')
                self._save_checkpoint('owner_posts',{'page':page,'after':next_after,'posts':len(results),'replies':reply_count,'reply_errors':reply_errors,'updated_at':datetime.now(timezone.utc).isoformat()})
                if not rows or not next_url or not next_after:
                    posts_exhausted=True; break
                if next_after in seen:
                    stop_reason='Threads post cursor repeated'; break
                seen.add(next_after); after=next_after
                if max_pages and page>=max_pages:
                    stop_reason=f'Stopped at max_pages={max_pages}'; break
            complete=posts_exhausted and replies_exhausted and reply_errors==0
            status=CoverageStatus.COMPLETE_WITHIN_API_SCOPE if complete else CoverageStatus.PARTIAL_PLATFORM_LIMIT
            gaps=['Deleted/private/unexposed historical content requires owner export']
            if reply_errors: gaps.append(f'Reply collection failed for {reply_errors} posts')
            if stop_reason: gaps.append(stop_reason)
            self.coverage.register_source('threads',account,status,record_count=len(results)+reply_count,posts_recovered=len(results),replies_recovered=reply_count,oldest_recovered_at=min(timestamps) if timestamps else None,newest_recovered_at=max(timestamps) if timestamps else None,pagination_exhausted=complete,data_origin='OWNER_AUTHORIZED_API',known_gaps=gaps,reply_errors=reply_errors,completion_reason='CURSOR_EXHAUSTED' if complete else stop_reason)
            return results
        except Exception as exc:
            self.coverage.register_source('threads',account,CoverageStatus.ERROR,record_count=len(results)+reply_count,posts_recovered=len(results),replies_recovered=reply_count,notes=str(exc)[:500],data_origin='OWNER_AUTHORIZED_API',known_gaps=['Collection interrupted']); raise
    def keyword_search(self,query:str,search_type:str='RECENT',since:Optional[str]=None,until:Optional[str]=None,max_pages:Optional[int]=None)->List[Dict[str,Any]]:
        if not self.access_token: return []
        results=[]; after=None; page=0
        while True:
            data,receipt=request_json('GET',f'{self.API_HOST}/keyword_search',token=self.access_token,params={'q':query,'search_type':search_type,'fields':self.POST_FIELDS,'limit':50,'since':since,'until':until,'after':after}); data=self._validate(data); page+=1
            rows=data.get('data') or []
            if not isinstance(rows,list): raise RuntimeError('Threads keyword search data is not a list')
            for item in rows: results.append(self._ingest(item,receipt,'public_search_post'))
            after=(data.get('paging') or {}).get('cursors',{}).get('after')
            if not after or not rows or (max_pages and page>=max_pages): break
        return results

ThreadsPublicSearchAdapter=ThreadsOfficialApiAdapter