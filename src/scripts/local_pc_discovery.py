"""Discover ABANGCOLEK-relevant local data without promoting it to business truth."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path("D:/ABANGCOLEK")
OUT = ROOT / "data/local_discovery/candidates.json"
TERMS = [
    "abangcolek", "abang colek", "styloairpool", "airpoolstylo",
    "liurleleh", "liur leleh", "jerux",
]
SOCIAL_HOSTS = (
    "tiktok.com", "instagram.com", "threads.com", "threads.net",
    "facebook.com", "notebook.google.com",
)
TEXT_EXTS = {".txt", ".md", ".json", ".csv", ".html", ".htm", ".yaml", ".yml"}
SKIP_NAMES = {".env", "cookies", "history", "login data", ".webbridge-auth.json"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_url(url: str) -> str:
    try:
        p = urlsplit(url)
        return urlunsplit((p.scheme, p.netloc, p.path, "", ""))
    except Exception:
        return url


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _relevant(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in TERMS)


def collect_browser_history() -> list[dict]:
    roots = [
        Path(r"C:\Users\megat\AppData\Local\Google\Chrome\User Data"),
        Path(r"C:\Users\megat\AppData\Local\Microsoft\Edge\User Data"),
    ]
    found: dict[str, dict] = {}
    for root in roots:
        if not root.exists():
            continue
        for hist in root.glob("*/History"):
            tmp = Path(tempfile.gettempdir()) / f"ac_hist_{abs(hash(str(hist)))}.db"
            try:
                shutil.copy2(hist, tmp)
                con = sqlite3.connect(tmp)
                cur = con.cursor()
                cur.execute("select url,title,visit_count from urls")
                for url, title, visits in cur.fetchall():
                    hay = f"{url or ''} {title or ''}"
                    if not _relevant(hay):
                        continue
                    host = urlsplit(url or "").netloc.lower()
                    if not any(host == h or host.endswith("." + h) for h in SOCIAL_HOSTS):
                        continue
                    clean = _clean_url(url)
                    item = {
                        "candidate_type": "browser_history_url",
                        "source_authoritative": False,
                        "business_fact_authoritative": False,
                        "url": clean,
                        "title": title or "",
                        "visit_count": int(visits or 0),
                        "browser_profile": hist.parent.name,
                        "discovered_at": _now(),
                    }
                    if clean not in found or item["visit_count"] > found[clean]["visit_count"]:
                        found[clean] = item
                con.close()
            except Exception:
                pass
            finally:
                try:
                    tmp.unlink(missing_ok=True)
                except Exception:
                    pass
    return list(found.values())


def _excerpt(text: str, span: int = 700) -> str:
    low = text.lower()
    positions = [low.find(t) for t in TERMS if low.find(t) >= 0]
    pos = min(positions) if positions else 0
    return text[max(0, pos - span): pos + span].strip()


def collect_local_files() -> list[dict]:
    project_roots = [
        Path(r"D:\ABANGCOLEK\docs"),
        Path(r"D:\ABANGCOLEK\reports"),
        Path(r"D:\ABANGCOLEK\src"),
        Path(r"C:\Users\megat\Hermes-WebApp\backend"),
        Path(r"C:\Users\megat\Hermes-WebApp\scripts"),
        Path(r"D:\GangNiaga-WebBridge\daemon"),
        Path(r"D:\GangNiaga-WebBridge\integrations"),
        Path(r"D:\GangNiaga-WebBridge\docs"),
    ]
    personal_roots = [
        Path(r"C:\Users\megat\Desktop"),
        Path(r"C:\Users\megat\Downloads"),
        Path(r"C:\Users\megat\Documents"),
    ]
    out: list[dict] = []
    skip_dirs = {"node_modules", ".git", ".venv", "venv", "__pycache__", "forensic_archive", "legacy", "data"}
    for root in project_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            try:
                if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
                    continue
                if any(part.lower() in skip_dirs for part in path.parts):
                    continue
                if path.name.lower() in SKIP_NAMES or path.stat().st_size > 1_000_000:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if not _relevant(text) and not _relevant(path.name):
                    continue
                out.append(_local_file_candidate(path, text))
            except Exception:
                continue
    for root in personal_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            try:
                if not path.is_file() or not _relevant(path.name):
                    continue
                out.append({
                    "candidate_type": "personal_filename_match",
                    "source_authoritative": False,
                    "business_fact_authoritative": False,
                    "path": str(path),
                    "filename": path.name,
                    "modified_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "discovered_at": _now(),
                })
            except Exception:
                continue
    return out


def _local_file_candidate(path: Path, text: str) -> dict:
    return {
        "candidate_type": "project_text_file",
        "source_authoritative": False,
        "business_fact_authoritative": False,
        "path": str(path),
        "sha256": _sha256_file(path),
        "excerpt": _excerpt(text),
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        "discovered_at": _now(),
    }


def main() -> dict:
    candidates = collect_browser_history() + collect_local_files()
    dedup: dict[str, dict] = {}
    for item in candidates:
        key = item.get("url") or item.get("sha256") or item.get("path") or json.dumps(item, sort_keys=True)
        dedup[str(key)] = item
    payload = {
        "generated_at": _now(),
        "authoritative_for_business_truth": False,
        "purpose": "discovery leads only; public URLs must be recaptured before promotion",
        "count": len(dedup),
        "candidates": list(dedup.values()),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "count": payload["count"],
        "browser_history": sum(1 for x in dedup.values() if x.get("candidate_type") == "browser_history_url"),
        "project_files": sum(1 for x in dedup.values() if x.get("candidate_type") == "project_text_file"),
        "personal_filename_matches": sum(1 for x in dedup.values() if x.get("candidate_type") == "personal_filename_match"),
        "output": str(OUT),
    }, indent=2))
    return payload


if __name__ == "__main__":
    main()
