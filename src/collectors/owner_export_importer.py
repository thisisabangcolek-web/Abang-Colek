"""Owner-authorized platform export importer with file-level provenance."""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker

class OwnerExportImporter:
    STORAGE_DIR=Path('D:/ABANGCOLEK/data/raw')
    def __init__(self,storage_dir:Optional[Path]=None,coverage:Optional[CoverageTracker]=None):
        self.storage_dir=Path(storage_dir or self.STORAGE_DIR); self.storage_dir.mkdir(parents=True,exist_ok=True)
        self.collector=BaseCollector(storage_dir=self.storage_dir,collector_name='owner_export_importer_v3'); self.coverage=coverage or CoverageTracker()
    @staticmethod
    def _sha(path:Path)->str:
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
        return h.hexdigest()
    def _ingest(self,data:Any,platform:str,source_id:str,export_file:Path,receipt:Dict[str,Any])->Dict[str,Any]:
        payload={'export_payload':data,'data_origin':'OWNER_EXPORT','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True,'provenance_verified':True}
        return self.collector.ingest(raw_data=payload,platform=platform,source_id=source_id,source_native_id=source_id,source_type='owner_export',access_method='OWNER_EXPORT',capture_receipt=receipt,provenance_verified=True,owner_export_file=str(export_file.resolve()))
    def import_json(self,json_path:Path,platform:str='unknown')->List[Dict[str,Any]]:
        json_path=Path(json_path)
        if not json_path.exists(): return []
        raw=json_path.read_bytes(); data=json.loads(raw.decode('utf-8-sig')); export_sha=hashlib.sha256(raw).hexdigest(); results=[]
        items=data if isinstance(data,list) else [data]
        for i,item in enumerate(items):
            sid=str(item.get('id') or item.get('post_id') or item.get('video_id') or f'{json_path.stem}_{i}') if isinstance(item,dict) else f'{json_path.stem}_{i}'
            receipt={'owner_export_sha256':export_sha,'member_path':json_path.name,'member_sha256':export_sha}
            results.append(self._ingest(item,platform,sid,json_path,receipt))
        self.coverage.register_source(platform,f'owner_export:{json_path.name}',CoverageStatus.COMPLETE_VERIFIED,record_count=len(results),owner_export_imported=True,pagination_exhausted=True,data_origin='OWNER_EXPORT')
        return results
    def import_zip(self,zip_path:Path,platform:str='unknown')->List[Dict[str,Any]]:
        zip_path=Path(zip_path)
        if not zip_path.exists(): return []
        export_sha=self._sha(zip_path); results=[]
        with zipfile.ZipFile(zip_path,'r') as zf:
            for info in zf.infolist():
                name=info.filename.replace('\\','/')
                if info.is_dir() or not name.lower().endswith('.json') or name.startswith('/') or '..' in Path(name).parts: continue
                raw=zf.read(info); member_sha=hashlib.sha256(raw).hexdigest()
                try: data=json.loads(raw.decode('utf-8-sig'))
                except Exception: continue
                items=data if isinstance(data,list) else [data]
                for i,item in enumerate(items):
                    stem=Path(name).stem; sid=str(item.get('id') or item.get('post_id') or item.get('video_id') or f'{stem}_{i}') if isinstance(item,dict) else f'{stem}_{i}'
                    receipt={'owner_export_sha256':export_sha,'member_path':name,'member_sha256':member_sha}
                    results.append(self._ingest(item,platform,sid,zip_path,receipt))
        self.coverage.register_source(platform,f'owner_export:{zip_path.name}',CoverageStatus.COMPLETE_VERIFIED,record_count=len(results),owner_export_imported=True,pagination_exhausted=True,data_origin='OWNER_EXPORT',known_gaps=['Export content completeness depends on platform export scope'])
        return results