"""Strict integrity and provenance verification for authoritative evidence."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict

ALLOWED_AUTHORITATIVE_ORIGINS = {
    "OWNER_EXPORT", "OFFICIAL_API", "OWNER_AUTHORIZED_API", "PUBLIC_PLATFORM",
    "PUBLIC_WEB", "SEARCH_INDEX", "ARCHIVE", "MANUAL_OWNER_UPLOAD",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.I)


class EvidenceIntegrityError(RuntimeError):
    pass


def _payload(record: Dict[str, Any]) -> Any:
    return record.get("raw_payload", {})


def field(record: Dict[str, Any], name: str, default: Any = None) -> Any:
    if name in record:
        return record.get(name, default)
    payload = _payload(record)
    return payload.get(name, default) if isinstance(payload, dict) else default


def payload_sha256(payload: Any) -> str:
    if isinstance(payload, bytes):
        data = payload
    elif isinstance(payload, str):
        data = payload.encode("utf-8")
    else:
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _require_bool(record: Dict[str, Any], name: str) -> bool:
    value = field(record, name, False)
    if type(value) is not bool:
        raise EvidenceIntegrityError(f"{name} must be a real boolean")
    return value


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def verify_capture(record: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the capture receipt without changing immutable raw evidence.

    Legacy Playwright snapshots are accepted when the stored pre-write UTF-8 text hash
    matches after universal newline normalization; new captures should use byte hashes.
    """
    receipt = field(record, "capture_receipt")
    owner_export_file = field(record, "owner_export_file")
    payload = _payload(record)
    details: Dict[str, Any] = {"capture_verified": False, "verification_mode": None}

    if owner_export_file:
        path = Path(str(owner_export_file))
        if not path.exists() or not path.is_file():
            raise EvidenceIntegrityError(f"Owner export file missing: {path}")
        expected = receipt.get("owner_export_sha256") if isinstance(receipt, dict) else None
        if not _valid_sha(expected) or file_sha256(path) != expected:
            raise EvidenceIntegrityError("Owner export file hash does not match receipt")
        details.update(capture_verified=True, verification_mode="OWNER_EXPORT_FILE_SHA256")
        return details

    if not isinstance(receipt, dict) or not receipt:
        raise EvidenceIntegrityError("Authoritative evidence requires a non-empty capture_receipt")

    raw_output = receipt.get("raw_output_file")
    stdout_sha = receipt.get("stdout_sha256")
    if raw_output or stdout_sha:
        path = Path(str(raw_output or ""))
        if not path.exists() or not _valid_sha(stdout_sha) or file_sha256(path) != stdout_sha:
            raise EvidenceIntegrityError("Extractor raw-output receipt failed SHA-256 verification")
        details.update(capture_verified=True, verification_mode="EXTRACTOR_RAW_BYTES_SHA256")
        return details

    html_hash = receipt.get("html_bytes_sha256") or receipt.get("html_sha256")
    snapshot = payload.get("html_snapshot") if isinstance(payload, dict) else None
    if html_hash or snapshot:
        if not snapshot:
            raise EvidenceIntegrityError("Browser receipt declares an HTML hash but no snapshot file")
        path = Path(str(snapshot))
        if not path.exists() or not path.is_file() or not _valid_sha(html_hash):
            raise EvidenceIntegrityError("Browser capture snapshot/hash is missing or invalid")
        exact = file_sha256(path)
        if exact == html_hash:
            details.update(capture_verified=True, verification_mode="HTML_BYTES_SHA256")
            return details
        # Legacy collector hashed the Python string before Windows newline conversion.
        text_hash = hashlib.sha256(path.read_text(encoding="utf-8", errors="replace").encode("utf-8")).hexdigest()
        if text_hash == html_hash:
            details.update(capture_verified=True, verification_mode="LEGACY_CANONICAL_TEXT_SHA256")
            return details
        raise EvidenceIntegrityError("Browser snapshot does not match any declared HTML hash mode")

    response_sha = receipt.get("response_sha256")
    if response_sha:
        if not _valid_sha(response_sha):
            raise EvidenceIntegrityError("API response_sha256 is malformed")
        status = receipt.get("http_status")
        if status is not None and (not isinstance(status, int) or not (100 <= status <= 599)):
            raise EvidenceIntegrityError("API http_status is invalid")
        details.update(capture_verified=True, verification_mode="API_RESPONSE_RECEIPT_SHA256")
        return details

    raise EvidenceIntegrityError("Capture receipt has no verifiable hash material")


