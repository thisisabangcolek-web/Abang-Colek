"""Hard integrity gate for raw evidence and the atomically active derived run."""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path
from src.config import ACTIVE_RUN_FILE, COVERAGE_FILE, PROJECT_ROOT, RAW_DIR
from src.evidence.integrity import validate_raw_record

def _sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def fail(msg): print(f"FAIL: {msg}"); return False

def main():
    ok=True; modes=Counter(); raw=list(RAW_DIR.glob("*.json")) if RAW_DIR.exists() else []
    for path in raw:
        try:
            v=validate_raw_record(json.loads(path.read_text(encoding="utf-8")),require_authoritative=True); modes[v.get("verification_mode")]+=1
        except Exception as exc: ok=fail(f"{path.name}: {exc}") and ok
    for rel in ["src/jev/batch_runner.py","src/analytics/bi_engine.py","src/media/pipeline.py"]:
        text=(PROJECT_ROOT/rel).read_text(encoding="utf-8").replace("\\","/").lower()
        if "data/synthetic" in text: ok=fail(f"{rel} reads synthetic production data") and ok
    if not COVERAGE_FILE.exists(): ok=fail("coverage manifest missing") and ok
    else:
        src=json.loads(COVERAGE_FILE.read_text(encoding="utf-8")).get("sources",[]); print(f"COVERAGE_SOURCES={len(src)}")
    if ACTIVE_RUN_FILE.exists():
        try:
            pointer=json.loads(ACTIVE_RUN_FILE.read_text(encoding="utf-8")); manifest_path=Path(pointer["manifest"]); manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("status")!="ACTIVE" or (manifest.get("validation") or {}).get("valid") is not True: ok=fail("active run manifest is not valid/ACTIVE") and ok
            for name,art in (manifest.get("artifacts") or {}).items():
                path=Path(art.get("path") or "")
                if not path.exists() or not path.is_file(): ok=fail(f"active artifact missing: {name}") and ok; continue
                if art.get("sha256") and _sha(path)!=art.get("sha256"): ok=fail(f"active artifact hash mismatch: {name}") and ok
            norm_manifest_path=Path((manifest.get("artifacts") or {}).get("normalized_manifest",{}).get("path") or "")
            if norm_manifest_path.exists():
                norm_manifest=json.loads(norm_manifest_path.read_text(encoding="utf-8")); norm_dir=Path(pointer["run_dir"])/"normalized"
                files=norm_manifest.get("files",[])
                if norm_manifest.get("count")!=len(files): ok=fail("normalized manifest count mismatch") and ok
                for row in files:
                    nf=norm_dir/row.get("file","")
                    if not nf.exists() or _sha(nf)!=row.get("sha256"): ok=fail(f"normalized artifact mismatch: {row.get('file')}") and ok
            decisions_path=Path((manifest.get("artifacts") or {}).get("jev_decisions",{}).get("path") or "")
            if decisions_path.exists():
                doc=json.loads(decisions_path.read_text(encoding="utf-8"));
                for d in doc.get("decisions",[]):
                    if d.get("authoritative") is not True or d.get("decision_engine")!="TYPESAFE_JEV" or not d.get("capture_id") or not d.get("normalized_id"):
                        ok=fail(f"invalid active JEV decision: {d.get('decision_id')}") and ok
            media_path=Path((manifest.get("artifacts") or {}).get("media",{}).get("path") or "")
            if media_path.exists():
                for a in json.loads(media_path.read_text(encoding="utf-8")):
                    if (a.get("transcript") or a.get("ocr_text") or a.get("visual_description")) and not a.get("sha256_fingerprint"):
                        ok=fail(f"derived media without byte hash: {a.get('asset_id')}") and ok
            print(f"ACTIVE_RUN={pointer.get('run_id')}")
        except Exception as exc: ok=fail(f"active run verification failed: {exc}") and ok
    else: print("ACTIVE_RUN=NONE")
    print(f"RAW_AUTHORITATIVE_RECORDS={len(raw)}"); print("CAPTURE_VERIFICATION_MODES="+json.dumps(dict(modes),sort_keys=True)); print("INTEGRITY_PASS" if ok else "INTEGRITY_FAIL"); return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
