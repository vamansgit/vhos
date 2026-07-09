import enum


class BrandStage(str, enum.Enum):
    IDEA = "idea"
    PRE_LAUNCH = "pre_launch"
    LIVE = "live"


class BusinessStructure(str, enum.Enum):
    NOT_INCORPORATED = "not_incorporated"
    PROPRIETORSHIP = "proprietorship"
    LLP = "llp"
    PVT_LTD = "pvt_ltd"


class UserRole(str, enum.Enum):
    FOUNDER = "founder"
    OPS = "ops"
    FINANCE = "finance"
    GROWTH = "growth"


# --- Onboard ---


class DocumentType(str, enum.Enum):
    INCORPORATION = "incorporation"
    GST = "gst"
    FSSAI = "fssai"
    BIS = "bis"
    IEC = "iec"
    TRADEMARK = "trademark"
    LABOUR = "labour"
    BANK_KYC = "bank_kyc"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    MISSING = "missing"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"


class ChecklistItemStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    NOT_APPLICABLE = "not_applicable"


# --- Source ---


class SourcingCategory(str, enum.Enum):
    PRODUCT = "product"
    PACKAGING = "packaging"
    LOGISTICS = "logistics"
    OTHER = "other"


class SourcingRequestStatus(str, enum.Enum):
    DRAFT = "draft"
    MATCHING = "matching"
    MATCHED = "matched"
    RFQ_SENT = "rfq_sent"
    QUOTED = "quoted"
    ACCEPTED = "accepted"


class SourceNetwork(str, enum.Enum):
    INTERNAL = "internal"
    INDIAMART = "indiamart"
    ALIBABA = "alibaba"
    TRADEINDIA = "tradeindia"
    MADE_IN_CHINA = "made_in_china"


class SupplierType(str, enum.Enum):
    PRODUCT = "product"
    PACKAGING = "packaging"
    LOGISTICS = "logistics"
    OTHER = "other"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    DOCUMENTS_SUBMITTED = "documents_submitted"
    VERIFIED = "verified"
    FEATURED = "featured"


class RFQStatus(str, enum.Enum):
    OPEN = "open"
    QUOTED = "quoted"
    CLOSED = "closed"
    EXPIRED = "expired"


class SourcedOrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


# --- Sell ---


class ChannelType(str, enum.Enum):
    NATIVE = "native"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    AMAZON = "amazon"


class SyncStatus(str, enum.Enum):
    NOT_CONNECTED = "not_connected"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"


class PaymentProviderName(str, enum.Enum):
    RAZORPAY = "razorpay"
    STRIPE = "stripe"
    PAYU = "payu"
    UPI = "upi"


class PaymentProviderStatus(str, enum.Enum):
    PRE_ENABLED = "pre_enabled"
    ACTIVE = "active"
    DISABLED = "disabled"


class KycStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    COMPLETE = "complete"


class FulfillmentStatus(str, enum.Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"


class HelpContentType(str, enum.Enum):
    FAQ = "faq"
    HOW_TO = "how_to"
    BEST_PRACTICE = "best_practice"


# --- Finance ---


class LedgerEntryType(str, enum.Enum):
    REVENUE = "revenue"
    COGS = "cogs"
    EXPENSE = "expense"
    AD_SPEND = "ad_spend"


# --- Orchestrator ---


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ModuleName(str, enum.Enum):
    ONBOARD = "onboard"
    SOURCE = "source"
    SELL = "sell"
    FINANCE = "finance"
    NONE = "none"
