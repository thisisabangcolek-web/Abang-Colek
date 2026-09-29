"""ABANGCOLEK immutable Evidence Lake collector with provenance enforcement."""
from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.evidence.integrity import EvidenceIntegrityError, validate_raw_record


class BaseCollector:
    DEFAULT_STORAGE_DIR = Path("D:/ABANGCOLEK/data/raw")
    COLLECTOR_VERSION = "2.0.0"

    def __init__(self, storage_dir: Optional[Path] = None, collector_name: Optional[str] = None):
        self.storage_dir = Path(storage_dir or self.DEFAULT_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.collector_name = collector_name or self.__class__.__name__

    @staticmethod
    def compute_sha256(payload: Union[str, bytes, Dict[str, Any]]) -> str:
        if isinstance(payload, bytes):
            data = payload
        elif isinstance(payload, str):
            data = payload.encode("utf-8")
        else:
            data = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sanitize_id(identifier: str) -> str:
        return re.sub(r"[^\w\-]", "_", identifier)

    def ingest(
        self,
        raw_data: Union[Dict[str, Any], str],
        platform: str = "generic",
        source_id: Optional[str] = None,
        source_type: str = "raw_record",
        source_url: Optional[str] = None,
        published_at: Optional[str] = None,
        *,
        access_method: Optional[str] = None,
        capture_receipt: Optional[Dict[str, Any]] = None,
        provenance_verified: bool = False,
        source_native_id: Optional[str] = None,
        owner_export_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        raw_hash = self.compute_sha256(raw_data)
        if not source_id:
            if isinstance(raw_data, dict) and ("id" in raw_data or "source_id" in raw_data):
                source_id = str(raw_data.get("id") or raw_data.get("source_id"))
            else:
                source_id = f"auto_{raw_hash[:8]}"

        safe_platform = self.sanitize_id(platform.lower())
        safe_source_id = self.sanitize_id(str(source_id))
        filename = f"{safe_platform}_{safe_source_id}_{raw_hash}.json"
        target_path = self.storage_dir / filename

        payload = raw_data if isinstance(raw_data, dict) else {}
        synthetic = bool(payload.get("synthetic", False))
        authoritative = bool(payload.get("authoritative", False))
        data_origin = payload.get("data_origin", "")
        evidence_class = payload.get("evidence_class", "RAW_EVIDENCE")

        record = {
            "source_platform": safe_platform,
            "source_type": source_type,
            "source_id": str(source_id),
            "source_native_id": source_native_id or str(source_id),
            "source_url": source_url or "",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "published_at": published_at or "",
            "collector": self.collector_name,
            "collector_version": self.COLLECTOR_VERSION,
            "access_method": access_method or "UNSPECIFIED",
            "capture_receipt": capture_receipt,
            "owner_export_file": owner_export_file,
            "provenance_verified": bool(provenance_verified),
            "data_origin": data_origin,
            "evidence_class": evidence_class,
            "synthetic": synthetic,
            "authoritative": authoritative,
            "raw_hash": raw_hash,
            "raw_payload": raw_data,
        }

        # Authoritative records fail closed. A caller cannot self-assert truth by
        # merely setting synthetic=False/authoritative=True in a Python object.
        if authoritative:
            validate_raw_record(record, require_authoritative=True)
        elif synthetic and self.storage_dir.resolve() == self.DEFAULT_STORAGE_DIR.resolve():
            raise EvidenceIntegrityError("Synthetic records cannot be written to production data/raw")

        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("raw_hash") != raw_hash:
                raise EvidenceIntegrityError(f"Immutability violation at {target_path}")
            return existing

        temp_path = target_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        temp_path.replace(target_path)
        record["filepath"] = str(target_path)
        return record

    def verify_integrity(self, target_path: Union[str, Path]) -> bool:
        path = Path(target_path)
        if not path.exists():
            return False
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        return record.get("raw_hash") == self.compute_sha256(record.get("raw_payload"))
