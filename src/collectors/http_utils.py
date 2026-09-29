"""Small HTTP helper for official social APIs. Never logs or persists bearer tokens."""
from __future__ import annotations
import hashlib, json, os, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

def load_env_file(path:Path=Path('C:/Users/megat/.env'))->None:
    if not path.exists(): return
    for line in path.read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))

def request_json(method:str,url:str,*,token:Optional[str]=None,payload:Optional[Dict[str,Any]]=None,params:Optional[Dict[str,Any]]=None,timeout:int=30)->Tuple[Dict[str,Any],Dict[str,Any]]:
    if params:
        q=urllib.parse.urlencode({k:v for k,v in params.items() if v is not None}); url=f"{url}{'&' if '?' in url else '?'}{q}"
    body=None if payload is None else json.dumps(payload).encode('utf-8')
    headers={'Content-Type':'application/json','User-Agent':'ABANGCOLEK-Forensic-Collector/3.0'}
    if token: headers['Authorization']=f'Bearer {token}'
    last=None
    for attempt in range(1,5):
        req=urllib.request.Request(url,data=body,method=method.upper(),headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=timeout) as resp:
                raw=resp.read(); data=json.loads(raw.decode('utf-8'))
                receipt={'http_status':int(resp.status),'captured_at':datetime.now(timezone.utc).isoformat(),'response_sha256':hashlib.sha256(raw).hexdigest(),'request_url':url.split('access_token=')[0].rstrip('?&'),'request_id':resp.headers.get('x-fb-trace-id') or resp.headers.get('x-request-id')}
                return data,receipt
        except urllib.error.HTTPError as exc:
            raw=exc.read(); last=RuntimeError(f'HTTP {exc.code}: {raw.decode("utf-8",errors="replace")[:500]}')
            if exc.code not in {429,500,502,503,504,529} or attempt==4: raise last
            retry=exc.headers.get('Retry-After'); delay=float(retry) if retry and retry.replace('.','',1).isdigit() else min(2**attempt,16); time.sleep(delay)
        except Exception as exc:
            last=exc
            if attempt==4: raise
            time.sleep(min(2**attempt,16))
    raise RuntimeError('HTTP request failed') from last
