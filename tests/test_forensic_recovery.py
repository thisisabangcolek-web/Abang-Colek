import json
from pathlib import Path
import pytest
from src.collectors.base import BaseCollector
from src.evidence.integrity import EvidenceIntegrityError, validate_raw_record
from src.media.pipeline import MediaProcessor
from src.jev.engine import JevEngine, JevUnavailableError
from src.jev.taxonomy import RootCauseStatus


def test_manual_authoritative_without_provenance_is_rejected(tmp_path):
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='test')
    payload={'text':'developer typed this','data_origin':'PUBLIC_PLATFORM','synthetic':False,'authoritative':True}
    with pytest.raises(EvidenceIntegrityError):
        c.ingest(payload,platform='threads',source_id='manual',source_type='post')


def test_synthetic_cannot_enter_production_raw(tmp_path):
    c=BaseCollector(storage_dir=BaseCollector.DEFAULT_STORAGE_DIR,collector_name='test')
    payload={'text':'fake','data_origin':'SYNTHETIC_TEST','synthetic':True,'authoritative':False}
    with pytest.raises(EvidenceIntegrityError):
        c.ingest(payload,platform='test',source_id='synthetic_guard_test',source_type='test')


def test_authoritative_capture_with_receipt_passes(tmp_path):
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='api_test')
    payload={'text':'real response text','data_origin':'OFFICIAL_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    rec=c.ingest(payload,platform='threads',source_id='123',source_type='post',source_url='https://example.test/post/123',access_method='OFFICIAL_API',capture_receipt={'http_status':200,'response_sha256':'a'*64},provenance_verified=True)
    validate_raw_record(rec,require_authoritative=True)
    assert rec['provenance_verified'] is True
    assert rec['raw_hash']


def test_media_without_bytes_generates_no_content(tmp_path):
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='api_test')
    payload={'text':'caption only','data_origin':'OFFICIAL_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    rec=c.ingest(payload,platform='threads',source_id='m1',source_type='post',source_url='https://example.test/m1',capture_receipt={'http_status':200,'response_sha256':'b'*64},provenance_verified=True,access_method='OFFICIAL_API')
    asset=MediaProcessor(raw_dir=tmp_path/'raw',output_file=tmp_path/'media.json').extract_media_from_record(rec)[0]
    assert asset['media_status']=='MEDIA_NOT_AVAILABLE'
    assert asset['transcript'] is None and asset['transcript_status']=='NOT_RUN'
    assert asset['ocr_text'] is None and asset['ocr_status']=='NOT_RUN'
    assert asset['visual_description'] is None
    assert asset['packaging_clues']==[]


def test_fallback_jev_is_explicitly_non_authoritative(tmp_path):
    e=JevEngine(cache_file=tmp_path/'cache.json',force_fallback=True)
    d=e.evaluate_interaction('kat mana lokasi?')
    assert d['decision_engine']=='RULE_FALLBACK'
    assert d['authoritative'] is False
    assert 'fallback' in d['model']


def test_authoritative_jev_fails_closed_when_client_unavailable(tmp_path):
    e=JevEngine(cache_file=tmp_path/'cache.json',force_fallback=False)
    e.client=None; e.client_error='simulated outage'
    with pytest.raises(JevUnavailableError): e.evaluate_content('test evidence')


def test_root_cause_never_auto_verifies(tmp_path):
    e=JevEngine(cache_file=tmp_path/'cache.json',force_fallback=True)
    d=e.evaluate_complaint('balang bocor semasa sampai',verified_evidence_attached=True)
    assert d['root_cause_status']==RootCauseStatus.UNDETERMINED.value
    assert d['root_cause_rule_enforced'] is True


def test_coverage_manifest_exists_and_is_not_falsely_complete():
    p=Path('D:/ABANGCOLEK/data/coverage/collection_manifest.json')
    assert p.exists()
    data=json.loads(p.read_text(encoding='utf-8'))
    assert data.get('sources')
    assert not all(x.get('status') in {'COMPLETE_VERIFIED','COMPLETE_WITHIN_API_SCOPE'} for x in data['sources'])
