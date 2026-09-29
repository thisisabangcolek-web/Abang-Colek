"""Minimal TypeSafe AI JEV client with model discovery and explicit provenance metadata."""
from __future__ import annotations
import json, os, re, time, urllib.error, urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from src.config import PROJECT_ROOT

class Choice:
    def __init__(self,instructions:str,criteria:Dict[str,str]): self.instructions,self.criteria=instructions,criteria
    def to_dict(self): return {'type':'choice','instructions':self.instructions,'criteria':self.criteria}
class Score:
    def __init__(self,instructions:str,criteria:List[str]): self.instructions,self.criteria=instructions,criteria
    def to_dict(self): return {'type':'score','instructions':self.instructions,'criteria':self.criteria}
class Noul:
    def __init__(self,instructions:str): self.instructions=instructions
    def to_dict(self): return {'type':'noul','instructions':self.instructions}

def _load_local_env():
    for p in (PROJECT_ROOT/'.env', Path.home()/'.env'):
        if not p.exists():
            continue
        for line in p.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k,v=line.split('=',1)
            os.environ.setdefault(k.strip(),v.strip().strip('\"').strip("'"))


class TypeSafeJevClient:
    BASE='https://api.typesafe.ai/v1'
    DEFAULT_MODEL='jev-1.13.0'
    def __init__(self,api_key:Optional[str]=None,preferred_model:Optional[str]=None):
        _load_local_env(); self.api_key=api_key or os.getenv('TYPESAFE_API_KEY')
        if not self.api_key: raise ValueError('TYPESAFE_API_KEY is not configured')
        self.preferred_model=preferred_model or os.getenv('TYPESAFE_MODEL', self.DEFAULT_MODEL); self._resolved_model=None
    def _request(self,method:str,path:str,payload:Optional[Dict[str,Any]]=None,timeout:int=30)->Dict[str,Any]:
        body=None if payload is None else json.dumps(payload).encode('utf-8')
        req=urllib.request.Request(f'{self.BASE}{path}',data=body,method=method,headers={'Authorization':f'Bearer {self.api_key}','Content-Type':'application/json','User-Agent':'ABANGCOLEK-Forensic-Discovery/3.0'})
        last=None
        for attempt in range(1,4):
            try:
                with urllib.request.urlopen(req,timeout=timeout) as resp: return json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as exc:
                last=RuntimeError(f"TypeSafe HTTP {exc.code}: {exc.read().decode('utf-8',errors='replace')[:500]}")
                if exc.code not in {429,502,503,529} or attempt==3: raise last
            except Exception as exc:
                last=exc
                if attempt==3: raise
            time.sleep(min(2**attempt,8))
        raise RuntimeError('TypeSafe request failed') from last
    def get_models(self): return self._request('GET','/models')
    @staticmethod
    def _model_ids(obj:Any)->List[str]:
        ids=[]
        if isinstance(obj,str): return [obj] if 'jev' in obj.lower() else []
        if isinstance(obj,list):
            for x in obj: ids.extend(TypeSafeJevClient._model_ids(x))
        elif isinstance(obj,dict):
            for key in ('id','model','name'):
                v=obj.get(key)
                if isinstance(v,str) and 'jev' in v.lower(): ids.append(v)
            for v in obj.values():
                if isinstance(v,(dict,list)): ids.extend(TypeSafeJevClient._model_ids(v))
        return list(dict.fromkeys(ids))
    @staticmethod
    def _version_key(model_id:str):
        match=re.search(r'jev-(\d+)\.(\d+)\.(\d+)',model_id.lower())
        return tuple(int(x) for x in match.groups()) if match else (-1,-1,-1)
    def resolve_model(self)->str:
        if self._resolved_model: return self._resolved_model
        ids=self._model_ids(self.get_models())
        if self.preferred_model:
            if self.preferred_model in ids:
                self._resolved_model=self.preferred_model
            elif any(m in ('jev-latest','jev-preview') for m in ids) and self._version_key(self.preferred_model)!=(-1,-1,-1):
                self._resolved_model=self.preferred_model
            else:
                raise RuntimeError(f'Pinned TYPESAFE_MODEL {self.preferred_model!r} is not available; discovered={ids}')
        elif ids:
            concrete=[m for m in ids if self._version_key(m)!=(-1,-1,-1)]
            self._resolved_model=max(concrete,key=self._version_key) if concrete else (self.DEFAULT_MODEL if any(m in ('jev-latest','jev-preview') for m in ids) else ids[0])
        else: raise RuntimeError('GET /v1/models returned no discoverable JEV model IDs')
        return self._resolved_model
    def system_one(self,state:str,questions:Dict[str,Union[Choice,Score,Noul,Dict[str,Any]]],timeout:int=30)->Dict[str,Any]:
        formatted={k:(v.to_dict() if hasattr(v,'to_dict') else v) for k,v in questions.items()}; requested=self.resolve_model()
        result=self._request('POST','/systemone',{'model':requested,'state':state,'questions':formatted},timeout); result.setdefault('model_requested',requested); return result