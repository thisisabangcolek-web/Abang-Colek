"""
D:\ABANGCOLEK\src\models\traceability.py
Traceability and Quality Assurance Models:
Batches, Chain of Custody Legs, Operational Incidents, and CAPA.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class QCStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class RootCauseStatus(str, Enum):
    UNDETERMINED = "UNDETERMINED"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED = "CONFIRMED"
    DISPROVED = "DISPROVED"


class IssueClass(str, Enum):
    PRODUCT_QUALITY = "PRODUCT_QUALITY"
    PACKAGING = "PACKAGING"
    LEAKAGE = "LEAKAGE"
    SEAL_FAILURE = "SEAL_FAILURE"
    FRESHNESS = "FRESHNESS"
    TASTE = "TASTE"
    APPEARANCE = "APPEARANCE"
    QUANTITY = "QUANTITY"
    WRONG_ITEM = "WRONG_ITEM"
    STOCKOUT = "STOCKOUT"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    DELIVERY_DAMAGE = "DELIVERY_DAMAGE"
    TRANSPORT = "TRANSPORT"
    STORAGE = "STORAGE"
    AGENT_HANDLING = "AGENT_HANDLING"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"
    PAYMENT = "PAYMENT"
    PRICE = "PRICE"
    LOCATION = "LOCATION"
    UNKNOWN = "UNKNOWN"


class ProcessStage(str, Enum):
    SUPPLIER = "SUPPLIER"
    RAW_MATERIAL_RECEIVING = "RAW_MATERIAL_RECEIVING"
    PRODUCTION = "PRODUCTION"
    FILLING = "FILLING"
    PACKAGING = "PACKAGING"
    QC = "QC"
    COLD_STORAGE = "COLD_STORAGE"
    WAREHOUSE = "WAREHOUSE"
    DISPATCH = "DISPATCH"
    TRANSPORT = "TRANSPORT"
    AGENT_RECEIVING = "AGENT_RECEIVING"
    AGENT_STORAGE = "AGENT_STORAGE"
    POINT_OF_SALE = "POINT_OF_SALE"
    LAST_MILE_DELIVERY = "LAST_MILE_DELIVERY"
    CUSTOMER_STORAGE = "CUSTOMER_STORAGE"
    UNKNOWN = "UNKNOWN"


class ProductBatch(BaseModel):
    """
    Represents an identifiable production batch of jeruk / colek fruit goods.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    batch_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique lot/batch tracking code"
    )
    product_name: str = Field(..., description="Product designation (e.g. 'Jerux Mangga Asam Boi')")
    prep_date: datetime = Field(..., description="Date/time when batch preparation was initiated")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiration date/time")
    fruit_lot: Optional[str] = Field(default=None, description="Raw fruit sourcing lot identifier")
    packaging_lot: Optional[str] = Field(default=None, description="Container/lid packaging lot number")
    operator: Optional[str] = Field(default=None, description="Lead preparation technician or operator")
    qc_status: Union[QCStatus, str] = Field(
        default=QCStatus.PENDING,
        description="Quality control release status"
    )
    total_units: int = Field(default=0, ge=0, description="Total units produced in this batch")


class ChainOfCustodyLeg(BaseModel):
    """
    Tracks cold chain / transportation movement of batch stock between nodes.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    leg_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique leg tracking ID"
    )
    batch_id: str = Field(..., description="Referenced ProductBatch ID")
    transport_type: str = Field(
        ...,
        description="Mode of transit (e.g. 'REFRIGERATED_VAN', 'MOTORCYCLE_DISPATCH', 'COLD_TRUCK')"
    )
    departure_time: datetime = Field(..., description="Timestamp when dispatch commenced")
    arrival_time: Optional[datetime] = Field(default=None, description="Timestamp of delivery/receipt")
    origin: str = Field(..., description="Departure facility / hub location")
    destination: str = Field(..., description="Arrival hub, agent, or retail spot")
    temp_celsius: Optional[float] = Field(
        default=None,
        description="Monitored temperature log in Celsius during transit"
    )
    received_good: int = Field(default=0, ge=0, description="Count of undamaged items successfully received")
    received_damaged: int = Field(default=0, ge=0, description="Count of damaged/leaked units recorded upon delivery")


class Incident(BaseModel):
    """
    Records an operational, packaging, cold-chain, or customer-reported anomaly.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    incident_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique incident log ID"
    )
    product_name: str = Field(..., description="Impacted product name")
    batch_id: Optional[str] = Field(default=None, description="Associated ProductBatch ID if traceable")
    report_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date and time when incident was reported"
    )
    location: Optional[str] = Field(default=None, description="Physical location or channel where fault occurred")
    issue_class: Union[IssueClass, str] = Field(
        ...,
        description="Taxonomy classification of issue (e.g., PACKAGING, LEAKAGE, FRESHNESS)"
    )
    customer_complaint: Optional[str] = Field(
        default=None,
        description="Raw or summarized customer feedback/complaint text"
    )
    root_cause_status: Union[RootCauseStatus, str] = Field(
        default=RootCauseStatus.UNDETERMINED,
        description="Current root-cause status (Defaults strictly to UNDETERMINED until proven)"
    )
    suspected_stages: List[str] = Field(
        default_factory=list,
        description="Hypothesized process stages under investigation (e.g. ['PACKAGING', 'TRANSPORT'])"
    )


class CAPA(BaseModel):
    """
    Corrective and Preventive Action executed in response to verified incidents.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    capa_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique CAPA record identifier"
    )
    incident_id: str = Field(..., description="Linked Incident ID")
    corrective_action: str = Field(..., description="Immediate remediative action taken to contain the issue")
    preventive_action: str = Field(..., description="Systemic modification implemented to prevent recurrence")
    verified_by: Optional[str] = Field(default=None, description="Auditor, QA lead, or manager sign-off")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