def validate_raw_record(record: Dict[str, Any], *, require_authoritative: bool = False) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise EvidenceIntegrityError("Raw evidence must be a JSON object")
    synthetic = _require_bool(record, "synthetic")
    authoritative = _require_bool(record, "authoritative")
    provenance_verified = _require_bool(record, "provenance_verified")
    origin = str(field(record, "data_origin", "") or "")
    raw_hash = record.get("raw_hash")

    if synthetic:
        raise EvidenceIntegrityError("Synthetic records are forbidden in the production Evidence Lake")
    if require_authoritative and not authoritative:
        raise EvidenceIntegrityError("Authoritative pipeline requires authoritative evidence")
    if not _valid_sha(raw_hash):
        raise EvidenceIntegrityError("raw_hash must be a 64-character SHA-256 hex string")
    computed = payload_sha256(_payload(record))
    if computed != raw_hash:
        raise EvidenceIntegrityError(f"raw_hash mismatch: stored={raw_hash} computed={computed}")

    capture = {"capture_verified": False, "verification_mode": None}
    if authoritative:
        if origin not in ALLOWED_AUTHORITATIVE_ORIGINS:
            raise EvidenceIntegrityError(f"Unsupported authoritative data_origin: {origin!r}")
        if not provenance_verified:
            raise EvidenceIntegrityError("authoritative=True requires provenance_verified=True")
        capture = verify_capture(record)

    return {
        "payload_hash_verified": True,
        "capture_verified": bool(capture.get("capture_verified")),
        "capture_verification_mode": capture.get("verification_mode"),
        "verification_mode": capture.get("verification_mode"),
        "claim_verified": False,
    }


def production_eligible(record: Dict[str, Any]) -> bool:
    try:
        result = validate_raw_record(record, require_authoritative=True)
        return bool(result.get("capture_verified"))
    except EvidenceIntegrityError:
        return False


def business_interpretation_usable(record: Dict[str, Any]) -> bool:
    explicit = field(record, "usable_for_business_interpretation")
    if explicit is not None:
        return explicit is True
    payload = _payload(record)
    text = ""
    if isinstance(payload, dict):
        text = f"{payload.get('title','')}\n{payload.get('visible_text','')}".lower()
    blocked_markers = (
        "verify to continue", "security check", "captcha", "unusual traffic",
        "access denied", "challenge required", "something went wrong",
    )
    return not any(marker in text for marker in blocked_markers)


def evidence_quality_score(record: Dict[str, Any]) -> tuple:
    """Deterministic quality ordering; higher is better than merely newer."""
    usable = 1 if business_interpretation_usable(record) else 0
    payload = _payload(record)
    text_len = 0
    if isinstance(payload, dict):
        for key in ("text", "visible_text", "caption", "description", "video_description", "title"):
            value = payload.get(key)
            if isinstance(value, str):
                text_len = max(text_len, len(value.strip()))
    origin_rank = {
        "OWNER_EXPORT": 5, "OWNER_AUTHORIZED_API": 5, "OFFICIAL_API": 5,
        "PUBLIC_PLATFORM": 4, "PUBLIC_WEB": 3, "ARCHIVE": 2, "SEARCH_INDEX": 1,
    }.get(str(field(record, "data_origin", "")), 0)
    return (usable, origin_rank, text_len, str(record.get("captured_at", "")))
