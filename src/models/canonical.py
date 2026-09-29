"""
⚡ ABANGCOLEK Canonical Data Models
Implements Section 10 of CHAT5.md (Master Implementation Specification).
Provides Pydantic schemas with type enforcement, UUID generation, and JSON serialization.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator

from src.jev.taxonomy import (
    Brand,
    BusinessFunction,
    SalesChannel,
    CustomerIntent,
    IssueClass,
    ProcessStage,
    RootCauseStatus,
)


class StrEnum(str, Enum):
    """Base string enum for canonical models."""
    def __str__(self) -> str:
        return str(self.value)


class HypothesisStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class QCStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"


class JevQuestionType(StrEnum):
    CHOICE = "choice"
    SCORE = "score"
    NOUL = "noul"


class BaseCanonicalModel(BaseModel):
    """Base class for all canonical data models with common metadata."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SocialAccount(BaseCanonicalModel):
    """Social media account representation."""
    account_id: str = Field(default_factory=lambda: str(uuid4()))
    platform: str
    username: Optional[str] = None
    handle: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers: Optional[int] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    is_verified: Optional[bool] = None
    profile_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_handle_and_followers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "username" in data and "handle" not in data:
                data["handle"] = data["username"]
            elif "handle" in data and "username" not in data:
                data["username"] = data["handle"]
            if "followers" in data and "followers_count" not in data:
                data["followers_count"] = data["followers"]
            elif "followers_count" in data and "followers" not in data:
                data["followers"] = data["followers_count"]
        return data


class MediaAsset(BaseCanonicalModel):
    """Media item attached to posts or evidence."""
    asset_id: str = Field(default_factory=lambda: str(uuid4()))
    media_type: str  # video, image, audio
    url: Optional[str] = None
    transcript: Optional[str] = None
    ocr_text: Optional[str] = None
    visual_description: Optional[str] = None
    duration_seconds: Optional[float] = None
    view_count: Optional[int] = None
    audio_title: Optional[str] = None


class SocialPost(BaseCanonicalModel):
    """Canonical representation of a published post."""
    post_id: str = Field(default_factory=lambda: str(uuid4()))
    platform: str
    platform_post_id: Optional[str] = None
    account_id: Optional[str] = None
    author_handle: Optional[str] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    published_at: Optional[Union[datetime, str]] = None
    permalink: Optional[str] = None
    media_types: List[str] = Field(default_factory=list)
    media: List[MediaAsset] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    views_count: Optional[int] = None
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    shares_count: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def sync_text_and_post_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "post_id" in data and "platform_post_id" not in data:
                data["platform_post_id"] = data["post_id"]
            elif "platform_post_id" in data and "post_id" not in data:
                data["post_id"] = data["platform_post_id"]
            if "text" in data and "caption" not in data:
                data["caption"] = data["text"]
            elif "caption" in data and "text" not in data:
                data["text"] = data["caption"]
        return data


class Comment(BaseCanonicalModel):
    """User comment or reply on social media."""
    comment_id: str = Field(default_factory=lambda: str(uuid4()))
    platform: Optional[str] = None
    post_id: str
    author_id: Optional[str] = None
    author_handle: Optional[str] = None
    text: str
    published_at: Optional[str] = None
    likes: Optional[int] = None
    likes_count: Optional[int] = None
    is_reply: bool = False
    is_creator_reply: bool = False
    parent_comment_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_likes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "likes" in data and "likes_count" not in data:
                data["likes_count"] = data["likes"]
            elif "likes_count" in data and "likes" not in data:
                data["likes"] = data["likes_count"]
        return data


class MetricSnapshot(BaseCanonicalModel):
    """Engagement metrics snapshot at a point in time."""
    target_id: str
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Evidence(BaseCanonicalModel):
    """Raw or extracted evidence item."""
    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    source_platform: str
    source_id: str
    raw_hash: str
    content: Optional[Union[Dict[str, Any], str]] = None
    text_content: Optional[str] = None
    captured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reliability: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ObservedFact(BaseCanonicalModel):
    """Directly observed empirical fact derived from evidence."""
    fact_id: str = Field(default_factory=lambda: str(uuid4()))
    evidence_id: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    statement: str
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def sync_evidence_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "evidence_id" in data and data.get("evidence_id") and not data.get("evidence_ids"):
                data["evidence_ids"] = [data["evidence_id"]]
            elif data.get("evidence_ids") and not data.get("evidence_id"):
                data["evidence_id"] = data["evidence_ids"][0]
            if not data.get("evidence_ids"):
                raise ValueError("ObservedFact requires at least one evidence_id")
        return data


Fact = ObservedFact  # Alias for compatibility


