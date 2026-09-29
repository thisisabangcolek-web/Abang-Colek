"""Neutral, abstention-capable JEV taxonomy for ABANGCOLEK discovery."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List

TAXONOMY_VERSION = "1.1.0"


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

    @classmethod
    def list_values(cls) -> List[str]:
        return [item.value for item in cls]

    @classmethod
    def has_value(cls, val: str) -> bool:
        return val in cls.list_values()

    @classmethod
    def _complete(cls, descriptions: Dict[str, str]) -> Dict[str, str]:
        missing = set(cls.list_values()) - set(descriptions)
        if missing:
            raise RuntimeError(f"Incomplete criteria for {cls.__name__}: {sorted(missing)}")
        return descriptions


class Brand(StrEnum):
    ABANGCOLEK="ABANGCOLEK"; LIURLELEH="LIURLELEH"; JERUX="JERUX"; MULTI_BRAND="MULTI_BRAND"; UNKNOWN="UNKNOWN"

    @classmethod
    def criteria(cls):
        return cls._complete({
            "ABANGCOLEK":"Evidence explicitly names or clearly displays ABANGCOLEK / Abang Colek.",
            "LIURLELEH":"Evidence explicitly names or clearly displays LIURLELEH / Liur Leleh House; no ownership relationship is implied.",
            "JERUX":"Evidence explicitly names or clearly displays JERUX / The Famous Jerux; no ownership relationship is implied.",
            "MULTI_BRAND":"Two or more listed brand identities are explicitly present in the same evidence.",
            "UNKNOWN":"No listed brand can be identified reliably from the evidence.",
        })


class BusinessFunction(StrEnum):
    PRODUCTION="PRODUCTION"; PROCUREMENT="PROCUREMENT"; PACKAGING="PACKAGING"; WAREHOUSING="WAREHOUSING"; INVENTORY="INVENTORY"
    DISTRIBUTION="DISTRIBUTION"; TRANSPORT="TRANSPORT"; AGENT_MANAGEMENT="AGENT_MANAGEMENT"; DIRECT_SALES="DIRECT_SALES"; RETAIL="RETAIL"
    POPUP="POPUP"; EVENT="EVENT"; CUSTOMER_SERVICE="CUSTOMER_SERVICE"; MARKETING="MARKETING"; CONTENT="CONTENT"; RECRUITMENT="RECRUITMENT"
    FINANCE="FINANCE"; COMPLIANCE="COMPLIANCE"; OTHER="OTHER"; UNKNOWN="UNKNOWN"

    @classmethod
    def criteria(cls):
        return cls._complete({
            "PRODUCTION":"Preparing, processing, mixing, cutting, marinating or making product.", "PROCUREMENT":"Sourcing or purchasing raw materials/supplies.",
            "PACKAGING":"Filling, sealing, labeling or packing product.", "WAREHOUSING":"Holding or organizing stock in a storage facility.",
            "INVENTORY":"Counting, tracking, allocating, expiring or reconciling stock.", "DISTRIBUTION":"Allocating or dispatching stock to sellers/locations.",
            "TRANSPORT":"Movement of goods between locations by any transport mode explicitly evidenced.", "AGENT_MANAGEMENT":"Recruiting, onboarding, supporting or restocking agents/resellers.",
            "DIRECT_SALES":"Direct selling activity to end customers.", "RETAIL":"Third-party or permanent retail placement/sales.",
            "POPUP":"Temporary physical selling activation or spot.", "EVENT":"Festival, expo, fair, carnival or event participation.",
            "CUSTOMER_SERVICE":"Answering customer questions or resolving customer issues.", "MARKETING":"Promotion, advertising, campaign or offer communication.",
            "CONTENT":"Content creation/publishing where no stronger operational function applies.", "RECRUITMENT":"Hiring workers/crew or recruiting sellers where not primarily agent management.",
            "FINANCE":"Payments, pricing administration, reconciliation, expenses or financial records.", "COMPLIANCE":"Regulatory, registration, certification, hygiene or formal compliance activity.",
            "OTHER":"A business function is evident but none of the listed categories fits.", "UNKNOWN":"No business function can be determined reliably.",
        })


class SalesChannel(StrEnum):
    DIRECT="DIRECT"; SOCIAL_COMMERCE="SOCIAL_COMMERCE"; AGENT="AGENT"; HOME_SELLER="HOME_SELLER"; POPUP="POPUP"; EVENT="EVENT"
    RETAIL="RETAIL"; DELIVERY="DELIVERY"; COD="COD"; ONLINE="ONLINE"; UNKNOWN="UNKNOWN"

    @classmethod
    def criteria(cls):
        return cls._complete({
            "DIRECT":"Direct purchase from the business or its own physical selling point.", "SOCIAL_COMMERCE":"Ordering/selling through social platform features, messages or social storefronts.",
            "AGENT":"Purchase or distribution through an explicitly identified agent/stockist/reseller.", "HOME_SELLER":"Home-based seller/reseller channel explicitly described.",
            "POPUP":"Temporary physical stall/spot channel.", "EVENT":"Sales at an event, fair, festival or expo.",
            "RETAIL":"Third-party retail shop/listing/channel.", "DELIVERY":"Delivery/runner/courier is the primary channel described.",
            "COD":"Cash-on-delivery arrangement explicitly described.", "ONLINE":"Online ordering is explicit but no more specific channel is supported.",
            "UNKNOWN":"Sales/distribution channel is absent or indeterminable.",
        })


class CustomerIntent(StrEnum):
    PURCHASE="PURCHASE"; PRICE_QUERY="PRICE_QUERY"; STOCK_QUERY="STOCK_QUERY"; LOCATION_QUERY="LOCATION_QUERY"; DELIVERY_QUERY="DELIVERY_QUERY"
    PRODUCT_QUERY="PRODUCT_QUERY"; CUSTOMIZATION="CUSTOMIZATION"; AGENT_APPLICATION="AGENT_APPLICATION"; JOB_APPLICATION="JOB_APPLICATION"
    COMPLAINT="COMPLAINT"; REFUND="REFUND"; RETURN="RETURN"; PRAISE="PRAISE"; GENERAL_CHAT="GENERAL_CHAT"; UNKNOWN="UNKNOWN"

    @classmethod
    def criteria(cls):
        return cls._complete({
            "PURCHASE":"Expresses intent to buy/order.", "PRICE_QUERY":"Asks about price/cost.", "STOCK_QUERY":"Asks whether product/variant is available.",
            "LOCATION_QUERY":"Asks where a selling point/location is.", "DELIVERY_QUERY":"Asks about delivery/shipping/COD logistics.", "PRODUCT_QUERY":"Asks about product details/variants/ingredients/format.",
            "CUSTOMIZATION":"Requests a custom option or modification.", "AGENT_APPLICATION":"Expresses interest in becoming an agent/reseller/stockist.",
            "JOB_APPLICATION":"Expresses interest in employment/crew work.", "COMPLAINT":"Reports dissatisfaction, defect or service problem.",
            "REFUND":"Requests money back/compensation/replacement as remedy.", "RETURN":"Requests or discusses returning product.",
            "PRAISE":"Positive feedback without stronger transactional intent.", "GENERAL_CHAT":"General conversation not fitting other categories.",
            "UNKNOWN":"No reliable customer intent can be determined.",
        })


class IssueClass(StrEnum):
    PRODUCT_QUALITY="PRODUCT_QUALITY"; PACKAGING="PACKAGING"; LEAKAGE="LEAKAGE"; SEAL_FAILURE="SEAL_FAILURE"; FRESHNESS="FRESHNESS"
    TASTE="TASTE"; APPEARANCE="APPEARANCE"; QUANTITY="QUANTITY"; WRONG_ITEM="WRONG_ITEM"; STOCKOUT="STOCKOUT"; DELIVERY_DELAY="DELIVERY_DELAY"
    DELIVERY_DAMAGE="DELIVERY_DAMAGE"; TRANSPORT="TRANSPORT"; STORAGE="STORAGE"; AGENT_HANDLING="AGENT_HANDLING"; CUSTOMER_SERVICE="CUSTOMER_SERVICE"
    PAYMENT="PAYMENT"; PRICE="PRICE"; LOCATION="LOCATION"; UNKNOWN="UNKNOWN"

    @classmethod
    def criteria(cls):
        return cls._complete({
            "PRODUCT_QUALITY":"General product condition/quality issue not better classified.", "PACKAGING":"Container, lid, label or packaging issue.",
            "LEAKAGE":"Liquid/sauce/brine leaking from packaging.", "SEAL_FAILURE":"Seal/lid/cap closure failure explicitly described.", "FRESHNESS":"Stale, spoiled, unexpectedly fermented or freshness concern.",
            "TASTE":"Taste/flavour issue.", "APPEARANCE":"Appearance/colour/visual quality issue.", "QUANTITY":"Quantity/fill/portion shortfall or mismatch.",
            "WRONG_ITEM":"Wrong item/variant supplied.", "STOCKOUT":"Requested item unavailable/out of stock.", "DELIVERY_DELAY":"Delivery arrived late or missed timing.",
            "DELIVERY_DAMAGE":"Damage observed on/after delivery.", "TRANSPORT":"Transport condition/logistics issue explicitly described without assuming cause.",
            "STORAGE":"Storage condition issue explicitly described.", "AGENT_HANDLING":"Agent/reseller handling issue explicitly described.", "CUSTOMER_SERVICE":"Service/response/support issue.",
            "PAYMENT":"Payment/settlement issue.", "PRICE":"Price/charge dispute or issue.", "LOCATION":"Location/access issue.", "UNKNOWN":"No reliable issue class can be determined.",
        })


class ProcessStage(StrEnum):
    SUPPLIER="SUPPLIER"; RAW_MATERIAL_RECEIVING="RAW_MATERIAL_RECEIVING"; PRODUCTION="PRODUCTION"; FILLING="FILLING"; PACKAGING="PACKAGING"
    QC="QC"; COLD_STORAGE="COLD_STORAGE"; WAREHOUSE="WAREHOUSE"; DISPATCH="DISPATCH"; TRANSPORT="TRANSPORT"; AGENT_RECEIVING="AGENT_RECEIVING"
    AGENT_STORAGE="AGENT_STORAGE"; POS="POS"; POINT_OF_SALE="POINT_OF_SALE"; LAST_MILE="LAST_MILE"; LAST_MILE_DELIVERY="LAST_MILE_DELIVERY"
    CUSTOMER_STORAGE="CUSTOMER_STORAGE"; UNKNOWN="UNKNOWN"

    @classmethod
    def criteria(cls):
        return cls._complete({
            "SUPPLIER":"Supplier/raw-source stage.", "RAW_MATERIAL_RECEIVING":"Receiving/inspection of incoming raw materials.",
            "PRODUCTION":"Product preparation or processing stage.", "FILLING":"Filling product/container stage.", "PACKAGING":"Closing, sealing, labeling or outer packing stage.",
            "QC":"Quality inspection/check stage.", "COLD_STORAGE":"Chilled/cold holding stage when explicitly applicable.", "WAREHOUSE":"Warehouse/general storage stage.",
            "DISPATCH":"Staging/dispatch before transport.", "TRANSPORT":"Movement between locations; transport mode must not be inferred.",
            "AGENT_RECEIVING":"Agent/reseller receiving/inspection stage.", "AGENT_STORAGE":"Agent/reseller storage/holding stage.",
            "POS":"Point-of-sale handling shorthand.", "POINT_OF_SALE":"Point-of-sale handling stage.", "LAST_MILE":"Final handoff/delivery shorthand.",
            "LAST_MILE_DELIVERY":"Final delivery/handoff to customer.", "CUSTOMER_STORAGE":"Customer-side storage after receipt.",
            "UNKNOWN":"Stage cannot be determined reliably; use this rather than forcing a causal stage.",
        })


class RootCauseStatus(StrEnum):
    UNDETERMINED="UNDETERMINED"; HYPOTHESIS="HYPOTHESIS"; UNDER_INVESTIGATION="UNDER_INVESTIGATION"; VERIFIED="VERIFIED"; REJECTED="REJECTED"


def get_taxonomy_summary() -> Dict[str, Any]:
    return {
        "version": TAXONOMY_VERSION,
        "brands": Brand.list_values(), "business_functions": BusinessFunction.list_values(),
        "sales_channels": SalesChannel.list_values(), "customer_intents": CustomerIntent.list_values(),
        "issue_classes": IssueClass.list_values(), "process_stages": ProcessStage.list_values(),
        "root_cause_statuses": RootCauseStatus.list_values(),
    }
