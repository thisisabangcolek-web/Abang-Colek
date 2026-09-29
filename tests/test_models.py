"""
Unit tests to validate all Pydantic v2 Canonical Models in D:\\ABANGCOLEK\\src\\models.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add D:\ABANGCOLEK to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import (
    SocialAccount,
    SocialPost,
    Comment,
    MediaAsset,
    MetricSnapshot,
    Evidence,
    ObservedFact,
    StructuredClassification,
    Inference,
    Hypothesis,
    Claim,
    HypothesisStatus,
    ProductBatch,
    ChainOfCustodyLeg,
    Incident,
    CAPA,
    QCStatus,
    RootCauseStatus,
    IssueClass,
    ProcessStage,
    JevDecision,
    JevTaxonomy,
    JevQuestionType,
)


def test_canonical_models():
    # SocialAccount
    account = SocialAccount(
        platform="tiktok",
        username="styloairpool",
        display_name="Abang Colek",
        bio="Jeruk Mangga No.1 Malaysia",
        followers=125000,
    )
    assert account.platform == "tiktok"
    assert account.account_id is not None
    assert account.followers == 125000

    # SocialPost
    post = SocialPost(
        platform="tiktok",
        post_id="post_123456789",
        account_id=account.account_id,
        published_at=datetime.now(timezone.utc),
        text="Stok baru dah sampai! Jangan lupa singgah booth kami.",
        permalink="https://tiktok.com/@styloairpool/video/123456789",
        media_types=["video"],
        hashtags=["#jeruk", "#abangcolek"],
        mentions=["@airpoolstylo"],
    )
    assert post.post_id == "post_123456789"
    assert len(post.hashtags) == 2

    # Comment
    comment = Comment(
        post_id=post.post_id,
        author_id="user_987",
        text="Bang, ada stock kat Shah Alam tak?",
        likes=12,
        is_creator_reply=False,
    )
    assert comment.comment_id is not None
    assert comment.likes == 12

    # MediaAsset
    media = MediaAsset(
        media_type="video",
        url="https://cdn.tiktok.com/v12345.mp4",
        transcript="Bismillah hari ini kita restock jeruk mangga asam boi 500 balang...",
        ocr_text="RESTOCK JERUK MANGGA",
        visual_description="Founder in black apron packing plastic jars into cool boxes",
    )
    assert media.asset_id is not None
    assert "restock" in media.transcript.lower()

    # MetricSnapshot
    metric = MetricSnapshot(
        target_id=post.post_id,
        views=45000,
        likes=3200,
        comments=180,
        shares=95,
        saves=410,
    )
    assert metric.views == 45000
    assert metric.captured_at is not None
    print("✅ Canonical models validated successfully.")


def test_epistemology_models():
    # Evidence
    evidence = Evidence(
        source_platform="threads",
        source_id="th_998877",
        raw_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
        content={"text": "ampun maaf dari saya, jangan marah2 team saya"},
        reliability=1.0,
    )
    assert evidence.evidence_id is not None
    assert evidence.reliability == 1.0

    # ObservedFact
    fact = ObservedFact(
        statement="Founder issued a public apology regarding team conduct.",
        evidence_ids=[evidence.evidence_id],
    )
    assert len(fact.evidence_ids) == 1

    # StructuredClassification
    classification = StructuredClassification(
        evidence_id=evidence.evidence_id,
        engine="jev",
        category="APOLOGY",
        confidence=0.98,
    )
    assert classification.engine == "jev"
    assert classification.confidence == 0.98

    # Inference
    inference = Inference(
        derived_from_fact_ids=[fact.fact_id],
        statement="Operational friction or customer dissatisfaction occurred during delivery.",
        confidence=0.85,
    )
    assert inference.confidence == 0.85

    # Hypothesis
    hypothesis = Hypothesis(
        statement="Issue originated during third-party transport to pop-up event.",
        status=HypothesisStatus.UNVERIFIED,
        candidate_stages=["TRANSPORT", "LAST_MILE_DELIVERY"],
    )
    assert hypothesis.status == HypothesisStatus.UNVERIFIED
    assert "TRANSPORT" in hypothesis.candidate_stages

    # Claim
    claim = Claim(
        text="Abang Colek produces 10,000 jars per day.",
        author_id="interviewer_1",
        evidence_id=evidence.evidence_id,
    )
    assert claim.claim_id is not None
    print("✅ Epistemology models validated successfully.")


def test_traceability_models():
    # ProductBatch
    batch = ProductBatch(
        product_name="Jerux Mangga Asam Boi",
        prep_date=datetime.now(timezone.utc),
        fruit_lot="LOT-MNG-20260920",
        packaging_lot="LOT-JAR-500ML-01",
        operator="Ahmad",
        qc_status=QCStatus.PASSED,
        total_units=1500,
    )
    assert batch.batch_id is not None
    assert batch.qc_status == QCStatus.PASSED

    # ChainOfCustodyLeg
    leg = ChainOfCustodyLeg(
        batch_id=batch.batch_id,
        transport_type="CHILLED_VAN",
        departure_time=datetime.now(timezone.utc),
        origin="Central Kitchen Klang",
        destination="Pop-up Booth Stadium Shah Alam",
        temp_celsius=4.5,
        received_good=1480,
        received_damaged=20,
    )
    assert leg.temp_celsius == 4.5
    assert leg.received_damaged == 20

    # Incident
    incident = Incident(
        product_name="Jerux Mangga Asam Boi",
        batch_id=batch.batch_id,
        location="Booth Stadium Shah Alam",
        issue_class=IssueClass.LEAKAGE,
        customer_complaint="Penutup balang terbuka sikit dan kuah asam meleleh dalam plastik.",
        root_cause_status=RootCauseStatus.UNDETERMINED,
        suspected_stages=["PACKAGING", "TRANSPORT"],
    )
    assert incident.root_cause_status == RootCauseStatus.UNDETERMINED
    assert incident.issue_class == IssueClass.LEAKAGE

    # CAPA
    capa = CAPA(
        incident_id=incident.incident_id,
        corrective_action="Replace damaged unit immediately with fresh sealed stock.",
        preventive_action="Implement induction heat-seal liner check on sealing station before dispatch.",
        verified_by="QA_Lead_Farid",
    )
    assert capa.capa_id is not None
    print("✅ Traceability models validated successfully.")


def test_jev_models():
    # JevDecision
    decision = JevDecision(
        evidence_id="ev_12345",
        question_name="is_customer_complaint",
        question_type=JevQuestionType.CHOICE,
        answer="YES",
        confidence=0.965,
        latency_ms=42.5,
    )
    assert decision.decision_id is not None
    assert decision.question_type == "choice"
    assert decision.confidence == 0.965

    # JevTaxonomy
    tax = JevTaxonomy.get_default_taxonomy()
    assert tax.version == "1.1.0"
    assert "ABANGCOLEK" in tax.categories["brand"]
    assert "PRODUCTION" in tax.categories["business_function"]
    assert "PURCHASE" in tax.categories["customer_intent"]
    assert "LEAKAGE" in tax.categories["issue_class"]
    print("✅ JEV models validated successfully.")


if __name__ == "__main__":
    test_canonical_models()
    test_epistemology_models()
    test_traceability_models()
    test_jev_models()
    print("\n🎉 ALL CANONICAL MODELS PASSED 100% EMPIRICAL VALIDATION!")