class StructuredClassification(BaseCanonicalModel):
    """Structured classification output."""
    evidence_id: str
    engine: str = "jev"
    category: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class Inference(BaseCanonicalModel):
    """Logical deduction derived from observed facts."""
    derived_from_fact_ids: List[str] = Field(default_factory=list)
    fact_ids: List[str] = Field(default_factory=list)
    statement: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

    @model_validator(mode="before")
    @classmethod
    def sync_fact_ids(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("derived_from_fact_ids") and not data.get("fact_ids"):
                data["fact_ids"] = data["derived_from_fact_ids"]
            elif data.get("fact_ids") and not data.get("derived_from_fact_ids"):
                data["derived_from_fact_ids"] = data["fact_ids"]
            if not data.get("fact_ids"):
                raise ValueError("Inference requires at least one supporting fact_id")
        return data


class Hypothesis(BaseCanonicalModel):
    """Unverified assumption or working theory requiring operational validation."""
    statement: str
    status: Union[HypothesisStatus, str] = HypothesisStatus.UNVERIFIED
    candidate_stages: List[str] = Field(default_factory=list)
    inference_ids: List[str] = Field(default_factory=list)
    verification_evidence_ids: List[str] = Field(default_factory=list)


class Claim(BaseCanonicalModel):
    """Unverified external or marketing claim."""
    claim_id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    author_id: Optional[str] = None
    evidence_id: Optional[str] = None


class ProductBatch(BaseCanonicalModel):
    """Product batch tracking model."""
    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    product_name: str
    prep_date: Optional[Union[datetime, str]] = None
    fruit_lot: Optional[str] = None
    packaging_lot: Optional[str] = None
    operator: Optional[str] = None
    qc_status: QCStatus = QCStatus.PENDING
    total_units: Optional[int] = None


class ChainOfCustodyLeg(BaseCanonicalModel):
    """Tracking movement and temperature log across transit leg."""
    leg_id: str = Field(default_factory=lambda: str(uuid4()))
    batch_id: str
    transport_type: str
    departure_time: Optional[Union[datetime, str]] = None
    origin: str
    destination: str
    temp_celsius: Optional[float] = None
    received_good: Optional[int] = None
    received_damaged: Optional[int] = None


class Incident(BaseCanonicalModel):
    """Operational incident or complaint tracking."""
    incident_id: str = Field(default_factory=lambda: str(uuid4()))
    product_name: str
    batch_id: Optional[str] = None
    location: Optional[str] = None
    issue_class: IssueClass
    customer_complaint: Optional[str] = None
    root_cause_status: RootCauseStatus = RootCauseStatus.UNDETERMINED
    suspected_stages: List[str] = Field(default_factory=list)


class CAPA(BaseCanonicalModel):
    """Corrective and Preventive Action record."""
    capa_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    corrective_action: str
    preventive_action: str
    verified_by: Optional[str] = None


class JevAnswer(BaseModel):
    """Structured response from TypeSafe Jev System One."""
    question_name: str
    decision_type: str  # choice, score, noul
    value: Union[str, float, bool]
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    probabilities: Optional[Dict[str, float]] = None


class JevDecision(BaseCanonicalModel):
    """Set of Jev System One decisions on an evidence unit."""
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    evidence_id: str
    model: Optional[str] = None
    taxonomy_version: str = "1.1.0"
    question_set_version: str = "1.0.0"
    question_name: Optional[str] = None
    question_type: Optional[Union[str, JevQuestionType]] = None
    answer: Optional[Union[str, float, bool]] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    latency_ms: Optional[float] = None
    answers: List[JevAnswer] = Field(default_factory=list)
    root_cause_status: RootCauseStatus = RootCauseStatus.UNDETERMINED


class JevTaxonomy(BaseModel):
    """Taxonomy container model."""
    version: str = "1.1.0"
    categories: Dict[str, List[str]] = Field(default_factory=dict)

    @classmethod
    def get_default_taxonomy(cls) -> "JevTaxonomy":
        return cls(
            version="1.1.0",
            categories={
                "brand": Brand.list_values(),
                "business_function": BusinessFunction.list_values(),
                "sales_channel": SalesChannel.list_values(),
                "customer_intent": CustomerIntent.list_values(),
                "issue_class": IssueClass.list_values(),
                "process_stage": ProcessStage.list_values(),
            }
        )


class BusinessSignal(BaseCanonicalModel):
    """Structured operational signal recognized from evidence."""
    signal_type: str
    brand: Brand = Brand.UNKNOWN
    business_function: BusinessFunction = BusinessFunction.UNKNOWN
    sales_channel: SalesChannel = SalesChannel.UNKNOWN
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ComplaintSignal(BaseCanonicalModel):
    """
    Complaint or incident signal.
    Enforces RootCauseStatus.UNDETERMINED by default.
    """
    evidence_id: str
    issue_class: IssueClass = IssueClass.UNKNOWN
    possible_process_stage: ProcessStage = ProcessStage.UNKNOWN
    root_cause_status: RootCauseStatus = RootCauseStatus.UNDETERMINED
    founder_apology_detected: bool = False
    requires_investigation: bool = True
    operational_checkpoints_needed: List[str] = Field(default_factory=list)


class BrandEntity(BaseCanonicalModel):
    """Brand entity representation."""
    name: str
    canonical_brand: Brand
    first_observed: Optional[str] = None
    registration_status: Optional[str] = None


class ProductEntity(BaseCanonicalModel):
    """Product catalog entity."""
    brand: Brand
    name: str
    variant: Optional[str] = None
    price_myr: Optional[float] = None
    packaging_type: Optional[str] = None
    is_active: bool = True


class UnifiedEvidenceRecord(BaseCanonicalModel):
    """Comprehensive aggregated record uniting raw evidence, facts, and JEV decisions."""
    source_platform: str
    source_id: str
    raw_hash: str
    post: Optional[SocialPost] = None
    evidence: Optional[Evidence] = None
    facts: List[Fact] = Field(default_factory=list)
    inferences: List[Inference] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    jev_decisions: List[JevDecision] = Field(default_factory=list)
    signals: List[BusinessSignal] = Field(default_factory=list)
