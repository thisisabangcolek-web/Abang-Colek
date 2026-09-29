"""No-key TikTok photo-post fallback using gallery-dl for browser-discovered URLs."""
from __future__ import annotations
import asyncio, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from src.config import DATA_DIR, RAW_DIR
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker

class TikTokGalleryPhotoAdapter:
    COLLECTOR_NAME="tiktok_gallery_dl_photo_v1"
    def __init__(self, discovery_file:Optional[Path]=None, storage_dir:Optional[Path]=None, coverage:Optional[CoverageTracker]=None):
        self.discovery_file=Path(discovery_file or DATA_DIR/"coverage"/"discovery"/"tiktok_styloairpool_public_urls.json")
        self.raw_dir=DATA_DIR/"extractor_raw"/"tiktok_gallery"; self.raw_dir.mkdir(parents=True,exist_ok=True)
        self.checkpoint=DATA_DIR/"coverage"/"checkpoints"/"tiktok_gallery_photo.json"; self.checkpoint.parent.mkdir(parents=True,exist_ok=True)
        self.collector=BaseCollector(storage_dir=storage_dir or RAW_DIR,collector_name=self.COLLECTOR_NAME)
        self.coverage=coverage or CoverageTracker(); self.bin=shutil.which("gallery-dl") or shutil.which("gallery-dl.exe")
    def _urls(self)->List[str]:
        if not self.discovery_file.exists(): return []
        d=json.loads(self.discovery_file.read_text(encoding="utf-8")); return [u for u in d.get("urls",[]) if "/photo/" in u]
    async def _one(self,url:str)->Tuple[str,Optional[Dict[str,Any]],Optional[bytes],Optional[str]]:
        if not self.bin: return url,None,None,"gallery-dl not installed"
        for attempt in range(3):
            p=await asyncio.create_subprocess_exec(self.bin,"-j",url,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            try: out,err=await asyncio.wait_for(p.communicate(),timeout=40)
            except asyncio.TimeoutError:
                p.kill(); await p.communicate(); out=b""; err=b"timeout"
            if p.returncode==0 and out:
                try:
                    messages=json.loads(out.decode("utf-8",errors="replace")); meta=next((x[1] for x in messages if isinstance(x,list) and len(x)>1 and x[0]==2 and isinstance(x[1],dict)),None)
                    if meta: return url,meta,out,None
                except Exception as exc: err=str(exc).encode()
            if attempt<2: await asyncio.sleep(1.5*(attempt+1))
        return url,None,None,err.decode("utf-8",errors="replace")[-700:]
    @staticmethod
    def _payload(meta:Dict[str,Any],url:str)->Dict[str,Any]:
        author=meta.get("author") or {}; stats=meta.get("stats") or {}; author_stats=meta.get("authorStats") or {}
        desc=meta.get("desc") or ""; ts=meta.get("createTime")
        return {
            "id":str(meta.get("id") or url.rstrip('/').split('/')[-1]),"title":desc,"description":desc,"timestamp":int(ts) if str(ts).isdigit() else ts,
            "uploader":author.get("uniqueId"),"uploader_id":author.get("id"),"channel":author.get("nickname"),"channel_id":author.get("secUid"),
            "view_count":stats.get("playCount"),"like_count":stats.get("diggCount"),"comment_count":stats.get("commentCount"),"share_count":stats.get("shareCount"),"save_count":stats.get("collectCount"),
            "author_stats":{"follower_count":author_stats.get("followerCount"),"following_count":author_stats.get("followingCount"),"heart_count":author_stats.get("heartCount"),"video_count":author_stats.get("videoCount")},
            "hashtags":[x.get("title") for x in (meta.get("challenges") or []) if isinstance(x,dict) and x.get("title")],"webpage_url":url,
            "data_origin":"PUBLIC_PLATFORM","evidence_class":"RAW_EVIDENCE","synthetic":False,"authoritative":True,"provenance_verified":True,"metadata_extractor":"gallery-dl"
        }
    async def collect_all(self)->Dict[str,int]:
        urls=self._urls(); processed=0; failed=0
        for url in urls:
            u,meta,raw,error=await self._one(url)
            if not meta or raw is None: failed+=1; continue
            raw_hash=hashlib.sha256(raw).hexdigest(); vid=str(meta.get("id") or url.rstrip('/').split('/')[-1]); raw_path=self.raw_dir/f"{vid}_{raw_hash}.json"
            if not raw_path.exists(): raw_path.write_bytes(raw)
            payload=self._payload(meta,url); ts=payload.get("timestamp"); published=""
            if ts:
                try: published=datetime.fromtimestamp(float(ts),tz=timezone.utc).isoformat()
                except Exception: pass
            self.collector.ingest(raw_data=payload,platform="tiktok",source_id=vid,source_native_id=vid,source_type="public_photo_metadata",source_url=url,published_at=published,access_method="GALLERY_DL_PUBLIC",capture_receipt={"capture_method":"GALLERY_DL_PUBLIC_METADATA","captured_at":datetime.now(timezone.utc).isoformat(),"source_url":url,"stdout_sha256":raw_hash,"raw_output_file":str(raw_path),"api_key_used":False,"credentials_exported":False},provenance_verified=True); processed+=1
        status=CoverageStatus.PARTIAL_UNKNOWN if failed else CoverageStatus.PARTIAL_PLATFORM_LIMIT
        self.coverage.register_source("tiktok","@styloairpool:gallery-dl-photo",status,record_count=processed,posts_recovered=processed,data_origin="PUBLIC_PLATFORM",known_gaps=["Only browser-discovered public photo posts are covered"],notes=f"gallery-dl photo fallback: processed={processed}, failed={failed}",api_key_used=False)
        self.checkpoint.write_text(json.dumps({"processed":processed,"failed":failed,"updated_at":datetime.now(timezone.utc).isoformat()},indent=2),encoding="utf-8")
        return {"discovered":len(urls),"processed":processed,"failed":failed}

def main(): print(json.dumps(asyncio.run(TikTokGalleryPhotoAdapter().collect_all()),indent=2))
if __name__=="__main__": main()
