"""Environment and project health check. Never prints secret values."""
from __future__ import annotations
import importlib.metadata as metadata
import json, os, shutil, sys
from pathlib import Path
from src.config import ACTIVE_RUN_FILE, COVERAGE_FILE, PROJECT_ROOT, RAW_DIR
from src.evidence.integrity import validate_raw_record
from src.jev.typesafe_client import _load_local_env

def _version(name:str):
    try: return metadata.version(name)
    except Exception: return None

def main()->dict:
    _load_local_env()
    checks={
        "project_root":str(PROJECT_ROOT),
        "python":{"version":sys.version.split()[0],"ok":sys.version_info[:2]>=(3,11)},
        "packages":{"pydantic":_version("pydantic"),"playwright":_version("playwright"),"pytest":_version("pytest")},
        "executables":{"yt-dlp":shutil.which("yt-dlp") or shutil.which("yt-dlp.exe"),"gallery-dl":shutil.which("gallery-dl") or shutil.which("gallery-dl.exe")},
        "secrets_present":{"TYPESAFE_API_KEY":bool(os.getenv("TYPESAFE_API_KEY"))},
        "coverage_manifest":COVERAGE_FILE.exists(),"active_run":None,"raw_records":0,"raw_invalid":[],
    }
    if ACTIVE_RUN_FILE.exists():
        try: checks["active_run"]=json.loads(ACTIVE_RUN_FILE.read_text(encoding="utf-8"))
        except Exception as exc: checks["active_run"]={"invalid":str(exc)}
    for path in sorted(RAW_DIR.glob("*.json")) if RAW_DIR.exists() else []:
        checks["raw_records"]+=1
        try: validate_raw_record(json.loads(path.read_text(encoding="utf-8")),require_authoritative=True)
        except Exception as exc: checks["raw_invalid"].append({"file":path.name,"error":str(exc)})
    checks["ok"]=bool(checks["python"]["ok"] and checks["packages"]["pydantic"] and checks["packages"]["playwright"] and checks["coverage_manifest"] and not checks["raw_invalid"])
    print(json.dumps(checks,indent=2,ensure_ascii=False)); return checks

if __name__=="__main__": raise SystemExit(0 if main()["ok"] else 1)
