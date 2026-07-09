from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import (
    ChannelType,
    FulfillmentStatus,
    HelpContentType,
    KycStatus,
    PaymentProviderName,
    PaymentProviderStatus,
    SyncStatus,
)


class Store(UUIDPKMixin, TimestampMixin, Base):
    """PRD §6.4 — one native storefront per brand for MVP."""

    __tablename__ = "stores"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, unique=True)
    domain: Mapped[str] = mapped_column(String(200), nullable=False)
    theme_config: Mapped[dict] = mapped_column(JSON, default=dict)  # colors, typography, layout descriptors
    pages: Mapped[list] = mapped_column(JSON, default=list)  # generated page structure
    published: Mapped[bool] = mapped_column(default=False)

    products: Mapped[list["Product"]] = relationship(back_populates="store", cascade="all, delete-orphan")
    channels: Mapped[list["Channel"]] = relationship(back_populates="store", cascade="all, delete-orphan")
    shipping_zones: Mapped[list["ShippingZone"]] = relationship(back_populates="store", cascade="all, delete-orphan")
    payment_providers: Mapped[list["PaymentProvider"]] = relationship(
        back_populates="store", cascade="all, delete-orphan"
    )


class Product(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "products"

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), nullable=False, index=True)
    sourced_order_id: Mapped[str | None] = mapped_column(ForeignKey("sourced_orders.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    cost_basis: Mapped[float] = mapped_column(Float, default=0.0)
    inventory: Mapped[int] = mapped_column(Integer, default=0)
    variants: Mapped[list] = mapped_column(JSON, default=list)

    store: Mapped["Store"] = relationship(back_populates="products")


class Channel(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "channels"

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), nullable=False, index=True)
    type: Mapped[ChannelType] = mapped_column(Enum(ChannelType), default=ChannelType.NATIVE)
    sync_status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus), default=SyncStatus.NOT_CONNECTED)
    credentials_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)

    store: Mapped["Store"] = relationship(back_populates="channels")


class ShippingZone(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "shipping_zones"

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(200), nullable=False)
    carrier: Mapped[str] = mapped_column(String(100), nullable=False)
    rate_rules: Mapped[dict] = mapped_column(JSON, default=dict)

    store: Mapped["Store"] = relationship(back_populates="shipping_zones")


class PaymentProvider(UUIDPKMixin, TimestampMixin, Base):
    """Pre-enabled by default (PRD §6.2D) — the founder just confirms and
    completes KYC rather than a from-scratch signup per provider."""

    __tablename__ = "payment_providers"

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), nullable=False, index=True)
    provider: Mapped[PaymentProviderName] = mapped_column(Enum(PaymentProviderName), nullable=False)
    status: Mapped[PaymentProviderStatus] = mapped_column(
        Enum(PaymentProviderStatus), default=PaymentProviderStatus.PRE_ENABLED
    )
    kyc_status: Mapped[KycStatus] = mapped_column(Enum(KycStatus), default=KycStatus.NOT_STARTED)

    store: Mapped["Store"] = relationship(back_populates="payment_providers")


class Order(UUIDPKMixin, TimestampMixin, Base):
    """Customer order on the storefront. Demo orders are generator-seeded
    (see services/connectors/demo_orders.py) so Finance has real data to
    show without a live checkout integration."""

    __tablename__ = "orders"

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), nullable=False, index=True)
    channel_id: Mapped[str | None] = mapped_column(ForeignKey("channels.id"), nullable=True)
    line_items: Mapped[list] = mapped_column(JSON, default=list)  # [{product_id, title, qty, unit_price}]
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    fulfillment_status: Mapped[FulfillmentStatus] = mapped_column(
        Enum(FulfillmentStatus), default=FulfillmentStatus.PENDING
    )

    store: Mapped["Store"] = relationship()


class HelpContent(UUIDPKMixin, TimestampMixin, Base):
    """PRD §6.2E / §10.1 — guided help layer, present in every module."""

    __tablename__ = "help_content"

    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    type: Mapped[HelpContentType] = mapped_column(Enum(HelpContentType), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category_tags: Mapped[str | None] = mapped_column(String(300), nullable=True)
