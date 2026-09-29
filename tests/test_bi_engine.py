import json
from pathlib import Path
import pytest
from src.analytics.bi_engine import BusinessIntelligenceEngine
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
    assert result['complaint_clusters']['issue_clusters']=={}
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
