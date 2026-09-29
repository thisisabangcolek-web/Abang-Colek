"""No-key TikTok metadata backfill from browser-discovered public post URLs using yt-dlp."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import DATA_DIR, RAW_DIR
from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker


class TikTokYtDlpAdapter:
    COLLECTOR_NAME = "tiktok_ytdlp_public_v1"

    def __init__(
        self,
        discovery_file: Optional[Path] = None,
        storage_dir: Optional[Path] = None,
        coverage: Optional[CoverageTracker] = None,
        concurrency: int = 4,
    ) -> None:
        self.discovery_file = Path(discovery_file or DATA_DIR/"coverage"/"discovery"/"tiktok_styloairpool_public_urls.json")
        self.raw_dir = DATA_DIR/"extractor_raw"/"tiktok"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint = DATA_DIR/"coverage"/"checkpoints"/"tiktok_ytdlp_processed.json"
        self.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        self.collector = BaseCollector(storage_dir=storage_dir or RAW_DIR, collector_name=self.COLLECTOR_NAME)
        self.coverage = coverage or CoverageTracker()
        self.concurrency = max(1, min(int(concurrency), 6))
        self.bin = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")

    def _load_urls(self) -> List[str]:
        if not self.discovery_file.exists():
            return []
        data = json.loads(self.discovery_file.read_text(encoding="utf-8"))
        return list(dict.fromkeys(str(x) for x in data.get("urls", []) if "/@styloairpool/" in str(x)))

    def _load_checkpoint(self) -> Dict[str, Any]:
        if not self.checkpoint.exists():
            return {"processed": {}, "failed": {}}
        try:
            return json.loads(self.checkpoint.read_text(encoding="utf-8"))
        except Exception:
            return {"processed": {}, "failed": {}}

    def _save_checkpoint(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp = self.checkpoint.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.checkpoint)

    @staticmethod
    def _stable_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
        keys = [
            "id", "title", "description", "timestamp", "upload_date", "duration",
            "channel", "channel_id", "channel_url", "uploader", "uploader_id", "uploader_url",
            "track", "artists", "view_count", "like_count", "repost_count", "comment_count",
            "save_count", "webpage_url", "original_url", "extractor", "extractor_key",
            "width", "height", "aspect_ratio",
        ]
        out = {k: data.get(k) for k in keys if data.get(k) is not None}
        out.update({
            "data_origin": "PUBLIC_PLATFORM",
            "evidence_class": "RAW_EVIDENCE",
            "synthetic": False,
            "authoritative": True,
            "provenance_verified": True,
            "metadata_extractor": "yt-dlp",
        })
        return out

    async def _extract_one(self, url: str, sem: asyncio.Semaphore) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
        if not self.bin:
            return url, None, "yt-dlp executable not found"
        async with sem:
            proc = await asyncio.create_subprocess_exec(
                self.bin,
                "--dump-single-json",
                "--skip-download",
                "--no-warnings",
                "--socket-timeout", "20",
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=45)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return url, None, "timeout"
            if proc.returncode != 0 or not stdout:
                msg = stderr.decode("utf-8", errors="replace")[-800:]
                return url, None, f"yt-dlp exit {proc.returncode}: {msg}"
            try:
                data = json.loads(stdout.decode("utf-8", errors="replace"))
            except Exception as exc:
                return url, None, f"invalid JSON: {exc}"
            raw_hash = hashlib.sha256(stdout).hexdigest()
            video_id = str(data.get("id") or url.rstrip("/").split("/")[-1])
            raw_path = self.raw_dir / f"{video_id}_{raw_hash}.json"
            if not raw_path.exists():
                raw_path.write_bytes(stdout)
            data["_raw_output_sha256"] = raw_hash
            data["_raw_output_path"] = str(raw_path)
            return url, data, None

    def _ingest(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        video_id = str(data.get("id") or url.rstrip("/").split("/")[-1])
        raw_sha = str(data.pop("_raw_output_sha256"))
        raw_path = str(data.pop("_raw_output_path"))
        payload = self._stable_metadata(data)
        version = "unknown"
        ver = data.get("_version")
        if isinstance(ver, dict):
            version = str(ver.get("version") or "unknown")
        receipt = {
            "capture_method": "YT_DLP_PUBLIC_METADATA",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "source_url": url,
            "stdout_sha256": raw_sha,
            "raw_output_file": raw_path,
            "yt_dlp_version": version,
            "api_key_used": False,
            "credentials_exported": False,
        }
        published_at = ""
        if data.get("timestamp"):
            try:
                published_at = datetime.fromtimestamp(float(data["timestamp"]), tz=timezone.utc).isoformat()
            except Exception:
                pass
        return self.collector.ingest(
            raw_data=payload,
            platform="tiktok",
            source_id=video_id,
            source_native_id=video_id,
            source_type="public_video_metadata",
            source_url=str(data.get("webpage_url") or url),
            published_at=published_at,
            access_method="YT_DLP_PUBLIC",
            capture_receipt=receipt,
            provenance_verified=True,
        )

    async def collect_all(self, retry_failed: bool = True) -> Dict[str, Any]:
        urls = self._load_urls()
        state = self._load_checkpoint()
        processed: Dict[str, Any] = state.setdefault("processed", {})
        failed: Dict[str, Any] = state.setdefault("failed", {})
        if not urls:
            self.coverage.register_source(
                "tiktok", "@styloairpool:yt-dlp", CoverageStatus.NOT_STARTED,
                notes="No browser-discovered TikTok URLs available", data_origin="PUBLIC_PLATFORM",
                known_gaps=["Run public browser discovery first"],
            )
            return {"discovered": 0, "processed": 0, "failed": 0}

        pending = []
        for url in urls:
            vid = url.rstrip("/").split("/")[-1]
            if vid in processed:
                continue
            if vid in failed and not retry_failed:
                continue
            pending.append(url)

        sem = asyncio.Semaphore(self.concurrency)
        tasks = [asyncio.create_task(self._extract_one(url, sem)) for url in pending]
        for future in asyncio.as_completed(tasks):
            url, data, error = await future
            vid = str((data or {}).get("id") or url.rstrip("/").split("/")[-1])
            if data is not None:
                try:
                    rec = self._ingest(url, data)
                    processed[vid] = {"source_url": url, "raw_hash": rec.get("raw_hash"), "at": datetime.now(timezone.utc).isoformat()}
                    failed.pop(vid, None)
                except Exception as exc:
                    failed[vid] = {"source_url": url, "error": str(exc)[:700]}
            else:
                failed[vid] = {"source_url": url, "error": str(error)[:700]}
            self._save_checkpoint(state)

        dates: List[str] = []
        for path in self.collector.storage_dir.glob("tiktok_*.json"):
            try:
                rec = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if rec.get("collector") != self.COLLECTOR_NAME:
                continue
            if rec.get("published_at"):
                dates.append(rec["published_at"])

        status = CoverageStatus.PARTIAL_UNKNOWN if failed or len(processed) < len(urls) else CoverageStatus.PARTIAL_PLATFORM_LIMIT
        self.coverage.register_source(
            "tiktok", "@styloairpool:yt-dlp", status,
            record_count=len(processed), posts_recovered=len(processed),
            oldest_recovered_at=min(dates) if dates else None,
            newest_recovered_at=max(dates) if dates else None,
            pagination_exhausted=False,
            data_origin="PUBLIC_PLATFORM",
            known_gaps=[
                "URL discovery derives from public profile scrolling and cannot prove deleted/private history completeness",
                "Comments/replies require a separate browser/session collection lane",
            ] + ([f"{len(failed)} discovered URLs failed metadata extraction"] if failed else []),
            notes=f"No-key yt-dlp metadata for {len(processed)}/{len(urls)} browser-discovered URLs; failed={len(failed)}.",
            api_key_used=False,
        )
        return {"discovered": len(urls), "processed": len(processed), "failed": len(failed), "pending": max(0, len(urls)-len(processed)-len(failed))}


def main() -> None:
    result = asyncio.run(TikTokYtDlpAdapter().collect_all())
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
