"""TikTok Display API collector with cursor backfill and owner-export fallback."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.collectors.http_utils import load_env_file, request_json
from src.collectors.owner_export_importer import OwnerExportImporter

class TikTokOfficialApiAdapter:
    COLLECTOR_NAME='tiktok_display_api_v3'; HOST='https://open.tiktokapis.com'
    VIDEO_FIELDS='id,create_time,cover_image_url,share_url,video_description,duration,height,width,title,embed_html,embed_link,like_count,comment_count,share_count,view_count,is_aigc'
    PROFILE_FIELDS='open_id,union_id,avatar_url,avatar_url_100,avatar_large_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count'
    def __init__(self,access_token:Optional[str]=None,storage_dir:Optional[Path]=None,coverage:Optional[CoverageTracker]=None):
        load_env_file(); self.access_token=access_token or os.getenv('TIKTOK_ACCESS_TOKEN') or os.getenv('TIKTOK_DISPLAY_ACCESS_TOKEN')
        self.collector=BaseCollector(storage_dir=storage_dir or Path('D:/ABANGCOLEK/data/raw'),collector_name=self.COLLECTOR_NAME); self.coverage=coverage or CoverageTracker(); self.checkpoint_dir=Path('D:/ABANGCOLEK/data/coverage/checkpoints'); self.checkpoint_dir.mkdir(parents=True,exist_ok=True)
    def _ingest(self,item:Dict[str,Any],receipt:Dict[str,Any],source_type:str)->Dict[str,Any]:
        payload={**item,'data_origin':'OWNER_AUTHORIZED_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True,'provenance_verified':True}
        sid=str(item.get('id') or item.get('open_id') or receipt['response_sha256'][:16])
        return self.collector.ingest(raw_data=payload,platform='tiktok',source_id=sid,source_native_id=sid,source_type=source_type,source_url=item.get('share_url') or item.get('profile_deep_link'),published_at=str(item.get('create_time') or ''),access_method='OWNER_AUTHORIZED_API',capture_receipt=receipt,provenance_verified=True)
    def collect_profile(self)->Optional[Dict[str,Any]]:
        if not self.access_token: return None
        data,receipt=request_json('GET',f'{self.HOST}/v2/user/info/',token=self.access_token,params={'fields':self.PROFILE_FIELDS}); user=(data.get('data') or {}).get('user') or {}
        return self._ingest(user,receipt,'profile_snapshot') if user else None
    def collect_user_videos(self,username:str='styloairpool',limit:int=20,max_pages:Optional[int]=None)->List[Dict[str,Any]]:
        account='@'+username.lstrip('@')
        if not self.access_token:
            self.coverage.register_source('tiktok',account,CoverageStatus.BLOCKED_AUTH,notes='TIKTOK_ACCESS_TOKEN/TIKTOK_DISPLAY_ACCESS_TOKEN missing',known_gaps=['Authorized video history','Profile metadata','Comments are not exposed by Display API','Owner export required for lifetime/deleted data'],data_origin='OWNER_AUTHORIZED_API'); return []
        results=[]; cursor=None; page=0; timestamps=[]; exhausted=False
        try:
            self.collect_profile()
            while True:
                body={'max_count':min(max(limit,1),20)}
                if cursor is not None: body['cursor']=cursor
                data,receipt=request_json('POST',f'{self.HOST}/v2/video/list/',token=self.access_token,params={'fields':self.VIDEO_FIELDS},payload=body); page+=1
                block=data.get('data') or {}; rows=block.get('videos',[]) or []
                for item in rows:
                    results.append(self._ingest(item,receipt,'video'))
                    if item.get('create_time') is not None: timestamps.append(str(item['create_time']))
                has_more=bool(block.get('has_more')); cursor=block.get('cursor')
                cp={'page':page,'cursor':cursor,'has_more':has_more,'videos':len(results),'updated_at':datetime.now(timezone.utc).isoformat()}; (self.checkpoint_dir/'tiktok_owner_videos.json').write_text(json.dumps(cp,indent=2),encoding='utf-8')
                if not has_more or not rows: exhausted=True; break
                if max_pages and page>=max_pages: break
            status=CoverageStatus.COMPLETE_WITHIN_API_SCOPE if exhausted else CoverageStatus.PARTIAL_PLATFORM_LIMIT
            gaps=['TikTok Display API does not provide comments; import owner export where available','Deleted/private/lifetime history may not be exposed by Display API; owner export required for maximum recoverable history']
            self.coverage.register_source('tiktok',account,status,record_count=len(results),posts_recovered=len(results),oldest_recovered_at=min(timestamps) if timestamps else None,newest_recovered_at=max(timestamps) if timestamps else None,pagination_exhausted=exhausted,data_origin='OWNER_AUTHORIZED_API',known_gaps=gaps)
            return results
        except Exception as exc:
            self.coverage.register_source('tiktok',account,CoverageStatus.ERROR,record_count=len(results),posts_recovered=len(results),notes=str(exc)[:500],data_origin='OWNER_AUTHORIZED_API',known_gaps=['Collection interrupted','Owner export may close historical gaps']); raise
    def query_videos(self,video_ids:List[str])->List[Dict[str,Any]]:
        if not self.access_token: return []
        out=[]
        for i in range(0,len(video_ids),20):
            ids=video_ids[i:i+20]; data,receipt=request_json('POST',f'{self.HOST}/v2/video/query/',token=self.access_token,params={'fields':self.VIDEO_FIELDS},payload={'filters':{'video_ids':ids}})
            for item in (data.get('data') or {}).get('videos',[]) or []: out.append(self._ingest(item,receipt,'video_snapshot'))
        return out

class TikTokOwnerExportAdapter:
    def __init__(self,storage_dir:Optional[Path]=None): self.importer=OwnerExportImporter(storage_dir=storage_dir)
    def import_export_archive(self,archive_path:Path)->List[Dict[str,Any]]:
        return self.importer.import_zip(archive_path,'tiktok') if archive_path.suffix.lower()=='.zip' else self.importer.import_json(archive_path,'tiktok')

class TikTokPublicEvidenceAdapter:
    def ingest_verified_record(self,*args,**kwargs):
        raise RuntimeError('Manual self-asserted public evidence ingestion is disabled. Capture source content through a real collector or owner export.')