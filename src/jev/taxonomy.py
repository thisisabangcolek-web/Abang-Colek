"""
⚡ ABANGCOLEK JEV Business Taxonomy (Version 1.0.0)
Based on Section 13 of CHAT5.md (Master Implementation Specification).
Provides structured, versioned classification primitives for TypeSafe AI Jev System One.
"""

from enum import Enum
from typing import Dict, List, Any

TAXONOMY_VERSION: str = "1.0.0"


class StrEnum(str, Enum):
    """String Enum base class with helper conversion methods."""
    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def list_values(cls) -> List[str]:
        return [item.value for item in cls]

    @classmethod
    def has_value(cls, val: str) -> bool:
        return val in cls.list_values()


class Brand(StrEnum):
    """Brand identity classification."""
    ABANGCOLEK = "ABANGCOLEK"
    LIURLELEH = "LIURLELEH"
    JERUX = "JERUX"
    MULTI_BRAND = "MULTI_BRAND"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def criteria(cls) -> Dict[str, str]:
        return {
            cls.ABANGCOLEK.value: "Abang Colek fresh fruit and dipping sauce brand, experiential events, live stalls",
            cls.LIURLELEH.value: "Liur Leleh House legacy preserved fruit / jeruk brand and parent identity",
            cls.JERUX.value: "The Famous Jerux bottled and packaged fruit pickle brand",
            cls.MULTI_BRAND.value: "Multiple co-existing brands from the ecosystem mentioned together",
            cls.UNKNOWN.value: "No recognizable brand entity identified in evidence",
        }


class BusinessFunction(StrEnum):
    """Operational business function classification."""
    PRODUCTION = "PRODUCTION"
    PROCUREMENT = "PROCUREMENT"
    PACKAGING = "PACKAGING"
    WAREHOUSING = "WAREHOUSING"
    INVENTORY = "INVENTORY"
    DISTRIBUTION = "DISTRIBUTION"
    TRANSPORT = "TRANSPORT"
    AGENT_MANAGEMENT = "AGENT_MANAGEMENT"
    DIRECT_SALES = "DIRECT_SALES"
    RETAIL = "RETAIL"
    POPUP = "POPUP"
    EVENT = "EVENT"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"
    MARKETING = "MARKETING"
    CONTENT = "CONTENT"
    RECRUITMENT = "RECRUITMENT"
    FINANCE = "FINANCE"
    COMPLIANCE = "COMPLIANCE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def criteria(cls) -> Dict[str, str]:
        return {
            cls.PRODUCTION.value: "Fruit preparation, cutting, marinating, pickling, sauce mixing",
            cls.PROCUREMENT.value: "Raw fruit sourcing, supplier purchase, packaging materials ordering",
            cls.PACKAGING.value: "Jar filling, sealing, lid capping, labeling, outer box packing",
            cls.INVENTORY.value: "Stock holding, batch tracking, stock counts, expiry management",
            cls.DISTRIBUTION.value: "Wholesale allocation, stock dispatch to agents or retail partners",
            cls.TRANSPORT.value: "Transit logistics, vehicle transit, courier delivery, long-distance bus or runner",
            cls.AGENT_MANAGEMENT.value: "Recruiting, onboarding, restocking, or managing agents and home sellers",
            cls.DIRECT_SALES.value: "Selling directly to end customers via booth, WhatsApp, or COD",
            cls.EVENT.value: "Exhibitions, festivals, carnivals, cross-border expos (e.g. Brunei)",
            cls.POPUP.value: "Temporary roadside or mall activation spot",
            cls.CUSTOMER_SERVICE.value: "Answering customer inquiries, resolving complaints, providing directions",
            cls.MARKETING.value: "Promotions, price discounts, advertising campaigns",
            cls.RECRUITMENT.value: "Hiring stall crew, event staff, full-time/part-time workers, or agents",
            cls.FINANCE.value: "Cash reconciliation, POS settlement, pricing, revenue, expense tracking",
            cls.COMPLIANCE.value: "Halal, trademark registration (Warta Kerajaan), SSM, food safety hygiene",
        }


class SalesChannel(StrEnum):
    """Sales and distribution channel classification."""
    DIRECT = "DIRECT"
    SOCIAL_COMMERCE = "SOCIAL_COMMERCE"
    AGENT = "AGENT"
    HOME_SELLER = "HOME_SELLER"
    POPUP = "POPUP"
    EVENT = "EVENT"
    RETAIL = "RETAIL"
    DELIVERY = "DELIVERY"
    COD = "COD"
    ONLINE = "ONLINE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def criteria(cls) -> Dict[str, str]:
        return {
            cls.DIRECT.value: "Direct purchase from official stall, physical store, or HQ",
            cls.SOCIAL_COMMERCE.value: "Order via TikTok Shop, Threads DM, Instagram DM, Facebook",
            cls.AGENT.value: "Purchase through authorized regional agent or stockist",
            cls.HOME_SELLER.value: "Part-time home-based distributor or local neighborhood reseller",
            cls.POPUP.value: "Temporary roadside, car boot, or pop-up stand",
            cls.EVENT.value: "Trade fair, food carnival, consumer exhibition",
            cls.RETAIL.value: "Third-party grocery, convenience store, or food delivery listing (e.g. Foodpanda)",
            cls.DELIVERY.value: "Delivery via runner or express courier service",
            cls.COD.value: "Cash On Delivery arranged directly with customer",
            cls.UNKNOWN.value: "Sales channel not mentioned or indeterminable",
        }


