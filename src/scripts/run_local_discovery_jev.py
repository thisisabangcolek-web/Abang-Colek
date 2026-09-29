"""Run live JEV over local discovery leads without promoting them to business truth."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.jev.engine import JevEngine

ROOT = Path("D:/ABANGCOLEK")
SOURCE = ROOT / "data/local_discovery/candidates.json"
OUTPUT = ROOT / "data/jev/local_discovery_decisions.json"
URL_SEEDS = ROOT / "data/local_discovery/public_url_seeds.json"


def _candidate_text(item: dict) -> str:
    if item.get("candidate_type") == "browser_history_url":
        return f"Discovery URL: {item.get('url','')}\nPage title: {item.get('title','')}"
    return f"Local project artifact: {item.get('path','')}\nExcerpt:\n{item.get('excerpt','')}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> dict:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])
    engine = JevEngine(force_fallback=False)
    decisions = []
    public_urls = []
    for idx, item in enumerate(candidates, start=1):
        text = _candidate_text(item)[:6000]
        result = engine.evaluate_bundle(text)
        decision = {
            "discovery_id": f"local_{idx:04d}",
            "candidate_type": item.get("candidate_type"),
            "source_authoritative": False,
            "business_fact_authoritative": False,
            "decision_engine": "TYPESAFE_JEV",
            "model": result.get("model_resolved") or result.get("model"),
            "classified": result.get("classified", {}),
            "answers": result.get("answers", {}),
            "root_cause_status": "UNDETERMINED",
            "candidate": item,
            "evaluated_at": _now(),
        }
        decisions.append(decision)
        if item.get("candidate_type") == "browser_history_url" and item.get("url"):
            public_urls.append(item["url"])
    brands = Counter(d["classified"].get("brand", "UNKNOWN") for d in decisions)
    functions = Counter(d["classified"].get("business_function", "UNKNOWN") for d in decisions)
    summary = {
        "generated_at": _now(),
        "status": "COMPLETE" if decisions else "NO_DISCOVERY_DATA",
        "authoritative_for_business_truth": False,
        "decision_engine": "TYPESAFE_JEV" if decisions else "NOT_RUN",
        "count": len(decisions),
        "models": dict(Counter(d["model"] for d in decisions)),
        "candidate_types": dict(Counter(d["candidate_type"] for d in decisions)),
        "brands": dict(brands),
        "business_functions": dict(functions),
        "complaint_flags": sum(1 for d in decisions if d["classified"].get("is_complaint")),
        "location_flags": sum(1 for d in decisions if d["classified"].get("is_location_query")),
        "recruitment_flags": sum(1 for d in decisions if d["classified"].get("signal_recruitment")),
        "decisions": decisions,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    URL_SEEDS.parent.mkdir(parents=True, exist_ok=True)
    URL_SEEDS.write_text(json.dumps({"generated_at": _now(), "urls": sorted(set(public_urls))}, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "decisions"}, indent=2, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    main()
