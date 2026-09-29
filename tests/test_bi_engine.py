import json
from pathlib import Path
import pytest
from src.analytics.bi_engine import BusinessIntelligenceEngine
from src.collectors.base import BaseCollector
from src.jev.batch_runner import JevBatchRunner


def test_authoritative_batch_with_no_evidence_is_blocked_cleanly(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir(); norm=tmp_path/'norm'; out=tmp_path/'decisions.json'
    runner=JevBatchRunner(raw_dir=raw,normalized_dir=norm,output_file=out)
    result=runner.run_all()
    assert result['status']=='BLOCKED_NO_EVIDENCE'
    assert result['total_raw_processed']==0
    assert result['total_decisions']==0
    assert out.exists()


def test_bi_zero_evidence_never_invents_counts(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir(); norm=tmp_path/'norm'; norm.mkdir()
    coverage=tmp_path/'coverage.json'; coverage.write_text(json.dumps({'sources':[]}),encoding='utf-8')
    engine=BusinessIntelligenceEngine(raw_dir=raw,normalized_dir=norm,decisions_file=tmp_path/'missing.json',metrics_file=tmp_path/'metrics.json',coverage_file=coverage)
    result=engine.run_all(); counts=result['total_counts']
    assert counts['total_posts']==0
    assert counts['total_comments']==0
    assert counts['total_complaints']==0
    assert counts['total_inquiries']==0
    assert result['channel_breakdown']['channels']=={}
    assert result['complaint_clusters']['structured_customer_complaints']=={}
    assert result['complaint_clusters']['page_level_complaint_signals']=={}
    assert result['business_eras']==[]
    assert result['business_signals']['total_variants_cataloged']==0
    assert result['status']=='PARTIAL_EVIDENCE_ONLY'
    assert result['authoritative_for_prd'] is False


def test_bi_refuses_fallback_jev_decision(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir(); norm=tmp_path/'norm'; norm.mkdir()
    decision=tmp_path/'decisions.json'; decision.write_text(json.dumps({'decisions':[{'authoritative':False,'decision_engine':'RULE_FALLBACK'}]}),encoding='utf-8')
    engine=BusinessIntelligenceEngine(raw_dir=raw,normalized_dir=norm,decisions_file=decision,metrics_file=tmp_path/'m.json',coverage_file=tmp_path/'c.json')
    with pytest.raises(RuntimeError): engine.load_data()


def test_bi_does_not_read_legacy_or_synthetic_paths(tmp_path):
    engine=BusinessIntelligenceEngine(raw_dir=tmp_path/'raw',normalized_dir=tmp_path/'norm',decisions_file=tmp_path/'live.json',metrics_file=tmp_path/'m.json',coverage_file=tmp_path/'c.json')
    assert 'synthetic' not in str(engine.raw_dir).lower()
    assert 'jev_decisions.json' not in str(engine.decisions_file).lower()


def test_batch_classification_suppresses_repeated_capture_snapshots(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir()
    collector=BaseCollector(storage_dir=raw,collector_name='browser_test')
    common=dict(platform='instagram',source_id='post1',source_type='public_post_snapshot',source_url='https://example.test/post1',access_method='OFFICIAL_API',provenance_verified=True)
    p1={'text':'older capture','data_origin':'OFFICIAL_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    p2={'text':'newer capture','data_origin':'OFFICIAL_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    collector.ingest(p1,capture_receipt={'http_status':200,'response_sha256':'a'*64},**common)
    collector.ingest(p2,capture_receipt={'http_status':200,'response_sha256':'b'*64},**common)
    runner=JevBatchRunner(raw_dir=raw,normalized_dir=tmp_path/'norm',output_file=tmp_path/'out.json')
    records=runner.load_raw_sources()
    assert runner.total_raw_captures_loaded==2
    assert runner.duplicate_snapshots_suppressed==1
    assert len(records)==1
    assert records[0]['raw_payload']['text']=='newer capture'
