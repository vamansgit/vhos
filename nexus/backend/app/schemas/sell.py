from datetime import datetime

from app.models.enums import ChannelType, FulfillmentStatus, KycStatus, PaymentProviderName, PaymentProviderStatus, SyncStatus
from pydantic import BaseModel, ConfigDict, Field


class StoreOut(BaseModel):
    id: str
    domain: str
    theme_config: dict
    pages: list
    published: bool

    model_config = ConfigDict(from_attributes=True)


class ProductOut(BaseModel):
    id: str
    sourced_order_id: str | None
    title: str
    price: float
    cost_basis: float
    inventory: int

    model_config = ConfigDict(from_attributes=True)


class ProductFromSourcedOrderRequest(BaseModel):
    sourced_order_id: str
    markup_multiplier: float = Field(default=2.0, gt=1.0)


class ProductUpdate(BaseModel):
    price: float | None = None
    inventory: int | None = None


class ChannelOut(BaseModel):
    id: str
    type: ChannelType
    sync_status: SyncStatus

    model_config = ConfigDict(from_attributes=True)


class ShippingZoneOut(BaseModel):
    id: str
    region: str
    carrier: str
    rate_rules: dict

    model_config = ConfigDict(from_attributes=True)


class PaymentProviderOut(BaseModel):
    id: str
    provider: PaymentProviderName
    status: PaymentProviderStatus
    kyc_status: KycStatus

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: str
    line_items: list
    subtotal: float
    fulfillment_status: FulfillmentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HelpContentOut(BaseModel):
    id: str
    module: str
    topic: str
    type: str
    body: str
    category_tags: str | None

    model_config = ConfigDict(from_attributes=True)
