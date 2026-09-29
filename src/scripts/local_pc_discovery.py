"""Opt-in discovery of ABANGCOLEK-relevant local leads.

Local material is DISCOVERY_ONLY. It is never promoted directly to business truth.
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, sqlite3, tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from src.config import DATA_DIR, LOCAL_DISCOVERY_ENABLED, LOCAL_DISCOVERY_ROOTS, PROJECT_ROOT

OUT=DATA_DIR/"local_discovery"/"candidates.json"
TERMS=["abangcolek","abang colek","styloairpool","airpoolstylo","liurleleh","liur leleh","jerux"]
SOCIAL_HOSTS=("tiktok.com","instagram.com","threads.com","threads.net","facebook.com")
TEXT_EXTS={".txt",".md",".json",".csv",".html",".htm",".yaml",".yml"}
SKIP_NAMES={".env","cookies","history","login data",".webbridge-auth.json"}
SKIP_DIRS={"node_modules",".git",".venv","venv","__pycache__","forensic_archive","legacy","data","quarantine"}
PERSONAL_FILENAME_DISCOVERY=os.getenv("ABANGCOLEK_LOCAL_DISCOVERY_PERSONAL","0").lower() in {"1","true","yes"}


def _now(): return datetime.now(timezone.utc).isoformat()
def _relevant(text:str): return any(t in text.lower() for t in TERMS)
def _clean_url(url:str):
    try:
        p=urlsplit(url); return urlunsplit((p.scheme,p.netloc,p.path,"",""))
    except Exception: return url
def _sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def redact_for_external(text:str)->str:
    """Redact obvious personal identifiers before optional external JEV processing."""
    text=re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}","[REDACTED_EMAIL]",text)
    text=re.sub(r"(?<!\d)(?:\+?6?0)?1\d[-\s]?\d{3,4}[-\s]?\d{4}(?!\d)","[REDACTED_PHONE]",text)
    text=re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+",r"\1=[REDACTED]",text)
    return text

def _excerpt(text:str,span:int=700)->str:
    low=text.lower(); positions=[low.find(t) for t in TERMS if low.find(t)>=0]; pos=min(positions) if positions else 0
    return redact_for_external(text[max(0,pos-span):pos+span].strip())

def _browser_history_roots()->list[Path]:
    local=Path(os.getenv("LOCALAPPDATA",str(Path.home()/"AppData/Local")))
    return [local/"Google/Chrome/User Data",local/"Microsoft/Edge/User Data"]

def collect_browser_history()->list[dict]:
    found={}
    for root in _browser_history_roots():
        if not root.exists(): continue
        for hist in root.glob("*/History"):
            tmp=Path(tempfile.gettempdir())/f"ac_hist_{abs(hash(str(hist)))}.db"
            try:
                shutil.copy2(hist,tmp); con=sqlite3.connect(tmp); cur=con.cursor(); cur.execute("select url,title,visit_count from urls")
                for url,title,visits in cur.fetchall():
                    hay=f"{url or ''} {title or ''}"
                    if not _relevant(hay): continue
                    host=urlsplit(url or "").netloc.lower()
                    if not any(host==h or host.endswith("."+h) for h in SOCIAL_HOSTS): continue
                    clean=_clean_url(url)
                    item={"candidate_type":"browser_history_url","source_authoritative":False,"business_fact_authoritative":False,
                          "url":clean,"title":redact_for_external(title or ""),"visit_count":int(visits or 0),"browser_profile":hist.parent.name,"discovered_at":_now()}
                    if clean not in found or item["visit_count"]>found[clean]["visit_count"]: found[clean]=item
                con.close()
            except Exception: pass
            finally:
                try: tmp.unlink(missing_ok=True)
                except Exception: pass
    return list(found.values())

def _project_roots()->list[Path]:
    if LOCAL_DISCOVERY_ROOTS: return [p for p in LOCAL_DISCOVERY_ROOTS if p.exists()]
    return [PROJECT_ROOT/"docs",PROJECT_ROOT/"reports",PROJECT_ROOT/"src"]

def _local_file_candidate(path:Path,text:str)->dict:
    return {"candidate_type":"project_text_file","source_authoritative":False,"business_fact_authoritative":False,
            "path":str(path),"sha256":_sha256_file(path),"excerpt":_excerpt(text),
            "modified_at":datetime.fromtimestamp(path.stat().st_mtime,tz=timezone.utc).isoformat(),"discovered_at":_now()}
def collect_local_files()->list[dict]:
    out=[]
    for root in _project_roots():
        if not root.exists(): continue
        for path in root.rglob("*"):
            try:
                if not path.is_file() or path.suffix.lower() not in TEXT_EXTS: continue
                if any(part.lower() in SKIP_DIRS for part in path.parts): continue
                if path.name.lower() in SKIP_NAMES or path.stat().st_size>1_000_000: continue
                text=path.read_text(encoding="utf-8",errors="ignore")
                if _relevant(text) or _relevant(path.name): out.append(_local_file_candidate(path,text))
            except Exception: continue
    if PERSONAL_FILENAME_DISCOVERY:
        home=Path.home()
        for root in [home/"Desktop",home/"Downloads",home/"Documents"]:
            if not root.exists(): continue
            for path in root.rglob("*"):
                try:
                    if path.is_file() and _relevant(path.name):
                        out.append({"candidate_type":"personal_filename_match","source_authoritative":False,"business_fact_authoritative":False,
                                    "path":str(path),"filename":path.name,"modified_at":datetime.fromtimestamp(path.stat().st_mtime,tz=timezone.utc).isoformat(),"discovered_at":_now()})
                except Exception: continue
    return out

def main(enabled:bool|None=None)->dict:
    enabled=LOCAL_DISCOVERY_ENABLED if enabled is None else bool(enabled)
    if not enabled:
        return {"status":"DISABLED","count":0,"authoritative_for_business_truth":False,"candidates":[]}
    candidates=collect_browser_history()+collect_local_files(); dedup={}
    for item in candidates:
        key=item.get("url") or item.get("sha256") or item.get("path") or json.dumps(item,sort_keys=True); dedup[str(key)]=item
    payload={"generated_at":_now(),"status":"COMPLETE","authoritative_for_business_truth":False,
             "purpose":"discovery leads only; public URLs must be recaptured before promotion",
             "roots":[str(x) for x in _project_roots()],"count":len(dedup),"candidates":list(dedup.values())}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    preview=OUT.with_name("preview.json")
    preview.write_text(json.dumps({"generated_at":payload["generated_at"],"count":payload["count"],"candidates":payload["candidates"]},indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"status":payload["status"],"count":payload["count"],"browser_history":sum(1 for x in dedup.values() if x.get("candidate_type")=="browser_history_url"),
                      "project_files":sum(1 for x in dedup.values() if x.get("candidate_type")=="project_text_file"),"output":str(OUT)},indent=2))
    return payload

if __name__=="__main__": main(enabled=True)
