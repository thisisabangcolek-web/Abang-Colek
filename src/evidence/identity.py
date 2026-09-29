"""Stable evidence identity primitives.

External platform identifiers are never used directly as filenames or global IDs.
"""
from __future__ import annotations

import hashlib
from typing import Optional

from src.config import NORMALIZER_VERSION
from src.models.record_kind import RecordKind, canonical_record_kind


def _digest(*parts: object, length: int = 24) -> str:
    text = "\x1f".join(str(p or "") for p in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def make_content_id(platform: str, native_id: str, record_kind: str | RecordKind) -> str:
    kind = record_kind.value if isinstance(record_kind, RecordKind) else str(record_kind)
    return f"cnt_{_digest(str(platform).lower(), kind.upper(), native_id, length=32)}"


def make_capture_id(content_id: str, collector: str, raw_hash: str) -> str:
    return f"cap_{_digest(content_id, collector, raw_hash, length=32)}"


def make_normalized_id(capture_id: str, normalizer_version: str = NORMALIZER_VERSION) -> str:
    return f"norm_{_digest(capture_id, normalizer_version, length=32)}"


def ids_for_record(record: dict, normalizer_version: Optional[str] = None) -> dict:
    kind = canonical_record_kind(record.get("source_type", ""))
    native_id = str(record.get("source_native_id") or record.get("source_id") or "")
    content_id = make_content_id(str(record.get("source_platform") or "unknown"), native_id, kind)
    capture_id = make_capture_id(content_id, str(record.get("collector") or "unknown"), str(record.get("raw_hash") or ""))
    return {
        "record_kind": kind.value,
        "content_id": content_id,
        "capture_id": capture_id,
        "normalized_id": make_normalized_id(capture_id, normalizer_version or NORMALIZER_VERSION),
    }
