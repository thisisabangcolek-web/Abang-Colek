"""Fail-closed TypeSafe JEV decision engine for authoritative business discovery."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Dict, List, Optional
from .taxonomy import TAXONOMY_VERSION, Brand, BusinessFunction, SalesChannel, CustomerIntent, IssueClass, ProcessStage, RootCauseStatus
from .typesafe_client import TypeSafeJevClient, Choice, Noul

class JevUnavailableError(RuntimeError):
    pass

class JevEngine:
    DEFAULT_CACHE_FILE = Path("D:/ABANGCOLEK/data/jev_cache_v3.json")
    def __init__(self, api_key: Optional[str]=None, cache_file: Optional[Path]=None,
                 force_fallback: bool=False, authoritative: bool=True):
        self.taxonomy_version = TAXONOMY_VERSION
        self.cache_file = Path(cache_file or self.DEFAULT_CACHE_FILE)
        self.force_fallback = bool(force_fallback)
        self.authoritative = bool(authoritative and not force_fallback)
        self.client = None; self.client_error = None; self._cache: Dict[str, Any] = {}
        if not self.force_fallback:
            try: self.client = TypeSafeJevClient(api_key=api_key)
            except Exception as exc: self.client_error = str(exc)
        self._load_cache()
    def _load_cache(self):
        if self.cache_file.exists():
            try: self._cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception: self._cache = {}
    def _save_cache(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp=self.cache_file.with_suffix(".tmp"); tmp.write_text(json.dumps(self._cache,indent=2,ensure_ascii=False),encoding="utf-8"); tmp.replace(self.cache_file)
    def compute_cache_key(self,text:str,version:str,keys:List[str])->str:
        eh=hashlib.sha256(text.strip().encode()).hexdigest(); mode="live" if self.authoritative else "fallback"
        return hashlib.sha256(f"{eh}:{self.taxonomy_version}:{version}:{','.join(sorted(keys))}:{mode}".encode()).hexdigest()
    def _cached(self,key):
        item=self._cache.get(key)
        if not isinstance(item,dict): return None
        if self.authoritative and (item.get("authoritative") is not True or item.get("decision_engine")!="TYPESAFE_JEV"): return None
        out=dict(item); out["cached"]=True; return out
    def _finish(self,key,out): self._cache[key]=out; self._save_cache(); return out
    def _live(self,text,questions,key,version):
        if self.client is None: raise JevUnavailableError(f"Live TypeSafe JEV unavailable: {self.client_error or 'client not initialized'}")
        try: raw=self.client.system_one(state=text,questions=questions)
        except Exception as exc: raise JevUnavailableError(f"Live TypeSafe JEV call failed: {exc}") from exc
        model=str(raw.get("model") or raw.get("model_requested") or "")
        if not model or "fallback" in model.lower(): raise JevUnavailableError(f"Invalid live model response: {model!r}")
        return {"cache_key":key,"model":model,"model_requested":raw.get("model_requested"),"model_resolved":model,
                "decision_engine":"TYPESAFE_JEV","authoritative":True,"taxonomy_version":self.taxonomy_version,
                "question_set_version":version,"cached":False,"answers":raw.get("answers",{}),"usage":raw.get("usage",{})}
    def _fallback(self,key,version,classified):
        return {"cache_key":key,"model":"jev-fallback-deterministic","model_requested":None,"model_resolved":None,
                "decision_engine":"RULE_FALLBACK","authoritative":False,"taxonomy_version":self.taxonomy_version,
                "question_set_version":version,"cached":False,"answers":{},"usage":{},"classified":classified}
    def evaluate_content(self,text:str,question_set_version="1.0.0",metadata=None):
        keys=["is_commercial","brand","business_function","sales_channel","exposes_production"]; ck=self.compute_cache_key(text,question_set_version,keys); c=self._cached(ck)
        if c: return c
        if self.force_fallback:
            low=text.lower(); out=self._fallback(ck,question_set_version,{"is_commercial":any(x in low for x in ("order","beli","harga","stok","stock")),"brand":Brand.JERUX.value if "jerux" in low else Brand.ABANGCOLEK.value if "colek" in low else Brand.UNKNOWN.value,"business_function":BusinessFunction.RECRUITMENT.value if any(x in low for x in ("join","kerja","part time","full time")) else BusinessFunction.UNKNOWN.value,"sales_channel":SalesChannel.AGENT.value if any(x in low for x in ("agent","ejen")) else SalesChannel.UNKNOWN.value,"exposes_production":any(x in low for x in ("filling","production","proses","prep"))}); return self._finish(ck,out)
        out=self._live(text,{"is_commercial":Noul("Is this commercial, marketing, or promotional business content?"),"brand":Choice("Which brand identity is primary?",Brand.criteria()),"business_function":Choice("What is the primary operational business function?",BusinessFunction.criteria()),"sales_channel":Choice("What sales or distribution channel is referenced?",SalesChannel.criteria()),"exposes_production":Noul("Does this content directly expose production or preparation activity?")},ck,question_set_version); a=out["answers"]; out["classified"]={"is_commercial":a.get("is_commercial",{}).get("noul",.5)>.5,"brand":a.get("brand",{}).get("choice",Brand.UNKNOWN.value),"business_function":a.get("business_function",{}).get("choice",BusinessFunction.UNKNOWN.value),"sales_channel":a.get("sales_channel",{}).get("choice",SalesChannel.UNKNOWN.value),"exposes_production":a.get("exposes_production",{}).get("noul",.5)>.5}; return self._finish(ck,out)
    def evaluate_interaction(self,text:str,question_set_version="1.0.0",metadata=None):
        keys=["customer_intent","is_purchase_intent","is_location_query","is_complaint"]; ck=self.compute_cache_key(text,question_set_version,keys); c=self._cached(ck)
        if c: return c
        if self.force_fallback:
            low=text.lower(); intent=CustomerIntent.COMPLAINT.value if any(x in low for x in ("bocor","rosak","tak puas")) else CustomerIntent.LOCATION_QUERY.value if any(x in low for x in ("kat mana","lokasi")) else CustomerIntent.PURCHASE.value if any(x in low for x in ("nak beli","nak order","order")) else CustomerIntent.UNKNOWN.value; out=self._fallback(ck,question_set_version,{"customer_intent":intent,"is_purchase_intent":intent==CustomerIntent.PURCHASE.value,"is_location_query":intent==CustomerIntent.LOCATION_QUERY.value,"is_complaint":intent==CustomerIntent.COMPLAINT.value}); return self._finish(ck,out)
        out=self._live(text,{"customer_intent":Choice("What is the primary customer intent?",CustomerIntent.criteria()),"is_purchase_intent":Noul("Is the user expressing intent to purchase or order?"),"is_location_query":Noul("Is the user asking for a location, stall address, or sales spot?"),"is_complaint":Noul("Is the user raising dissatisfaction, a defect, or a service complaint?")},ck,question_set_version); a=out["answers"]; out["classified"]={"customer_intent":a.get("customer_intent",{}).get("choice",CustomerIntent.UNKNOWN.value),"is_purchase_intent":a.get("is_purchase_intent",{}).get("noul",.5)>.5,"is_location_query":a.get("is_location_query",{}).get("noul",.5)>.5,"is_complaint":a.get("is_complaint",{}).get("noul",.5)>.5}; return self._finish(ck,out)
    def evaluate_complaint(self,text:str,question_set_version="1.0.0",metadata=None,verified_evidence_attached=False):
        keys=["is_complaint","issue_class","possible_process_stage","requires_immediate_review"]; ck=self.compute_cache_key(text,question_set_version,keys); c=self._cached(ck)
        if c: c["root_cause_status"]=RootCauseStatus.UNDETERMINED.value; return c
        if self.force_fallback:
            low=text.lower(); issue=IssueClass.LEAKAGE.value if any(x in low for x in ("bocor","leak")) else IssueClass.UNKNOWN.value; out=self._fallback(ck,question_set_version,{"is_complaint":issue!=IssueClass.UNKNOWN.value,"issue_class":issue,"possible_process_stage":ProcessStage.UNKNOWN.value,"requires_immediate_review":False}); out["root_cause_status"]=RootCauseStatus.UNDETERMINED.value; out["root_cause_rule_enforced"]=True; return self._finish(ck,out)
        out=self._live(text,{"is_complaint":Noul("Is this statement a customer complaint or operational incident?"),"issue_class":Choice("What class of issue is directly described?",IssueClass.criteria()),"possible_process_stage":Choice("Which process stage is only a hypothesis for investigation?",ProcessStage.criteria()),"requires_immediate_review":Noul("Does this evidence warrant immediate human review?")},ck,question_set_version); a=out["answers"]; out["classified"]={"is_complaint":a.get("is_complaint",{}).get("noul",.5)>.5,"issue_class":a.get("issue_class",{}).get("choice",IssueClass.UNKNOWN.value),"possible_process_stage":a.get("possible_process_stage",{}).get("choice",ProcessStage.UNKNOWN.value),"requires_immediate_review":a.get("requires_immediate_review",{}).get("noul",.5)>.5}; out["root_cause_status"]=RootCauseStatus.UNDETERMINED.value; out["root_cause_rule_enforced"]=True; return self._finish(ck,out)
    def evaluate_business_signal(self,text:str,question_set_version="1.0.0",metadata=None):
        keys=["signal_new_variant","signal_new_territory","signal_mobile_team","signal_recruitment"]; ck=self.compute_cache_key(text,question_set_version,keys); c=self._cached(ck)
        if c: return c
        if self.force_fallback:
            low=text.lower(); out=self._fallback(ck,question_set_version,{"signal_new_variant":any(x in low for x in ("produk baru","flava baru","new flavour")),"signal_new_territory":any(x in low for x in ("brunei","johor","selangor","shah alam")),"signal_mobile_team":any(x in low for x in ("pacak","on ground","pop-up","popup")),"signal_recruitment":any(x in low for x in ("join","agent","ejen","part time","full time"))}); return self._finish(ck,out)
        out=self._live(text,{"signal_new_variant":Noul("Does this evidence explicitly signal a new product or variant?"),"signal_new_territory":Noul("Does this evidence explicitly signal geographical expansion?"),"signal_mobile_team":Noul("Does this evidence signal a mobile sales team or temporary activation?"),"signal_recruitment":Noul("Does this evidence signal workforce or agent recruitment?")},ck,question_set_version); a=out["answers"]; out["classified"]={k:a.get(k,{}).get("noul",.5)>.5 for k in keys}; return self._finish(ck,out)
    def evaluate_bundle(self,text:str,question_set_version="2.0.0",metadata=None):
        keys=["is_commercial","brand","business_function","sales_channel","exposes_production","customer_intent","is_purchase_intent","is_location_query","is_complaint","issue_class","possible_process_stage","requires_immediate_review","signal_new_variant","signal_new_territory","signal_mobile_team","signal_recruitment"]
        ck=self.compute_cache_key(text,question_set_version,keys); c=self._cached(ck)
        if c: return c
        if self.force_fallback: raise JevUnavailableError("Bundled authoritative evaluation does not permit deterministic fallback")
        q={
            "is_commercial":Noul("Is this commercial, marketing, promotional, sales, recruitment, customer-service, or operational business content?"),
            "brand":Choice("Which brand identity is primary?",Brand.criteria()),
            "business_function":Choice("What is the primary operational business function?",BusinessFunction.criteria()),
            "sales_channel":Choice("What sales or distribution channel is referenced?",SalesChannel.criteria()),
            "exposes_production":Noul("Does this evidence directly expose production or preparation activity?"),
            "customer_intent":Choice("What is the primary customer intent visible in this evidence?",CustomerIntent.criteria()),
            "is_purchase_intent":Noul("Does this evidence contain purchase or order intent?"),
            "is_location_query":Noul("Does this evidence contain a request about a stall, store, spot, or location?"),
            "is_complaint":Noul("Does this evidence contain a customer complaint, dissatisfaction, defect, or service issue?"),
            "issue_class":Choice("If an issue is present, what class is directly described? Otherwise choose UNKNOWN.",IssueClass.criteria()),
            "possible_process_stage":Choice("If investigation is warranted, which process stage is only a hypothesis? Otherwise choose UNKNOWN.",ProcessStage.criteria()),
            "requires_immediate_review":Noul("Does this evidence warrant immediate human review?"),
            "signal_new_variant":Noul("Does this evidence explicitly signal a new product or variant?"),
            "signal_new_territory":Noul("Does this evidence explicitly signal geographical expansion?"),
            "signal_mobile_team":Noul("Does this evidence signal a mobile sales team, temporary stall, pop-up, or activation?"),
            "signal_recruitment":Noul("Does this evidence signal workforce, seller, reseller, stockist, or agent recruitment?")}
        out=self._live(text,q,ck,question_set_version); a=out["answers"]
        out["classified"]={
            "is_commercial":a.get("is_commercial",{}).get("noul",.5)>.5,
            "brand":a.get("brand",{}).get("choice",Brand.UNKNOWN.value),
            "business_function":a.get("business_function",{}).get("choice",BusinessFunction.UNKNOWN.value),
            "sales_channel":a.get("sales_channel",{}).get("choice",SalesChannel.UNKNOWN.value),
            "exposes_production":a.get("exposes_production",{}).get("noul",.5)>.5,
            "customer_intent":a.get("customer_intent",{}).get("choice",CustomerIntent.UNKNOWN.value),
            "is_purchase_intent":a.get("is_purchase_intent",{}).get("noul",.5)>.5,
            "is_location_query":a.get("is_location_query",{}).get("noul",.5)>.5,
            "is_complaint":a.get("is_complaint",{}).get("noul",.5)>.5,
            "issue_class":a.get("issue_class",{}).get("choice",IssueClass.UNKNOWN.value),
            "possible_process_stage":a.get("possible_process_stage",{}).get("choice",ProcessStage.UNKNOWN.value),
            "requires_immediate_review":a.get("requires_immediate_review",{}).get("noul",.5)>.5,
            "signal_new_variant":a.get("signal_new_variant",{}).get("noul",.5)>.5,
            "signal_new_territory":a.get("signal_new_territory",{}).get("noul",.5)>.5,
            "signal_mobile_team":a.get("signal_mobile_team",{}).get("noul",.5)>.5,
            "signal_recruitment":a.get("signal_recruitment",{}).get("noul",.5)>.5}
        out["root_cause_status"]=RootCauseStatus.UNDETERMINED.value; out["root_cause_rule_enforced"]=True
        return self._finish(ck,out)

    def evaluate_all(self,text:str,question_set_version="1.0.0",metadata=None,verified_evidence_attached=False):
        return {"content":self.evaluate_content(text,question_set_version,metadata),"interaction":self.evaluate_interaction(text,question_set_version,metadata),"complaint":self.evaluate_complaint(text,question_set_version,metadata,verified_evidence_attached),"business_signal":self.evaluate_business_signal(text,question_set_version,metadata)}