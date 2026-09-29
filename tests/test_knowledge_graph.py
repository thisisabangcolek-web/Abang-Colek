import hashlib
import pytest
from src.collectors.base import BaseCollector
from src.knowledge.graph import KnowledgeGraph
from src.evidence.identity import ids_for_record
from src.media.pipeline import MediaProcessor


def make_real_record(tmp_path,source_id='ev1',published='2026-01-01T00:00:00+00:00'):
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='official_test')
    payload={'text':'Observed source content','data_origin':'OFFICIAL_API','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    return c.ingest(payload,platform='threads',source_id=source_id,source_type='post',source_url=f'https://example.test/{source_id}',published_at=published,access_method='OFFICIAL_API',capture_receipt={'http_status':200,'response_sha256':'c'*64},provenance_verified=True)


def register_one(kg,tmp_path,source_id='ev1'):
    rec=make_real_record(tmp_path,source_id); ids=kg.register_evidence(rec); return rec,ids['capture_id']


def test_media_with_no_local_file_stays_metadata_only(tmp_path):
    rec=make_real_record(tmp_path); asset=MediaProcessor(raw_dir=tmp_path/'raw',output_file=tmp_path/'media.json').extract_media_from_record(rec)[0]
    assert asset['media_status']=='MEDIA_NOT_AVAILABLE'
    assert asset['transcript'] is None and asset['ocr_text'] is None and asset['visual_description'] is None


def test_media_with_real_bytes_gets_hash_but_no_fabricated_analysis(tmp_path):
    media=tmp_path/'photo.jpg'; media.write_bytes(b'real-bytes-for-provenance'); media_hash=hashlib.sha256(media.read_bytes()).hexdigest()
    c=BaseCollector(storage_dir=tmp_path/'raw',collector_name='owner_test')
    payload={'text':'caption','local_media_path':str(media),'data_origin':'OWNER_EXPORT','evidence_class':'RAW_EVIDENCE','synthetic':False,'authoritative':True}
    rec=c.ingest(payload,platform='instagram',source_id='img1',source_type='post',source_url='https://example.test/img1',capture_receipt={'owner_export_sha256':media_hash},provenance_verified=True,access_method='OWNER_EXPORT',owner_export_file=str(media))
    asset=MediaProcessor().extract_media_from_record(rec)[0]
    assert asset['sha256_fingerprint']==media_hash
    assert asset['transcript'] is None and asset['ocr_text'] is None and asset['visual_description'] is None


def test_graph_relationship_requires_registered_evidence(tmp_path):
    kg=KnowledgeGraph(tmp_path/'g.db'); kg.add_entity('a','TEST','A'); kg.add_entity('b','TEST','B')
    with pytest.raises(ValueError): kg.add_relationship('a','b','RELATED',[])
    with pytest.raises(ValueError): kg.add_relationship('a','b','RELATED',['orphan'])
    _,cap=register_one(kg,tmp_path,'ev1'); assert kg.add_relationship('a','b','RELATED',[cap])['evidence_ids']==[cap]; kg.close()


def test_graph_fact_requires_registered_evidence_and_hypothesis_cannot_verify(tmp_path):
    kg=KnowledgeGraph(tmp_path/'g.db'); _,cap=register_one(kg,tmp_path,'ev1')
    with pytest.raises(ValueError): kg.add_epistemology_item('unsupported fact','OBSERVED_FACT',[],status='VERIFIED')
    with pytest.raises(ValueError): kg.add_epistemology_item('guess','HYPOTHESIS',[cap],status='VERIFIED')
    assert kg.add_epistemology_item('possible issue','HYPOTHESIS',[cap],confidence=.4,status='UNVERIFIED')['status']=='UNVERIFIED'; kg.close()


def test_build_graph_from_real_evidence_only(tmp_path):
    rec=make_real_record(tmp_path,'post123'); cap=ids_for_record(rec)['capture_id']
    kg=KnowledgeGraph(tmp_path/'g.db'); summary=kg.build_from_verified_evidence(tmp_path/'raw',tmp_path/'missing_decisions.json')
    assert summary['total_evidence']==1 and summary['total_entities']==2 and summary['total_relationships']==1 and summary['total_timeline_events']==1
    assert kg.query_provenance(cap)['total_references']>=1; kg.close()


def test_no_hardcoded_foundational_seed(tmp_path):
    kg=KnowledgeGraph(tmp_path/'g.db')
    with pytest.raises(RuntimeError): kg.populate_foundational_records()
    assert kg.get_summary()['total_entities']==0; kg.close()
