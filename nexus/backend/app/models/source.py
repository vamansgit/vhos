from datetime import date

from sqlalchemy import JSON, Date, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import (
    RFQStatus,
    SourcedOrderStatus,
    SourceNetwork,
    SourcingCategory,
    SourcingRequestStatus,
    SupplierType,
    VerificationStatus,
)


class SourcingRequest(UUIDPKMixin, TimestampMixin, Base):
    """PRD §5.4 — the parsed structured form of a free-text sourcing ask."""

    __tablename__ = "sourcing_requests"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[SourcingCategory] = mapped_column(Enum(SourcingCategory), default=SourcingCategory.PRODUCT)
    parsed_spec: Mapped[dict] = mapped_column(JSON, default=dict)  # attribute:value pairs parsed from raw_text
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(200), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[SourcingRequestStatus] = mapped_column(
        Enum(SourcingRequestStatus), default=SourcingRequestStatus.DRAFT
    )

    matches: Mapped[list["SourcingMatch"]] = relationship(back_populates="request", cascade="all, delete-orphan")
    rfqs: Mapped[list["RFQ"]] = relationship(back_populates="request", cascade="all, delete-orphan")


class Supplier(UUIDPKMixin, TimestampMixin, Base):
    """PRD §5.4 — not brand-scoped, shared directory. Mock/internal for MVP;
    `source_network` reserves the slot for real IndiaMART/Alibaba connectors."""

    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_network: Mapped[SourceNetwork] = mapped_column(Enum(SourceNetwork), default=SourceNetwork.INTERNAL)
    supplier_type: Mapped[SupplierType] = mapped_column(Enum(SupplierType), nullable=False)
    category_tags: Mapped[str] = mapped_column(String(300), nullable=False)  # comma-separated
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED
    )
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    lead_time_avg_days: Mapped[int] = mapped_column(Integer, default=14)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_channel: Mapped[str | None] = mapped_column(String(200), nullable=True)

    catalog_items: Mapped[list["CatalogItem"]] = relationship(back_populates="supplier", cascade="all, delete-orphan")


class CatalogItem(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "catalog_items"

    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True)
    category: Mapped[SourcingCategory] = mapped_column(Enum(SourcingCategory), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    spec_attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    price_breaks: Mapped[list] = mapped_column(JSON, default=list)  # [{"min_qty": int, "unit_price": float}]
    moq: Mapped[int] = mapped_column(Integer, default=1)

    supplier: Mapped["Supplier"] = relationship(back_populates="catalog_items")


class SourcingMatch(UUIDPKMixin, TimestampMixin, Base):
    """Ranked supplier match against a SourcingRequest — mirrors the 'never a
    bare filter grid' requirement (PRD §5.2A): every match carries a score
    and a plain-language reason."""

    __tablename__ = "sourcing_matches"

    request_id: Mapped[str] = mapped_column(ForeignKey("sourcing_requests.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True)
    catalog_item_id: Mapped[str] = mapped_column(ForeignKey("catalog_items.id"), nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=0)

    request: Mapped["SourcingRequest"] = relationship(back_populates="matches")
    supplier: Mapped["Supplier"] = relationship()
    catalog_item: Mapped["CatalogItem"] = relationship()


class RFQ(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "rfqs"

    request_id: Mapped[str] = mapped_column(ForeignKey("sourcing_requests.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)  # auto-generated, editable RFQ text
    status: Mapped[RFQStatus] = mapped_column(Enum(RFQStatus), default=RFQStatus.OPEN)

    request: Mapped["SourcingRequest"] = relationship(back_populates="rfqs")
    supplier: Mapped["Supplier"] = relationship()
    quote: Mapped["Quote | None"] = relationship(back_populates="rfq", uselist=False, cascade="all, delete-orphan")


class Quote(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "quotes"

    rfq_id: Mapped[str] = mapped_column(ForeignKey("rfqs.id"), nullable=False, unique=True)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    moq: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    terms: Mapped[str | None] = mapped_column(String(500), nullable=True)

    rfq: Mapped["RFQ"] = relationship(back_populates="quote")


class SourcedOrder(UUIDPKMixin, TimestampMixin, Base):
    """An accepted quote — flows into Finance as expected cost and into Sell
    as a draft catalog entry (PRD §5.3)."""

    __tablename__ = "sourced_orders"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"), nullable=False)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[SourcingCategory] = mapped_column(Enum(SourcingCategory), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[SourcedOrderStatus] = mapped_column(Enum(SourcedOrderStatus), default=SourcedOrderStatus.PENDING)

    supplier: Mapped["Supplier"] = relationship()
