from __future__ import annotations

from typing import Any, Dict

ALLOWED_AUTHORITATIVE_ORIGINS = {
    "OWNER_EXPORT", "OFFICIAL_API", "OWNER_AUTHORIZED_API",
    "PUBLIC_PLATFORM", "PUBLIC_WEB", "SEARCH_INDEX",
    "ARCHIVE", "MANUAL_OWNER_UPLOAD",
}

class EvidenceIntegrityError(RuntimeError):
    pass

def _payload(record: Dict[str, Any]) -> Dict[str, Any]:
    p = record.get("raw_payload", {})
    return p if isinstance(p, dict) else {}

def field(record: Dict[str, Any], name: str, default: Any = None) -> Any:
    if name in record:
        return record.get(name, default)
    return _payload(record).get(name, default)

def validate_raw_record(record: Dict[str, Any], *, require_authoritative: bool = False) -> None:
    synthetic = bool(field(record, "synthetic", False))
    authoritative = bool(field(record, "authoritative", False))
    provenance_verified = bool(field(record, "provenance_verified", False))
    origin = str(field(record, "data_origin", "") or "")
    source_url = str(record.get("source_url", "") or "")
    receipt = field(record, "capture_receipt")
    owner_export_file = field(record, "owner_export_file")
    raw_hash = record.get("raw_hash")

    if synthetic:
        raise EvidenceIntegrityError("Synthetic records are forbidden in the production Evidence Lake")
    if require_authoritative and not authoritative:
        raise EvidenceIntegrityError("Authoritative pipeline requires authoritative evidence")
    if authoritative:
        if origin not in ALLOWED_AUTHORITATIVE_ORIGINS:
            raise EvidenceIntegrityError(f"Unsupported authoritative data_origin: {origin!r}")
        if not provenance_verified:
            raise EvidenceIntegrityError("authoritative=True requires provenance_verified=True")
        if not (receipt or owner_export_file or source_url):
            raise EvidenceIntegrityError("Authoritative evidence requires capture_receipt, owner_export_file, or source_url")
    if not raw_hash:
        raise EvidenceIntegrityError("Raw evidence requires raw_hash")

def production_eligible(record: Dict[str, Any]) -> bool:
    try:
        validate_raw_record(record, require_authoritative=True)
        return True
    except EvidenceIntegrityError:
        return False