class CustomerIntent(StrEnum):
    """Customer interaction and intent classification."""
    PURCHASE = "PURCHASE"
    PRICE_QUERY = "PRICE_QUERY"
    STOCK_QUERY = "STOCK_QUERY"
    LOCATION_QUERY = "LOCATION_QUERY"
    DELIVERY_QUERY = "DELIVERY_QUERY"
    PRODUCT_QUERY = "PRODUCT_QUERY"
    CUSTOMIZATION = "CUSTOMIZATION"
    AGENT_APPLICATION = "AGENT_APPLICATION"
    JOB_APPLICATION = "JOB_APPLICATION"
    COMPLAINT = "COMPLAINT"
    REFUND = "REFUND"
    RETURN = "RETURN"
    PRAISE = "PRAISE"
    GENERAL_CHAT = "GENERAL_CHAT"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def criteria(cls) -> Dict[str, str]:
        return {
            cls.PURCHASE.value: "Intent to buy, place an order, or craving expressed with buying intent",
            cls.PRICE_QUERY.value: "Asking how much an item or jar costs ('berapa sebalang?')",
            cls.STOCK_QUERY.value: "Asking if a variant or item is still available / in stock",
            cls.LOCATION_QUERY.value: "Asking where the stall, booth, or agent is located ('kat mana pacak?')",
            cls.DELIVERY_QUERY.value: "Asking about shipping, courier, COD, or runner delivery options",
            cls.AGENT_APPLICATION.value: "Expressing interest in becoming a reseller, agent, or home seller",
            cls.JOB_APPLICATION.value: "Inquiring about crew, stall staff, or factory job openings",
            cls.COMPLAINT.value: "Expressing dissatisfaction, defect, spoilage, or service issue",
            cls.REFUND.value: "Demanding money back, compensation, or replacement item",
            cls.PRAISE.value: "Complimenting the taste, quality, speed, or service ('sedap giler')",
            cls.UNKNOWN.value: "No clear customer intent detected",
        }


class IssueClass(StrEnum):
    """Classification of operational, product, or customer issues."""
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

    @classmethod
    def criteria(cls) -> Dict[str, str]:
        return {
            cls.PRODUCT_QUALITY.value: "General product condition or manufacturing defect",
            cls.PACKAGING.value: "Defective container, lid, cap, or label",
            cls.LEAKAGE.value: "Pickle juice, brine, or sauce leaking from container",
            cls.SEAL_FAILURE.value: "Seal broken, loose lid, unsealed or pressurized jar opening",
            cls.FRESHNESS.value: "Fruit stale, fermenting prematurely, soft texture, or rotten",
            cls.TASTE.value: "Taste off, too sour, lacking seasoning, or altered flavor profile",
            cls.DELIVERY_DAMAGE.value: "Crushed, dropped, or broken packaging during transit",
            cls.TRANSPORT.value: "Temperature abuse, excessive vibration, or transit delays",
            cls.STORAGE.value: "Improper temperature or holding environment before sale",
            cls.AGENT_HANDLING.value: "Improper handling, slow turnover, or poor storage by agent",
            cls.UNKNOWN.value: "Issue class not identifiable from evidence",
        }


class ProcessStage(StrEnum):
    """
    Possible business process stage where an issue or signal originates.
    CRITICAL: Process stage is a classification hypothesis and must NEVER
    be treated as a proven root cause without direct verifiable operational evidence.
    """
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
    POS = "POS"
    POINT_OF_SALE = "POINT_OF_SALE"
    LAST_MILE = "LAST_MILE"
    LAST_MILE_DELIVERY = "LAST_MILE_DELIVERY"
    CUSTOMER_STORAGE = "CUSTOMER_STORAGE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def criteria(cls) -> Dict[str, str]:
        return {
            cls.SUPPLIER.value: "Raw fruit quality, farm ripeness, chemical residue",
            cls.PRODUCTION.value: "Peeling, cutting, marinating, brine formulation",
            cls.FILLING.value: "Filling jar to brim, headspace variation, juice level",
            cls.PACKAGING.value: "Capping, induction sealing, lid tightening, labeling",
            cls.QC.value: "Quality control inspection, fill level check, seal check",
            cls.COLD_STORAGE.value: "Chilled storage before dispatch, holding temperature",
            cls.DISPATCH.value: "Palletizing, sorting, staging for transit",
            cls.TRANSPORT.value: "Transit via vehicle, courier van, or bus cargo bay",
            cls.AGENT_RECEIVING.value: "Agent intake, inspection, and verification",
            cls.AGENT_STORAGE.value: "Agent home/shop storage condition and temperature",
            cls.POS.value: "Stall, booth, or point of sale handling",
            cls.LAST_MILE.value: "Final runner, dispatch, or hand-off to consumer",
            cls.UNKNOWN.value: "Stage cannot be determined from available evidence",
        }


class RootCauseStatus(StrEnum):
    """
    Root Cause Verification Status.
    Safety Invariant: Any complaint or issue root cause MUST default to UNDETERMINED
    until rigorous physical/logistical evidence confirms the fault path.
    """
    UNDETERMINED = "UNDETERMINED"
    HYPOTHESIS = "HYPOTHESIS"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


def get_taxonomy_summary() -> Dict[str, Any]:
    """Returns metadata and value lists for the taxonomy version."""
    return {
        "version": TAXONOMY_VERSION,
        "brands": Brand.list_values(),
        "business_functions": BusinessFunction.list_values(),
        "sales_channels": SalesChannel.list_values(),
        "customer_intents": CustomerIntent.list_values(),
        "issue_classes": IssueClass.list_values(),
        "process_stages": ProcessStage.list_values(),
        "root_cause_statuses": RootCauseStatus.list_values(),
    }
