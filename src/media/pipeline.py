"""Forensic media pipeline. Derived media evidence requires actual local media bytes."""
from __future__ import annotations

import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config import DATA_DIR, RAW_DIR
from src.evidence.integrity import validate_raw_record
from src.models.canonical import MediaAsset


class MediaProcessor:
    DEFAULT_RAW_DIR = RAW_DIR
    DEFAULT_OUTPUT_FILE = DATA_DIR / "media_processed_v4.json"
    V2_OUTPUT_FILE = DEFAULT_OUTPUT_FILE

    def __init__(self, raw_dir: Optional[Union[str, Path]] = None,
                 output_file: Optional[Union[str, Path]] = None):
        self.raw_dir = Path(raw_dir or self.DEFAULT_RAW_DIR)
        self.output_file = Path(output_file or self.DEFAULT_OUTPUT_FILE)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.processed_assets: List[Dict[str, Any]] = []

    @staticmethod
    def file_sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _media_path(record: Dict[str, Any]) -> Optional[Path]:
        payload = record.get("raw_payload", {})
        candidates = []
        if isinstance(payload, dict):
            candidates.extend([payload.get("media_file_path"), payload.get("local_media_path")])
        candidates.extend([record.get("media_file_path"), record.get("local_media_path")])
        for value in candidates:
            if value:
                p = Path(str(value))
                if p.exists() and p.is_file() and p.stat().st_size > 0:
                    return p
        return None

    def extract_media_from_record(self, raw_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        validate_raw_record(raw_record, require_authoritative=True)
        source_id = raw_record.get("source_id", "unknown")
        platform = raw_record.get("source_platform", "unknown")
        media_path = self._media_path(raw_record)
        if media_path is None:
            return [{
                "asset_id": f"media_{platform}_{source_id}",
                "source_platform": platform,
                "source_id": source_id,
                "source_raw_hash": raw_record.get("raw_hash"),
                "media_type": "metadata_only",
                "media_status": "MEDIA_NOT_AVAILABLE",
                "media_file_path": None,
                "sha256_fingerprint": None,
                "url": raw_record.get("source_url", ""),
                "transcript": None,
                "transcript_status": "NOT_RUN",
                "ocr_text": None,
                "ocr_status": "NOT_RUN",
                "visual_description": None,
                "vision_status": "NOT_RUN",
                "packaging_clues": [],
                "product_clues": [],
                "logo_clues": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }]

        media_hash = self.file_sha256(media_path)
        mime, _ = mimetypes.guess_type(str(media_path))
        if mime and mime.startswith("video/"):
            media_type = "video"
        elif mime and mime.startswith("audio/"):
            media_type = "audio"
        elif mime and mime.startswith("image/"):
            media_type = "image"
        else:
            media_type = "document_or_binary"

        # This layer establishes provenance only. ASR/OCR/Vision processors may enrich
        # later, but they must reference this exact media hash.
        return [{
            "asset_id": f"media_{platform}_{source_id}_{media_hash[:12]}",
            "source_platform": platform,
            "source_id": source_id,
            "source_raw_hash": raw_record.get("raw_hash"),
            "media_type": media_type,
            "media_status": "BYTES_VERIFIED",
            "media_file_path": str(media_path.resolve()),
            "sha256_fingerprint": media_hash,
            "url": raw_record.get("source_url", ""),
            "transcript": None,
            "transcript_status": "PENDING_ASR" if media_type in {"video", "audio"} else "NOT_APPLICABLE",
            "ocr_text": None,
            "ocr_status": "PENDING_OCR" if media_type in {"video", "image", "document_or_binary"} else "NOT_APPLICABLE",
            "visual_description": None,
            "vision_status": "PENDING_VISION" if media_type in {"video", "image"} else "NOT_APPLICABLE",
            "packaging_clues": [],
            "product_clues": [],
            "logo_clues": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }]

    def process_raw_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        with open(Path(file_path), "r", encoding="utf-8") as f:
            return self.extract_media_from_record(json.load(f))

    def process_records(self, records: List[Dict[str, Any]], output_file: Optional[Union[str, Path]] = None, run_id: Optional[str] = None, input_fingerprint: Optional[str] = None) -> List[Dict[str, Any]]:
        target = Path(output_file or self.output_file)
        assets: List[Dict[str, Any]] = []
        for record in records:
            for asset in self.extract_media_from_record(record):
                if run_id: asset["run_id"] = run_id
                if input_fingerprint: asset["input_fingerprint"] = input_fingerprint
                assets.append(asset)
        self.processed_assets = assets
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(assets, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(target)
        return assets

    def process_all_sources(self, raw_dir: Optional[Union[str, Path]] = None,
                            output_file: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
        source_dir = Path(raw_dir or self.raw_dir)
        target = Path(output_file or self.output_file)
        assets: List[Dict[str, Any]] = []
        if source_dir.exists():
            for jf in sorted(source_dir.glob("*.json")):
                assets.extend(self.process_raw_file(jf))
        self.processed_assets = assets
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
        return assets

    def to_canonical_media_asset(self, item: Dict[str, Any]) -> MediaAsset:
        return MediaAsset(asset_id=item["asset_id"], media_type=item["media_type"],
                          url=item.get("url"), transcript=item.get("transcript"),
                          ocr_text=item.get("ocr_text"), visual_description=item.get("visual_description"))


MediaProcessorV2 = MediaProcessor
