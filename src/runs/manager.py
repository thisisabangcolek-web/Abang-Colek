"""Transactional processing-run manager.

Derived artifacts are written under data/runs/<run_id>.  The active pointer only
changes after validation, preserving the previous valid run on failure.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from uuid import uuid4

from src.config import ACTIVE_RUN_FILE, RUNS_DIR, RUN_SCHEMA_VERSION


def active_run() -> Optional[Dict[str, Any]]:
    if not ACTIVE_RUN_FILE.exists():
        return None
    try:
        return json.loads(ACTIVE_RUN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


class ProcessingRun:
    def __init__(self, run_id: Optional[str] = None, *, runs_dir: Optional[Path] = None, active_file: Optional[Path] = None):
        self.runs_dir=Path(runs_dir or RUNS_DIR); self.active_file=Path(active_file or ACTIVE_RUN_FILE)
        self.run_id=run_id or f"run_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}_{uuid4().hex[:8]}"
        self.root=self.runs_dir/self.run_id; self.root.mkdir(parents=True,exist_ok=False)
        self.normalized_dir=self.root/"normalized"; self.normalized_dir.mkdir()
        self.decisions_file=self.root/"jev_decisions.json"; self.media_file=self.root/"media.json"
        self.bi_file=self.root/"bi.json"; self.graph_file=self.root/"knowledge.db"; self.workspace_dir=self.root/"workspace"
        self.manifest_file=self.root/"manifest.json"; self.manifest={"schema_version":RUN_SCHEMA_VERSION,"run_id":self.run_id,
            "status":"STAGING","created_at":datetime.now(timezone.utc).isoformat(),"stages":{},"artifacts":{}}
        self._save_manifest()

    @staticmethod
    def fingerprint_hashes(hashes: Iterable[str]) -> str:
        values=sorted(str(x) for x in hashes)
        return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()

    def set_input(self, *, fingerprint: str, selected_records: int, total_captures: int, raw_hashes: Optional[list[str]] = None):
        self.manifest["input_fingerprint"] = fingerprint
        self.manifest["input"] = {"selected_records": selected_records, "total_captures": total_captures}
        if raw_hashes is not None:
            self.manifest["input"]["raw_hashes_sha256"] = self.fingerprint_hashes(raw_hashes)
        self._save_manifest()

    def stage(self,name:str,status:str,**details):
        self.manifest["stages"][name]={"status":status,"at":datetime.now(timezone.utc).isoformat(),**details}; self._save_manifest()

    def artifact(self,name:str,path:Path,**details):
        path=Path(path); info={"path":str(path.resolve()),**details}
        if path.exists() and path.is_file(): info.update(size=path.stat().st_size,sha256=self._sha(path))
        self.manifest["artifacts"][name]=info; self._save_manifest()

    @staticmethod
    def _sha(path:Path)->str:
        h=hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
        return h.hexdigest()

    def _save_manifest(self):
        tmp=self.manifest_file.with_suffix(".tmp"); tmp.write_text(json.dumps(self.manifest,indent=2,ensure_ascii=False),encoding="utf-8"); tmp.replace(self.manifest_file)

    def fail(self,error:Exception|str):
        self.manifest["status"]="FAILED"; self.manifest["failed_at"]=datetime.now(timezone.utc).isoformat(); self.manifest["error"]=str(error)[:2000]; self._save_manifest()

    def activate(self,validation:Dict[str,Any]):
        if validation.get("valid") is not True: raise RuntimeError(f"Cannot activate invalid run: {validation}")
        self.manifest["status"]="ACTIVE"; self.manifest["activated_at"]=datetime.now(timezone.utc).isoformat(); self.manifest["validation"]=validation; self._save_manifest()
        pointer={"schema_version":RUN_SCHEMA_VERSION,"run_id":self.run_id,"run_dir":str(self.root.resolve()),"manifest":str(self.manifest_file.resolve()),
                 "activated_at":self.manifest["activated_at"],"input_fingerprint":self.manifest.get("input_fingerprint")}
        self.active_file.parent.mkdir(parents=True,exist_ok=True); tmp=self.active_file.with_suffix(".tmp"); tmp.write_text(json.dumps(pointer,indent=2),encoding="utf-8"); tmp.replace(self.active_file)
        return pointer
