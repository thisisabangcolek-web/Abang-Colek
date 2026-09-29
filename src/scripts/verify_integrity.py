"""Hard integrity gate for authoritative ABANGCOLEK discovery."""
from __future__ import annotations
import json, sys
from pathlib import Path
from src.evidence.integrity import validate_raw_record

ROOT=Path('D:/ABANGCOLEK')

def fail(msg):
    print(f'FAIL: {msg}'); return False

def main():
    ok=True; raw=list((ROOT/'data/raw').glob('*.json')) if (ROOT/'data/raw').exists() else []
    for f in raw:
        try: validate_raw_record(json.loads(f.read_text(encoding='utf-8')),require_authoritative=True)
        except Exception as exc: ok=fail(f'{f.name}: {exc}') and ok
    for rel in ['src/jev/batch_runner.py','src/analytics/bi_engine.py','src/media/pipeline.py']:
        text=(ROOT/rel).read_text(encoding='utf-8').replace('\\','/').lower()
        if 'data/synthetic' in text: ok=fail(f'{rel} reads synthetic production data') and ok
    media=ROOT/'data/media_processed_v3.json'
    if media.exists():
        for a in json.loads(media.read_text(encoding='utf-8')):
            if (a.get('transcript') or a.get('ocr_text') or a.get('visual_description')) and not a.get('sha256_fingerprint'):
                ok=fail(f"media {a.get('asset_id')} has derived content without media hash") and ok
    decisions=ROOT/'data/jev/live_decisions.json'
    if decisions.exists():
        d=json.loads(decisions.read_text(encoding='utf-8'))
        for x in d.get('decisions',[]):
            if x.get('authoritative') is not True or x.get('decision_engine')!='TYPESAFE_JEV' or 'fallback' in str(x.get('model','')).lower():
                ok=fail(f"non-live decision {x.get('decision_id')}") and ok
    manifest=ROOT/'data/coverage/collection_manifest.json'
    if not manifest.exists(): ok=fail('coverage manifest missing') and ok
    else:
        src=json.loads(manifest.read_text(encoding='utf-8')).get('sources',[])
        ready=bool(src) and all(x.get('status') in {'COMPLETE_VERIFIED','COMPLETE_WITHIN_API_SCOPE'} for x in src)
        print(f'COVERAGE_READY={ready}')
    print(f'RAW_AUTHORITATIVE_RECORDS={len(raw)}'); print('INTEGRITY_PASS' if ok else 'INTEGRITY_FAIL'); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
