import hashlib, json
from pathlib import Path
import pytest
from pydantic import ValidationError

from src.analytics.bi_engine import BusinessIntelligenceEngine
from src.collectors.base import BaseCollector
from src.collectors.browser_public_adapter import PublicBrowserCollector
from src.collectors.coverage_tracker import CoverageTracker
from src.collectors.owner_export_importer import OwnerExportImporter
from src.evidence.identity import ids_for_record
from src.evidence.integrity import EvidenceIntegrityError, validate_raw_record
from src.jev.engine import JevEngine, JevInvalidResponseError
from src.jev.taxonomy import Brand, BusinessFunction, SalesChannel, CustomerIntent, IssueClass, ProcessStage
from src.jev.typesafe_client import TypeSafeJevClient
from src.models.canonical import Inference, MetricSnapshot, ProductBatch, QCStatus
from src.models.record_kind import RecordKind, canonical_record_kind
from src.runs.manager import ProcessingRun
def api_record(tmp_path,platform='threads',source_id='same',source_type='post',text='hello'):
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='api_fixture')
    payload={'text':text,'data_origin':'OFFICIAL_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    return c.ingest(payload,platform=platform,source_id=source_id,source_type=source_type,source_url=f'https://example.test/{platform}/{source_id}',access_method='OFFICIAL_API',capture_receipt={'http_status':200,'response_sha256':hashlib.sha256(text.encode()).hexdigest()},provenance_verified=True)


def test_ac01_payload_tamper_and_malformed_hash_are_rejected(tmp_path):
    rec=api_record(tmp_path,text='original'); validate_raw_record(rec,require_authoritative=True)
    bad=dict(rec); bad['raw_hash']='not-a-sha256'
    with pytest.raises(EvidenceIntegrityError): validate_raw_record(bad,require_authoritative=True)
    bad=json.loads(json.dumps(rec)); bad['raw_payload']['text']='tampered'
    with pytest.raises(EvidenceIntegrityError): validate_raw_record(bad,require_authoritative=True)


def test_ac01_browser_hash_requires_snapshot(tmp_path):
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='browser_fixture')
    payload={'visible_text':'x','data_origin':'PUBLIC_PLATFORM','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    with pytest.raises(EvidenceIntegrityError):
        c.ingest(payload,platform='instagram',source_id='p1',source_type='public_post_snapshot',source_url='https://example.test/p1',access_method='PUBLIC_BROWSER',capture_receipt={'http_status':200,'html_sha256':'a'*64},provenance_verified=True)
def test_ac02_platform_same_native_id_does_not_collide(tmp_path):
    a=api_record(tmp_path,platform='threads',source_id='profile_airpoolstylo',source_type='profile_snapshot',text='threads')
    b=api_record(tmp_path,platform='instagram',source_id='profile_airpoolstylo',source_type='profile_snapshot',text='instagram')
    ia,ib=ids_for_record(a),ids_for_record(b)
    assert ia['content_id']!=ib['content_id']
    assert ia['capture_id']!=ib['capture_id']
    assert ia['normalized_id']!=ib['normalized_id']


def test_ac03_record_kind_mapping_covers_current_collectors():
    assert canonical_record_kind('public_post_snapshot')==RecordKind.POST
    assert canonical_record_kind('public_video_metadata')==RecordKind.POST
    assert canonical_record_kind('public_photo_metadata')==RecordKind.POST
    assert canonical_record_kind('public_profile_snapshot')==RecordKind.PROFILE
    assert canonical_record_kind('owner_export_comment')==RecordKind.COMMENT
    assert canonical_record_kind('owner_export_reply')==RecordKind.REPLY


class EmptyAnswerClient:
    def resolve_model(self): return 'jev-1.13.0'
    def system_one(self,state,questions): return {'model':'jev-1.13.0','answers':{}}


def test_ac04_empty_jev_response_is_rejected(tmp_path):
    engine=JevEngine(cache_file=tmp_path/'cache.json',client=EmptyAnswerClient())
    with pytest.raises(JevInvalidResponseError): engine.evaluate_bundle('real evidence')
class ModelListClient(TypeSafeJevClient):
    def __init__(self): self.api_key='x'; self.preferred_model=None; self._resolved_model=None
    def get_models(self): return {'data':[{'id':'jev-1.9.0'},{'id':'jev-1.13.0'},{'id':'jev-preview'}]}


def test_ac12_model_selection_uses_semver_not_string_sort():
    assert ModelListClient().resolve_model()=='jev-1.13.0'


def test_ac11_all_choice_taxonomies_offer_every_enum_value():
    for enum in (Brand,BusinessFunction,SalesChannel,CustomerIntent,IssueClass,ProcessStage):
        assert set(enum.list_values())==set(enum.criteria())
        assert 'UNKNOWN' in enum.criteria()


def test_ac14_unknown_metrics_and_qc_defaults_are_not_false_facts():
    m=MetricSnapshot(target_id='x')
    assert m.views is None and m.likes is None and m.comments is None and m.shares is None
    assert ProductBatch(product_name='x').qc_status==QCStatus.PENDING
    with pytest.raises(ValidationError): Inference(statement='unsupported')
    assert Inference(statement='supported',fact_ids=['fact1']).fact_ids==['fact1']


def test_ac10_instagram_link_parser_accepts_canonical_handleless_paths():
    links=['https://www.instagram.com/p/ABC123/?utm_source=x','https://www.instagram.com/reel/XYZ999/']
    out=PublicBrowserCollector._extract_post_links('instagram',links,'@airpoolstylo')
    assert out==['https://www.instagram.com/p/ABC123','https://www.instagram.com/reel/XYZ999']
def test_ac07_owner_export_parse_success_does_not_claim_complete(tmp_path):
    export=tmp_path/'instagram_export.json'; export.write_text(json.dumps({'posts':[{'id':'1','caption':'hello'}]}),encoding='utf-8')
    tracker=CoverageTracker(output_path=tmp_path/'coverage.json')
    rows=OwnerExportImporter(storage_dir=tmp_path/'raw',coverage=tracker).import_json(export,'instagram')
    assert len(rows)>=1
    status=tracker.get_summary()['sources'][0]['status']
    assert status=='PARTIAL_UNKNOWN'
    empty=tmp_path/'empty.json'; empty.write_text('{}',encoding='utf-8')
    tracker2=CoverageTracker(output_path=tmp_path/'coverage2.json')
    assert OwnerExportImporter(storage_dir=tmp_path/'raw2',coverage=tracker2).import_json(empty,'instagram')==[]
    assert tracker2.get_summary()['sources'][0]['status']=='ERROR'


def test_ac08_failed_processing_run_does_not_replace_active_pointer(tmp_path):
    active=tmp_path/'active.json'; active.write_text(json.dumps({'run_id':'old'}),encoding='utf-8')
    run=ProcessingRun(runs_dir=tmp_path/'runs',active_file=active); run.fail('simulated')
    assert json.loads(active.read_text())['run_id']=='old'
    run2=ProcessingRun(runs_dir=tmp_path/'runs',active_file=active); run2.activate({'valid':True,'checks':{}})
    assert json.loads(active.read_text())['run_id']==run2.run_id


def test_ac09_unusable_challenge_capture_is_not_selected(tmp_path):
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='api_fixture')
    base={'data_origin':'OFFICIAL_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    c.ingest({**base,'text':'usable','usable_for_business_interpretation':True},platform='threads',source_id='x',source_type='post',source_url='https://example.test/x',access_method='OFFICIAL_API',capture_receipt={'http_status':200,'response_sha256':'a'*64},provenance_verified=True)
    c.ingest({**base,'text':'challenge','usable_for_business_interpretation':False,'capture_state':'BLOCKED_CHALLENGE'},platform='threads',source_id='x',source_type='post',source_url='https://example.test/x',access_method='OFFICIAL_API',capture_receipt={'http_status':200,'response_sha256':'b'*64},provenance_verified=True)
    from src.jev.batch_runner import JevBatchRunner
    selected=JevBatchRunner(raw_dir=tmp_path/'raw',normalized_dir=tmp_path/'norm',output_file=tmp_path/'out.json').load_raw_sources()
    assert len(selected)==1 and selected[0]['raw_payload']['text']=='usable'
def test_ac05_prd_gate_requires_human_workflow_not_all_collection_complete(tmp_path):
    norm=tmp_path/'norm'; norm.mkdir(); capture='cap_1'; normalized='norm_1'; raw_hash='f'*64
    (norm/'n.json').write_text(json.dumps({'normalized_id':normalized,'capture_id':capture,'content_id':'content_1','source_raw_hash':raw_hash,'platform':'threads','record_kind':'POST','authoritative':True,'synthetic':False,'capture_verified':True}),encoding='utf-8')
    decisions=tmp_path/'decisions.json'; decisions.write_text(json.dumps({'run_id':'r1','input_fingerprint':'i1','decisions':[{'decision_id':'d1','normalized_id':normalized,'capture_id':capture,'source_raw_hash':raw_hash,'source_platform':'threads','evaluation_type':'content','authoritative':True,'decision_engine':'TYPESAFE_JEV','classified':{'sales_channel':'UNKNOWN'}}]}),encoding='utf-8')
    coverage=tmp_path/'coverage.json'; coverage.write_text(json.dumps({'sources':[{'status':'PARTIAL_UNKNOWN'}]}),encoding='utf-8')
    workflow=tmp_path/'workflow.json'; approval=tmp_path/'approval.json'
    workflow.write_text(json.dumps({'workflows':[]}),encoding='utf-8'); approval.write_text(json.dumps({'approved':False}),encoding='utf-8')
    e=BusinessIntelligenceEngine(normalized_dir=norm,decisions_file=decisions,metrics_file=tmp_path/'m1.json',coverage_file=coverage,workflow_validation_file=workflow,prd_approval_file=approval)
    assert e.run_all()['authoritative_for_prd'] is False
    workflow.write_text(json.dumps({'workflows':[{'status':'VALIDATED','owner_or_team_validated':True}]}),encoding='utf-8')
    approval.write_text(json.dumps({'approved':True,'approved_by':'owner'}),encoding='utf-8')
    e=BusinessIntelligenceEngine(normalized_dir=norm,decisions_file=decisions,metrics_file=tmp_path/'m2.json',coverage_file=coverage,workflow_validation_file=workflow,prd_approval_file=approval)
    assert e.run_all()['authoritative_for_prd'] is True


def test_ac15_local_discovery_is_disabled_by_default(monkeypatch):
    from src.scripts.local_pc_discovery import main
    result=main(enabled=False)
    assert result['status']=='DISABLED' and result['count']==0
def test_ac06_legacy_windows_newline_capture_is_verifiable_without_rewrite(tmp_path):
    snap=tmp_path/'legacy.html'; snap.write_bytes(b'<p>a</p>\r\n<p>b</p>')
    legacy_text='<p>a</p>\n<p>b</p>'; legacy_hash=hashlib.sha256(legacy_text.encode()).hexdigest()
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='browser_legacy')
    payload={'visible_text':'a b','html_snapshot':str(snap),'data_origin':'PUBLIC_PLATFORM','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    rec=c.ingest(payload,platform='threads',source_id='legacy',source_type='public_post_snapshot',source_url='https://example.test/legacy',access_method='PUBLIC_BROWSER',capture_receipt={'http_status':200,'html_sha256':legacy_hash},provenance_verified=True)
    result=validate_raw_record(rec,require_authoritative=True)
    assert result['verification_mode']=='LEGACY_CANONICAL_TEXT_SHA256'
    assert snap.read_bytes()==b'<p>a</p>\r\n<p>b</p>'


def test_ac02_normalized_filename_is_safe_hash_id(tmp_path):
    rec=api_record(tmp_path,platform='threads',source_id='../profile:weird',source_type='profile_snapshot')
    ids=ids_for_record(rec)
    assert '/' not in ids['normalized_id'] and '\\' not in ids['normalized_id'] and '..' not in ids['normalized_id']
