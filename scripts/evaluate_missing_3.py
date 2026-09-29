import json
from src.jev.engine import JevEngine
from src.jev.batch_runner import JevBatchRunner

runner = JevBatchRunner()
raw_records = runner.load_raw_sources()
engine = JevEngine(force_fallback=False)

print(f"JEV Engine model: {engine._requested_model()}")

evaluated = 0
for raw in raw_records:
    text = runner._extract_text(raw)
    if not text:
        continue
    ids = raw["_ids"]
    meta = {"record_kind": ids["record_kind"], "platform": raw.get("source_platform")}
    # Check if cached
    bundle = engine.evaluate_bundle(text, metadata=meta)
    if not bundle.get("cached"):
        print(f"Live evaluated: {raw.get('source_platform')} {raw.get('source_id')}")
        evaluated += 1

print(f"Done. Newly live-evaluated: {evaluated}")
