import json, hashlib, sys
from src.config import DATA_DIR, RAW_DIR
from src.evidence.identity import ids_for_record
from src.evidence.integrity import business_interpretation_usable, evidence_quality_score, validate_raw_record

missing_hashes = {
    '9b70bcddb26c0d2c88466b0a8805f634b3f3b9ce967da0039ea8bfeec5c92823',
    'a97b750c308b08ab8669e4f50fe0a9e7bc1922c2a392e2e92ec4ad5c4883fc51',
    '2e30386a67322d84814c330fec6600c62c2f6da0684f8eeef24cb613ffda73ad'
}

for p in sorted(RAW_DIR.glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("raw_hash") in missing_hashes:
        payload = d.get("raw_payload", {})
        text = payload.get("visible_text") or payload.get("text") or payload.get("caption") or ""
        print(f"File: {p.name}", flush=True)
        print(f"Platform: {d.get('source_platform')}, ID: {d.get('source_id')}, Type: {d.get('source_type')}", flush=True)
        print(f"Text: {repr(text[:150])}", flush=True)
        print("---", flush=True)
