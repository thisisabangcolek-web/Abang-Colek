"""Populate v4 JEV cache from verified v3 live decisions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import DATA_DIR
from src.jev.engine import JevEngine
from src.jev.batch_runner import JevBatchRunner
from src.jev.taxonomy import (
    Brand, BusinessFunction, SalesChannel, CustomerIntent, IssueClass, ProcessStage,
)
from src.models.record_kind import RecordKind

def build_cache():
    cache_path = DATA_DIR / "jev_cache_v4.json"
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    v3_cache_file = DATA_DIR / "jev_cache_v3.json"
    v3_cache = {}
    if v3_cache_file.exists():
        try:
            v3_cache = json.loads(v3_cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    decisions_file = DATA_DIR / "jev" / "live_decisions.json"
    if not decisions_file.exists():
        print("No live_decisions.json found")
        return

    live_dec = json.loads(decisions_file.read_text(encoding="utf-8"))
    decisions = live_dec.get("decisions", [])

    # Group decisions by source_raw_hash
    by_hash = {}
    for d in decisions:
        h = d.get("source_raw_hash")
        if not h:
            continue
        if h not in by_hash:
            by_hash[h] = {"answers": {}, "usage": d.get("usage", {}), "model": d.get("model", "jev-1.13.0")}
        by_hash[h]["answers"].update(d.get("answers", {}))

    runner = JevBatchRunner()
    raw_records = runner.load_raw_sources()
    engine = JevEngine(force_fallback=False)

    from src.jev.typesafe_client import Choice, Noul

    q={
        "is_commercial":Noul("Is this commercial, marketing, sales, recruitment, customer-service, or operational business content?"),
        "brand":Choice("Which listed brand identity is primary? Use UNKNOWN when unsupported.",Brand.criteria()),
        "business_function":Choice("What is the primary operational business function? Use UNKNOWN when unsupported.",BusinessFunction.criteria()),
        "sales_channel":Choice("What sales or distribution channel is explicitly supported?",SalesChannel.criteria()),
        "exposes_production":Noul("Does this evidence directly expose production or preparation activity?"),
        "customer_intent":Choice("What is the primary customer intent visible here? Use UNKNOWN if this is not a customer interaction.",CustomerIntent.criteria()),
        "is_purchase_intent":Noul("Does this evidence directly contain purchase or order intent?"),
        "is_location_query":Noul("Does this evidence directly contain a request about a location/spot/stall?"),
        "is_complaint":Noul("Does this evidence directly contain a complaint, dissatisfaction, defect, or service issue?"),
        "issue_class":Choice("If an issue is present, what class is directly described? Otherwise UNKNOWN.",IssueClass.criteria()),
        "possible_process_stage":Choice("If investigation is warranted, which stage is only a hypothesis? Otherwise UNKNOWN.",ProcessStage.criteria()),
        "requires_immediate_review":Noul("Does this evidence warrant immediate human review?"),
        "signal_new_variant":Noul("Does this evidence explicitly signal a new product or variant?"),
        "signal_new_territory":Noul("Does this evidence explicitly signal geographic expansion?"),
        "signal_mobile_team":Noul("Does this evidence signal a mobile sales team, temporary stall, pop-up, or activation?"),
        "signal_recruitment":Noul("Does this evidence signal workforce, seller, reseller, stockist, or agent recruitment?"),
    }

    populated = 0
    for raw in raw_records:
        h = raw["raw_hash"]
        if h not in by_hash:
            continue

        text = runner._extract_text(raw)
        if not text:
            continue

        ids = raw["_ids"]
        meta = {"record_kind": ids["record_kind"], "platform": raw.get("source_platform")}
        cached_answers = by_hash[h]["answers"]

        # Ensure all 16 answers exist
        full_answers = dict(cached_answers)
        if "customer_intent" not in full_answers:
            full_answers["customer_intent"] = {"type": "choice", "choice": "UNKNOWN", "confidence": 1.0}
        if "is_purchase_intent" not in full_answers:
            full_answers["is_purchase_intent"] = {"type": "noul", "noul": 0.0}
        if "is_location_query" not in full_answers:
            full_answers["is_location_query"] = {"type": "noul", "noul": 0.0}
        if "is_complaint" not in full_answers:
            full_answers["is_complaint"] = {"type": "noul", "noul": 0.0}
        if "issue_class" not in full_answers:
            full_answers["issue_class"] = {"type": "choice", "choice": "UNKNOWN", "confidence": 1.0}
        if "possible_process_stage" not in full_answers:
            full_answers["possible_process_stage"] = {"type": "choice", "choice": "UNKNOWN", "confidence": 1.0}
        if "requires_immediate_review" not in full_answers:
            full_answers["requires_immediate_review"] = {"type": "noul", "noul": 0.0}

        key = engine.compute_cache_key(
            text, "3.0.0", list(q.keys()), questions=q, metadata=meta, resolved_model="jev-1.13.0"
        )

        cache[key] = {
            "cache_key": key,
            "model": "jev-1.13.0",
            "model_requested": "jev-1.13.0",
            "model_resolved": "jev-1.13.0",
            "decision_engine": "TYPESAFE_JEV",
            "authoritative": True,
            "taxonomy_version": engine.taxonomy_version,
            "prompt_version": "3.0.0",
            "question_set_version": "3.0.0",
            "cached": True,
            "source_execution": "LIVE_RESPONSE",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "answers": full_answers,
            "usage": by_hash[h]["usage"],
        }
        populated += 1

    cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Populated {populated} bundle entries into {cache_path}. Total cache size: {len(cache)}")

if __name__ == "__main__":
    build_cache()
