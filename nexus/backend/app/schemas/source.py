from datetime import date

from app.models.enums import (
    RFQStatus,
    SourcedOrderStatus,
    SourceNetwork,
    SourcingCategory,
    SourcingRequestStatus,
    SupplierType,
    VerificationStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class SourcingRequestCreate(BaseModel):
    raw_text: str = Field(min_length=3)


class SourcingRequestOut(BaseModel):
    id: str
    brand_id: str
    raw_text: str
    category: SourcingCategory
    parsed_spec: dict
    quantity: int | None
    target_price: float | None
    destination: str | None
    deadline: date | None
    status: SourcingRequestStatus
    confirmation_line: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SupplierOut(BaseModel):
    id: str
    name: str
    source_network: SourceNetwork
    supplier_type: SupplierType
    category_tags: str
    verification_status: VerificationStatus
    rating: float
    lead_time_avg_days: int
    location: str | None

    model_config = ConfigDict(from_attributes=True)


class CatalogItemOut(BaseModel):
    id: str
    title: str
    spec_attributes: dict
    price_breaks: list
    moq: int

    model_config = ConfigDict(from_attributes=True)


class SourcingMatchOut(BaseModel):
    id: str
    supplier: SupplierOut
    catalog_item: CatalogItemOut
    fit_score: float
    estimated_unit_price: float
    reason: str
    rank: int

    model_config = ConfigDict(from_attributes=True)


class RFQCreateRequest(BaseModel):
    supplier_ids: list[str] = Field(min_length=1)


class QuoteSubmitRequest(BaseModel):
    unit_price: float = Field(gt=0)
    moq: int = Field(gt=0)
    lead_time_days: int = Field(gt=0)
    terms: str | None = None


class QuoteOut(BaseModel):
    id: str
    unit_price: float
    moq: int
    lead_time_days: int
    terms: str | None

    model_config = ConfigDict(from_attributes=True)


class RFQOut(BaseModel):
    id: str
    supplier: SupplierOut
    message: str
    status: RFQStatus
    quote: QuoteOut | None = None

    model_config = ConfigDict(from_attributes=True)


class QuoteAcceptRequest(BaseModel):
    quantity: int = Field(gt=0)


class SourcedOrderOut(BaseModel):
    id: str
    title: str
    category: SourcingCategory
    quantity: int
    unit_cost: float
    total_cost: float
    status: SourcedOrderStatus

    model_config = ConfigDict(from_attributes=True)
