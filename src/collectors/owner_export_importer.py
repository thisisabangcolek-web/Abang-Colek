"""Owner export importer that emits canonical evidence units, not opaque containers."""
from __future__ import annotations

import hashlib, json, zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker
from src.config import OWNER_EXPORT_INBOX, RAW_DIR


class OwnerExportImporter:
    STORAGE_DIR=RAW_DIR
    def __init__(self,storage_dir:Optional[Path]=None,coverage:Optional[CoverageTracker]=None):
        self.storage_dir=Path(storage_dir or self.STORAGE_DIR); self.storage_dir.mkdir(parents=True,exist_ok=True)
        self.collector=BaseCollector(storage_dir=self.storage_dir,collector_name="owner_export_importer_v4"); self.coverage=coverage or CoverageTracker()
    @staticmethod
    def _sha(path:Path)->str:
        h=hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
        return h.hexdigest()
    @staticmethod
    def _walk(value:Any,path:str="root")->Iterable[Tuple[str,Dict[str,Any]]]:
        if isinstance(value,dict):
            keys={str(k).lower() for k in value}
            content_keys={"id","post_id","video_id","comment_id","text","message","caption","description","timestamp","created_time","date"}
            if keys & content_keys: yield path,value
            for key,child in value.items(): yield from OwnerExportImporter._walk(child,f"{path}.{key}")
        elif isinstance(value,list):
            for i,child in enumerate(value): yield from OwnerExportImporter._walk(child,f"{path}[{i}]")
    @staticmethod
    def _kind(path:str,item:Dict[str,Any])->str:
        low=path.lower(); keys={str(k).lower() for k in item}
        if "comment" in low or "comment_id" in keys: return "owner_export_reply" if "reply" in low else "owner_export_comment"
        if "reply" in low: return "owner_export_reply"
        if any(x in low for x in ("post","video","media","content")) or keys & {"post_id","video_id","caption","description"}: return "owner_export_post"
        return "owner_export_container"
    @staticmethod
    def _sid(item:Dict[str,Any],path:str)->str:
        value=item.get("id") or item.get("post_id") or item.get("video_id") or item.get("comment_id")
        return str(value) if value is not None else hashlib.sha256(f"{path}:{json.dumps(item,sort_keys=True,default=str)}".encode()).hexdigest()[:24]
    def _ingest_item(self,item:Dict[str,Any],platform:str,path:str,export_file:Path,receipt:Dict[str,Any]):
        kind=self._kind(path,item); sid=self._sid(item,path); text=next((str(item[k]) for k in ("text","message","caption","description","title") if item.get(k)),"")
        payload={"text":text,"export_payload":item,"export_path":path,"data_origin":"OWNER_EXPORT","evidence_class":"RAW_EVIDENCE","synthetic":False,"authoritative":True,"provenance_verified":True}
        published=str(item.get("timestamp") or item.get("created_time") or item.get("date") or "")
        return self.collector.ingest(payload,platform=platform,source_id=sid,source_native_id=sid,source_type=kind,published_at=published,access_method="OWNER_EXPORT",capture_receipt=receipt,provenance_verified=True,owner_export_file=str(export_file.resolve()))

    def _import_data(self,data:Any,platform:str,export_file:Path,receipt:Dict[str,Any],root_path:str)->List[Dict[str,Any]]:
        results=[]; seen=set()
        for path,item in self._walk(data,root_path):
            key=(path,self._sid(item,path))
            if key in seen: continue
            seen.add(key); results.append(self._ingest_item(item,platform,path,export_file,receipt))
        return results
    def _register(self,platform:str,name:str,count:int,recognized:bool):
        status=CoverageStatus.PARTIAL_UNKNOWN if recognized else CoverageStatus.ERROR
        gaps=["Import parsing completed, but platform export scope/completeness is not independently verified"] if recognized else ["No recognizable post/comment/media records found in export"]
        self.coverage.register_source(platform,f"owner_export:{name}",status,record_count=count,owner_export_imported=recognized,pagination_exhausted=False,data_origin="OWNER_EXPORT",known_gaps=gaps,
                                      notes="Parsed owner export; parsing success is not equivalent to complete account coverage.")
    def import_json(self,json_path:Path,platform:str="unknown")->List[Dict[str,Any]]:
        path=Path(json_path)
        if not path.exists(): return []
        raw=path.read_bytes(); data=json.loads(raw.decode("utf-8-sig")); sha=hashlib.sha256(raw).hexdigest()
        receipt={"owner_export_sha256":sha,"member_path":path.name,"member_sha256":sha}
        results=self._import_data(data,platform,path,receipt,path.name); self._register(platform,path.name,len(results),bool(results)); return results
    def import_zip(self,zip_path:Path,platform:str="unknown")->List[Dict[str,Any]]:
        path=Path(zip_path)
        if not path.exists(): return []
        export_sha=self._sha(path); results=[]
        with zipfile.ZipFile(path,"r") as zf:
            for info in zf.infolist():
                name=info.filename.replace("\\","/")
                if info.is_dir() or not name.lower().endswith(".json") or name.startswith("/") or ".." in Path(name).parts: continue
                raw=zf.read(info); member_sha=hashlib.sha256(raw).hexdigest()
                try: data=json.loads(raw.decode("utf-8-sig"))
                except Exception: continue
                receipt={"owner_export_sha256":export_sha,"member_path":name,"member_sha256":member_sha}
                results.extend(self._import_data(data,platform,path,receipt,name))
        self._register(platform,path.name,len(results),bool(results)); return results
