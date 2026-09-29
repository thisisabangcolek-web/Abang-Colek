"""
D:\ABANGCOLEK\src\models\jev_types.py
TypeSafe AI System One / JEV Decision Engine Types.
High-speed typed micro-decisions and structured business taxonomy.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class JevQuestionType(str, Enum):
    CHOICE = "choice"
    SCORE = "score"
    NOUL = "noul"
    BOOL = "bool"


class JevDecision(BaseModel):
    """
    Represents an atomic, typed micro-decision produced by the TypeSafe JEV engine.
    """
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    decision_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique decision event identifier"
    )
    evidence_id: str = Field(..., description="ID of Evidence evaluated")
    question_name: str = Field(..., description="Specific question key (e.g., 'is_customer_complaint', 'content_type')")
    question_type: Union[JevQuestionType, str] = Field(
        ...,
        description="Type of question evaluation (choice, score, noul, bool)"
    )
    answer: Any = Field(..., description="The typed answer value (e.g. category string, numerical score, or boolean)")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calibrated probability or confidence score returned by JEV"
    )
    latency_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Execution latency in milliseconds"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when decision was produced"
    )


class JevTaxonomy(BaseModel):
    """
    Standardized, versioned hierarchical taxonomy for JEV classification.
    """
    model_config = ConfigDict(populate_by_name=True)

    version: str = Field(default="1.0.0", description="Taxonomy semantic version")
    categories: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "brand": [
                "ABANGCOLEK",
                "LIURLELEH",
                "JERUX",
                "MULTI_BRAND",
                "UNKNOWN",
            ],
            "business_function": [
                "PRODUCTION",
                "PROCUREMENT",
                "PACKAGING",
                "WAREHOUSING",
                "INVENTORY",
                "DISTRIBUTION",
                "TRANSPORT",
                "AGENT_MANAGEMENT",
                "DIRECT_SALES",
                "RETAIL",
                "POPUP",
                "EVENT",
                "CUSTOMER_SERVICE",
                "MARKETING",
                "CONTENT",
                "RECRUITMENT",
                "FINANCE",
                "COMPLIANCE",
                "OTHER",
                "UNKNOWN",
            ],
            "sales_channel": [
                "DIRECT",
                "SOCIAL_COMMERCE",
                "AGENT",
                "HOME_SELLER",
                "POPUP",
                "EVENT",
                "RETAIL",
                "DELIVERY",
                "COD",
                "ONLINE",
                "UNKNOWN",
            ],
            "customer_intent": [
                "PURCHASE",
                "PRICE_QUERY",
                "STOCK_QUERY",
                "LOCATION_QUERY",
                "DELIVERY_QUERY",
                "PRODUCT_QUERY",
                "CUSTOMIZATION",
                "AGENT_APPLICATION",
                "JOB_APPLICATION",
                "COMPLAINT",
                "REFUND",
                "RETURN",
                "PRAISE",
                "GENERAL_CHAT",
                "UNKNOWN",
            ],
            "issue_class": [
                "PRODUCT_QUALITY",
                "PACKAGING",
                "LEAKAGE",
                "SEAL_FAILURE",
                "FRESHNESS",
                "TASTE",
                "APPEARANCE",
                "QUANTITY",
                "WRONG_ITEM",
                "STOCKOUT",
                "DELIVERY_DELAY",
                "DELIVERY_DAMAGE",
                "TRANSPORT",
                "STORAGE",
                "AGENT_HANDLING",
                "CUSTOMER_SERVICE",
                "PAYMENT",
                "PRICE",
                "LOCATION",
                "UNKNOWN",
            ],
            "possible_process_stage": [
                "SUPPLIER",
                "RAW_MATERIAL_RECEIVING",
                "PRODUCTION",
                "FILLING",
                "PACKAGING",
                "QC",
                "COLD_STORAGE",
                "WAREHOUSE",
                "DISPATCH",
                "TRANSPORT",
                "AGENT_RECEIVING",
                "AGENT_STORAGE",
                "POINT_OF_SALE",
                "LAST_MILE_DELIVERY",
                "CUSTOMER_STORAGE",
                "UNKNOWN",
            ],
        },
        description="Dictionary mapping taxonomy domain names to valid enum strings"
    )

    @classmethod
    def get_default_taxonomy(cls) -> "JevTaxonomy":
        """Returns the canonical V1 taxonomy instance."""
        return cls(version="1.0.0")
