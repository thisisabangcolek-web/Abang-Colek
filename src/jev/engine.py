"""Strict, fail-closed TypeSafe JEV decision engine."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import DATA_DIR, JEV_PROMPT_VERSION
from .taxonomy import TAXONOMY_VERSION, Brand, BusinessFunction, SalesChannel, CustomerIntent, IssueClass, ProcessStage, RootCauseStatus
from .typesafe_client import TypeSafeJevClient, Choice, Noul, Score


class JevUnavailableError(RuntimeError):
    pass


class JevInvalidResponseError(RuntimeError):
    pass


class JevEngine:
    DEFAULT_CACHE_FILE = DATA_DIR / "jev_cache_v4.json"

    def __init__(self, api_key: Optional[str] = None, cache_file: Optional[Path] = None,
                 force_fallback: bool = False, authoritative: bool = True, client: Any = None):
        self.taxonomy_version = TAXONOMY_VERSION
        self.cache_file = Path(cache_file or self.DEFAULT_CACHE_FILE)
        self.force_fallback = bool(force_fallback)
        self.authoritative = bool(authoritative and not force_fallback)
        self.client = client
        self.client_error: Optional[str] = None
        if self.client is None and not self.force_fallback:
            try:
                self.client = TypeSafeJevClient(api_key=api_key)
            except Exception as exc:
                self.client_error = str(exc)
        self._cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                self._cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                self._cache = {}
        elif (DATA_DIR / "jev_cache_v3.json").exists():
            try:
                self._cache = json.loads((DATA_DIR / "jev_cache_v3.json").read_text(encoding="utf-8"))
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._cache, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.cache_file)

    @staticmethod
    def _schema(questions: Dict[str, Any]) -> Dict[str, Any]:
        return {k: (v.to_dict() if hasattr(v, "to_dict") else v) for k, v in questions.items()}

    def _requested_model(self) -> str:
        if self.force_fallback:
            return "jev-fallback-deterministic"
        if self.client is None:
            raise JevUnavailableError(f"Live TypeSafe JEV unavailable: {self.client_error or 'client not initialized'}")
        try:
            return str(self.client.resolve_model())
        except Exception as exc:
            raise JevUnavailableError(f"JEV model resolution failed: {exc}") from exc

    def compute_cache_key(self, text: str, version: str, keys: List[str], *, questions: Optional[Dict[str, Any]] = None,
                          metadata: Optional[Dict[str, Any]] = None, resolved_model: Optional[str] = None) -> str:
        state_hash = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
        schema = self._schema(questions or {})
        schema_hash = hashlib.sha256(json.dumps(schema, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        metadata_hash = hashlib.sha256(json.dumps(metadata or {}, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()
        model = resolved_model or self._requested_model()
        material = {
            "state_hash": state_hash,
            "taxonomy_version": self.taxonomy_version,
            "question_set_version": version,
            "prompt_version": JEV_PROMPT_VERSION,
            "question_keys": sorted(keys),
            "question_schema_hash": schema_hash,
            "metadata_hash": metadata_hash,
            "model": model,
            "mode": "live" if self.authoritative else "fallback",
        }
        return hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()

    def _cached(self, key: str, requested_model: str) -> Optional[Dict[str, Any]]:
        # Mutable aliases cannot safely reuse cache across backend model changes.
        if any(alias in requested_model.lower() for alias in ("preview", "latest")):
            return None
        item = self._cache.get(key)
        if not isinstance(item, dict):
            return None
        if self.authoritative:
            if item.get("authoritative") is not True or item.get("decision_engine") != "TYPESAFE_JEV":
                return None
            if item.get("model_resolved") != requested_model:
                return None
        out = dict(item)
        out["cached"] = True
        out["source_execution"] = "CACHE_REUSE"
        out["cache_retrieved_at"] = datetime.now(timezone.utc).isoformat()
        return out

    def _finish(self, key: str, out: Dict[str, Any]) -> Dict[str, Any]:
        self._cache[key] = out
        self._save_cache()
        return out

    @staticmethod
    def _validate_answers(questions: Dict[str, Any], answers: Any) -> Dict[str, Any]:
        if not isinstance(answers, dict):
            raise JevInvalidResponseError("JEV answers must be an object")
        missing = [key for key in questions if key not in answers]
        if missing:
            raise JevInvalidResponseError(f"JEV response missing required answers: {missing}")
        for key, question in questions.items():
            answer = answers[key]
            if not isinstance(answer, dict):
                raise JevInvalidResponseError(f"Answer {key!r} must be an object")
            if isinstance(question, Noul):
                value = answer.get("noul")
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not (0.0 <= float(value) <= 1.0):
                    raise JevInvalidResponseError(f"Answer {key!r} requires noul probability in [0,1]")
            elif isinstance(question, Choice):
                choice = answer.get("choice")
                if choice not in question.criteria:
                    raise JevInvalidResponseError(f"Answer {key!r} choice {choice!r} is outside criteria")
                confidence = answer.get("confidence")
                if confidence is not None and (not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0)):
                    raise JevInvalidResponseError(f"Answer {key!r} confidence is invalid")
            elif isinstance(question, Score):
                value = answer.get("score")
                if value is None:
                    raise JevInvalidResponseError(f"Answer {key!r} requires score")
        return answers

    def _live(self, text: str, questions: Dict[str, Any], key: str, version: str, requested_model: str) -> Dict[str, Any]:
        if self.client is None:
            raise JevUnavailableError(f"Live TypeSafe JEV unavailable: {self.client_error or 'client not initialized'}")
        try:
            raw = self.client.system_one(state=text, questions=questions)
        except Exception as exc:
            raise JevUnavailableError(f"Live TypeSafe JEV call failed: {exc}") from exc
        model_resolved = raw.get("model")
        if not isinstance(model_resolved, str) or not model_resolved or "fallback" in model_resolved.lower():
            raise JevInvalidResponseError("JEV response must declare the actual resolved model")
        answers = self._validate_answers(questions, raw.get("answers"))
        return {
            "cache_key": key,
            "model": model_resolved,
            "model_requested": requested_model,
            "model_resolved": model_resolved,
            "decision_engine": "TYPESAFE_JEV",
            "authoritative": True,
            "taxonomy_version": self.taxonomy_version,
            "prompt_version": JEV_PROMPT_VERSION,
            "question_set_version": version,
            "cached": False,
            "source_execution": "LIVE_RESPONSE",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "answers": answers,
            "usage": raw.get("usage", {}),
        }

    def _fallback(self, key: str, version: str, classified: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "cache_key": key,
            "model": "jev-fallback-deterministic",
            "model_requested": None,
            "model_resolved": None,
            "decision_engine": "RULE_FALLBACK",
            "authoritative": False,
            "taxonomy_version": self.taxonomy_version,
            "prompt_version": JEV_PROMPT_VERSION,
            "question_set_version": version,
            "cached": False,
            "source_execution": "RULE_FALLBACK",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "answers": {},
            "usage": {},
            "classified": classified,
        }

    def _evaluate(self, text: str, version: str, questions: Dict[str, Any], *, metadata: Optional[Dict[str, Any]] = None,
                  fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        keys = list(questions)
        if self.force_fallback:
            key = self.compute_cache_key(text, version, keys, questions=questions, metadata=metadata,
                                         resolved_model="jev-fallback-deterministic")
            cached = self._cached(key, "jev-fallback-deterministic")
            if cached:
                return cached
            return self._finish(key, self._fallback(key, version, fallback or {}))
        requested = self._requested_model()
        key = self.compute_cache_key(text, version, keys, questions=questions, metadata=metadata, resolved_model=requested)
        cached = self._cached(key, requested)
        if cached:
            return cached
        return self._finish(key, self._live(text, questions, key, version, requested))

    @staticmethod
    def _bool(answer: Dict[str, Any]) -> bool:
        return float(answer["noul"]) > 0.5

    def evaluate_content(self, text: str, question_set_version: str = "2.0.0", metadata=None):
        q = {
            "is_commercial": Noul("Is this commercial, marketing, sales, recruitment, customer-service, or operational business content?"),
            "brand": Choice("Which listed brand identity is primary? Abstain with UNKNOWN when unsupported.", Brand.criteria()),
            "business_function": Choice("What is the primary business function? Use UNKNOWN when unsupported.", BusinessFunction.criteria()),
            "sales_channel": Choice("What sales/distribution channel is explicitly supported?", SalesChannel.criteria()),
            "exposes_production": Noul("Does this evidence directly expose production/preparation activity?"),
        }
        low=text.lower(); fallback={
            "is_commercial": any(x in low for x in ("order","beli","harga","stok","stock")),
            "brand": Brand.JERUX.value if "jerux" in low else Brand.ABANGCOLEK.value if "colek" in low else Brand.UNKNOWN.value,
            "business_function": BusinessFunction.UNKNOWN.value,
            "sales_channel": SalesChannel.UNKNOWN.value,
            "exposes_production": any(x in low for x in ("filling","production","proses","prep")),
        }
        out=self._evaluate(text,question_set_version,q,metadata=metadata,fallback=fallback)
        if not self.force_fallback:
            a=out["answers"]; out["classified"]={
                "is_commercial":self._bool(a["is_commercial"]), "brand":a["brand"]["choice"],
                "business_function":a["business_function"]["choice"], "sales_channel":a["sales_channel"]["choice"],
                "exposes_production":self._bool(a["exposes_production"]),
            }
        return out

    def evaluate_interaction(self, text: str, question_set_version: str = "2.0.0", metadata=None):
        q={
            "customer_intent":Choice("What is the primary customer intent? Use UNKNOWN if this is not a customer message.",CustomerIntent.criteria()),
            "is_purchase_intent":Noul("Is purchase/order intent directly present?"),
            "is_location_query":Noul("Is a location/spot/stall query directly present?"),
            "is_complaint":Noul("Is dissatisfaction, defect, or service complaint directly present?"),
        }
        low=text.lower(); intent=CustomerIntent.COMPLAINT.value if any(x in low for x in ("bocor","rosak","tak puas")) else CustomerIntent.LOCATION_QUERY.value if any(x in low for x in ("kat mana","lokasi")) else CustomerIntent.UNKNOWN.value
        out=self._evaluate(text,question_set_version,q,metadata=metadata,fallback={"customer_intent":intent,"is_purchase_intent":False,"is_location_query":intent==CustomerIntent.LOCATION_QUERY.value,"is_complaint":intent==CustomerIntent.COMPLAINT.value})
        if not self.force_fallback:
            a=out["answers"]; out["classified"]={"customer_intent":a["customer_intent"]["choice"],"is_purchase_intent":self._bool(a["is_purchase_intent"]),"is_location_query":self._bool(a["is_location_query"]),"is_complaint":self._bool(a["is_complaint"])}
        return out

    def evaluate_complaint(self, text: str, question_set_version: str = "2.0.0", metadata=None, verified_evidence_attached=False):
        q={
            "is_complaint":Noul("Is this evidence directly a complaint or operational incident?"),
            "issue_class":Choice("What issue class is directly described? Use UNKNOWN when unsupported.",IssueClass.criteria()),
            "possible_process_stage":Choice("Which process stage is only a hypothesis for investigation? Use UNKNOWN rather than infer cause.",ProcessStage.criteria()),
            "requires_immediate_review":Noul("Does this evidence warrant immediate human review?"),
        }
        low=text.lower(); issue=IssueClass.LEAKAGE.value if any(x in low for x in ("bocor","leak")) else IssueClass.UNKNOWN.value
        out=self._evaluate(text,question_set_version,q,metadata=metadata,fallback={"is_complaint":issue!=IssueClass.UNKNOWN.value,"issue_class":issue,"possible_process_stage":ProcessStage.UNKNOWN.value,"requires_immediate_review":False})
        if not self.force_fallback:
            a=out["answers"]; out["classified"]={"is_complaint":self._bool(a["is_complaint"]),"issue_class":a["issue_class"]["choice"],"possible_process_stage":a["possible_process_stage"]["choice"],"requires_immediate_review":self._bool(a["requires_immediate_review"])}
        out["root_cause_status"]=RootCauseStatus.UNDETERMINED.value
        out["root_cause_rule_enforced"]=True
        return out

    def evaluate_business_signal(self, text: str, question_set_version: str = "2.0.0", metadata=None):
        q={
            "signal_new_variant":Noul("Does this evidence explicitly signal a new product or variant?"),
            "signal_new_territory":Noul("Does this evidence explicitly signal geographic expansion or a newly served territory?"),
            "signal_mobile_team":Noul("Does this evidence signal a mobile sales team, temporary stall, pop-up, or activation?"),
            "signal_recruitment":Noul("Does this evidence signal workforce, seller, reseller, stockist, or agent recruitment?"),
        }
        low=text.lower(); fallback={"signal_new_variant":any(x in low for x in ("produk baru","flava baru","new flavour")),"signal_new_territory":False,"signal_mobile_team":any(x in low for x in ("pacak","on ground","pop-up","popup")),"signal_recruitment":any(x in low for x in ("join","agent","ejen","part time","full time"))}
        out=self._evaluate(text,question_set_version,q,metadata=metadata,fallback=fallback)
        if not self.force_fallback:
            a=out["answers"]; out["classified"]={key:self._bool(a[key]) for key in q}
        return out

    def evaluate_bundle(self, text: str, question_set_version: str = "3.0.0", metadata=None):
        if self.force_fallback:
            raise JevUnavailableError("Bundled authoritative evaluation does not permit deterministic fallback")
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
        out=self._evaluate(text,question_set_version,q,metadata=metadata)
        a=out["answers"]
        out["classified"]={
            "is_commercial":self._bool(a["is_commercial"]), "brand":a["brand"]["choice"], "business_function":a["business_function"]["choice"],
            "sales_channel":a["sales_channel"]["choice"], "exposes_production":self._bool(a["exposes_production"]), "customer_intent":a["customer_intent"]["choice"],
            "is_purchase_intent":self._bool(a["is_purchase_intent"]), "is_location_query":self._bool(a["is_location_query"]), "is_complaint":self._bool(a["is_complaint"]),
            "issue_class":a["issue_class"]["choice"], "possible_process_stage":a["possible_process_stage"]["choice"], "requires_immediate_review":self._bool(a["requires_immediate_review"]),
            "signal_new_variant":self._bool(a["signal_new_variant"]), "signal_new_territory":self._bool(a["signal_new_territory"]), "signal_mobile_team":self._bool(a["signal_mobile_team"]),
            "signal_recruitment":self._bool(a["signal_recruitment"]),
        }
        out["root_cause_status"]=RootCauseStatus.UNDETERMINED.value
        out["root_cause_rule_enforced"]=True
        return out

    def evaluate_all(self, text: str, question_set_version: str = "2.0.0", metadata=None, verified_evidence_attached=False):
        return {"content":self.evaluate_content(text,question_set_version,metadata),"interaction":self.evaluate_interaction(text,question_set_version,metadata),"complaint":self.evaluate_complaint(text,question_set_version,metadata,verified_evidence_attached),"business_signal":self.evaluate_business_signal(text,question_set_version,metadata)}
