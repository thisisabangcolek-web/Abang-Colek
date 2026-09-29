import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from src.collectors.base import BaseCollector
from src.evidence.integrity import EvidenceIntegrityError
from src.jev.engine import JevEngine
from src.jev.taxonomy import TAXONOMY_VERSION, Brand, BusinessFunction, SalesChannel, CustomerIntent, IssueClass, ProcessStage, RootCauseStatus, get_taxonomy_summary
from src.models.canonical import SocialAccount, Inference, ComplaintSignal, ProductEntity


def test_canonical_models_still_validate():
    a=SocialAccount(platform='threads',handle='@example',display_name='Example')
    assert a.handle=='@example'
    assert Inference(statement='possible',fact_ids=['fact1'],confidence=.5).confidence==.5
    with pytest.raises(ValidationError): Inference(statement='bad',fact_ids=['fact1'],confidence=1.5)
    s=ComplaintSignal(evidence_id='ev1',issue_class=IssueClass.LEAKAGE,possible_process_stage=ProcessStage.UNKNOWN)
    assert s.root_cause_status==RootCauseStatus.UNDETERMINED
    p=ProductEntity(brand=Brand.JERUX,name='Test Product'); assert p.brand==Brand.JERUX


def test_taxonomy_core_is_present():
    assert TAXONOMY_VERSION=='1.1.0'
    assert {'ABANGCOLEK','LIURLELEH','JERUX','UNKNOWN'}.issubset(set(Brand.list_values()))
    assert {'PRODUCTION','PACKAGING','TRANSPORT','CUSTOMER_SERVICE'}.issubset(set(BusinessFunction.list_values()))
    assert {'DIRECT','AGENT','EVENT','SOCIAL_COMMERCE'}.issubset(set(SalesChannel.list_values()))
    assert {'COMPLAINT','LOCATION_QUERY','PURCHASE'}.issubset(set(CustomerIntent.list_values()))
    assert get_taxonomy_summary()['version']==TAXONOMY_VERSION


def test_fallback_cache_is_non_authoritative_and_reused(tmp_path):
    e=JevEngine(cache_file=tmp_path/'cache.json',force_fallback=True)
    first=e.evaluate_content('proses filling hari ini')
    second=e.evaluate_content('proses filling hari ini')
    assert first['authoritative'] is False and first['decision_engine']=='RULE_FALLBACK'
    assert second['cached'] is True and second['cache_key']==first['cache_key']
    assert (tmp_path/'cache.json').exists()


def test_root_cause_stays_undetermined_even_if_caller_claims_verified(tmp_path):
    e=JevEngine(cache_file=tmp_path/'cache.json',force_fallback=True)
    r=e.evaluate_complaint('balang bocor teruk',verified_evidence_attached=True)
    assert r['root_cause_status']==RootCauseStatus.UNDETERMINED.value
    assert r['root_cause_rule_enforced'] is True


def test_collector_hash_integrity_and_idempotence(tmp_path):
    c=BaseCollector(storage_dir=tmp_path/'raw')
    payload={'data':'non-authoritative test record'}
    r1=c.ingest(payload,platform='test',source_id='1'); r2=c.ingest(payload,platform='test',source_id='1')
    assert r1['raw_hash']==r2['raw_hash']
    assert c.verify_integrity(r1['filepath']) is True
    p=Path(r1['filepath']); data=json.loads(p.read_text(encoding='utf-8')); data['raw_payload']['data']='tampered'; p.write_text(json.dumps(data),encoding='utf-8')
    assert c.verify_integrity(p) is False


def test_collector_cannot_turn_handwritten_record_authoritative(tmp_path):
    c=BaseCollector(storage_dir=tmp_path/'raw')
    payload={'text':'invented','data_origin':'PUBLIC_PLATFORM','authoritative':True,'synthetic':False}
    with pytest.raises(EvidenceIntegrityError): c.ingest(payload,platform='threads',source_id='fake')


def test_mock_loader_is_not_a_production_dependency():
    source=Path('D:/ABANGCOLEK/src/collectors/mock_loader.py').read_text(encoding='utf-8')
    assert 'MockLoader' in source
    for production_file in ['src/jev/batch_runner.py','src/analytics/bi_engine.py','src/media/pipeline.py']:
        text=Path('D:/ABANGCOLEK') .joinpath(production_file).read_text(encoding='utf-8')
        assert 'mock_loader' not in text.lower()
        assert 'data/synthetic' not in text.replace('\\','/').lower()