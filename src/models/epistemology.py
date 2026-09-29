"""
D:\ABANGCOLEK\src\models\epistemology.py
Epistemological Layer Models:
Raw Evidence -> Observed Fact -> Structured Classification -> Inference -> Hypothesis -> Claim.
Strictly separates what is observed from what is inferred.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class HypothesisStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"


class Evidence(BaseModel):
    """
    Immutable raw evidence record captured from an external platform or import.
    """
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    evidence_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this evidence record"
    )
    source_platform: str = Field(..., description="Platform origin (tiktok, threads, instagram, etc.)")
    source_id: str = Field(..., description="Platform native ID for post, comment, or media")
    raw_hash: str = Field(..., description="Cryptographic SHA-256 hash of raw payload for integrity verification")
    content: Union[Dict[str, Any], str] = Field(..., description="Raw captured content payload or string")
    captured_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when evidence was ingested"
    )
    reliability: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Source reliability score between 0.0 (untrusted) and 1.0 (verified first-party)"
    )


class ObservedFact(BaseModel):
    """
    Empirically verified, indisputable assertion grounded directly in evidence.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    fact_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique fact identifier"
    )
    statement: str = Field(..., description="Defensible factual statement directly observed from evidence")
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of Evidence UUIDs directly supporting this fact"
    )
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this fact was verified"
    )


class StructuredClassification(BaseModel):
    """
    Machine-generated classification decision over evidence (e.g. via TypeSafe JEV or LLM).
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    classification_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique classification identifier"
    )
    evidence_id: str = Field(..., description="Associated Evidence UUID")
    engine: str = Field(..., description="Decision engine identifier (e.g., 'jev', 'gpt-4o', 'rule')")
    category: str = Field(..., description="Assigned taxonomy category or label")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Calibrated probability or confidence score"
    )


class Inference(BaseModel):
    """
    Analytical deduction derived by synthesizing one or more observed facts.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    inference_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique inference identifier"
    )
    derived_from_fact_ids: List[str] = Field(
        default_factory=list,
        description="Fact UUIDs from which this deduction was derived"
    )
    statement: str = Field(..., description="Inferred business pattern or deduction")
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence score for this inference (0.0 to 1.0)"
    )


class Hypothesis(BaseModel):
    """
    Tentative working explanation or suspect root cause requiring further empirical validation.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    hypothesis_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique hypothesis identifier"
    )
    statement: str = Field(..., description="Hypothetical statement or root cause conjecture")
    status: HypothesisStatus = Field(
        default=HypothesisStatus.UNVERIFIED,
        description="Current verification status (UNVERIFIED, SUPPORTED, REFUTED)"
    )
    candidate_stages: List[str] = Field(
        default_factory=list,
        description="Suspected process stages involved (e.g. TRANSPORT, PACKAGING, AGENT_STORAGE)"
    )


class Claim(BaseModel):
    """
    Assertion made by an external entity (e.g. founder statement, customer allegation)
    before or independent of objective factual verification.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    claim_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique claim identifier"
    )
    text: str = Field(..., description="The stated claim or assertion text")
    author_id: Optional[str] = Field(default=None, description="Identifier of the entity making the claim")
    evidence_id: Optional[str] = Field(default=None, description="Evidence record where claim was captured")
