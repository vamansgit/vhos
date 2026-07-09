"""Sell module services (PRD §6) — storefront creation, catalog from sourced
goods, pre-enabled payments, and a demo order generator so Finance has real
numbers without a live checkout integration."""

import hashlib
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.enums import ChannelType, FulfillmentStatus, KycStatus, PaymentProviderName, PaymentProviderStatus, SyncStatus
from app.models.sell import Channel, Order, PaymentProvider, Product, ShippingZone, Store
from app.models.source import SourcedOrder
from app.services.site_builder import generate_theme_and_pages

_ALL_PROVIDERS = [PaymentProviderName.RAZORPAY, PaymentProviderName.UPI, PaymentProviderName.STRIPE, PaymentProviderName.PAYU]


def create_store(db: Session, brand) -> Store:
    existing = db.query(Store).filter(Store.brand_id == brand.id).first()
    if existing:
        return existing

    theme_config, pages, domain = generate_theme_and_pages(brand)
    store = Store(brand_id=brand.id, domain=domain, theme_config=theme_config, pages=pages)
    db.add(store)
    db.flush()

    db.add(Channel(store_id=store.id, type=ChannelType.NATIVE, sync_status=SyncStatus.SYNCED))

    geographies = [g.strip() for g in (brand.target_geographies or "India").split(",") if g.strip()]
    for geo in geographies:
        carrier = "Delhivery" if geo.lower() in ("india", "pan-india") else "DHL"
        db.add(ShippingZone(store_id=store.id, region=geo, carrier=carrier, rate_rules={"flat_rate": 99 if carrier == "Delhivery" else 1500}))

    for provider in _ALL_PROVIDERS:
        db.add(PaymentProvider(store_id=store.id, provider=provider, status=PaymentProviderStatus.PRE_ENABLED))

    db.commit()
    db.refresh(store)
    return store


def activate_payment_provider(db: Session, provider: PaymentProvider) -> PaymentProvider:
    """Confirms a pre-enabled provider and simulates completed KYC (PRD
    §6.2D) — in production this would kick off the provider's real KYC
    flow, pre-filled from the Onboard document vault."""
    provider.status = PaymentProviderStatus.ACTIVE
    provider.kyc_status = KycStatus.COMPLETE
    db.commit()
    db.refresh(provider)
    return provider


def add_sourced_order_to_catalog(db: Session, store: Store, sourced_order: SourcedOrder, markup_multiplier: float) -> Product:
    price = round(sourced_order.unit_cost * markup_multiplier, 2)
    product = Product(
        store_id=store.id,
        sourced_order_id=sourced_order.id,
        title=sourced_order.title,
        price=price,
        cost_basis=sourced_order.unit_cost,
        inventory=sourced_order.quantity,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def generate_demo_orders(db: Session, store: Store, days: int = 60) -> int:
    """Synthetic order history so the Finance dashboard has real revenue to
    aggregate — same rationale as AdSaarthi's mock ad connector."""
    products = db.query(Product).filter(Product.store_id == store.id).all()
    if not products:
        return 0

    channel = db.query(Channel).filter(Channel.store_id == store.id).first()
    created = 0
    for day_offset in range(days):
        order_date = date.today() - timedelta(days=day_offset)
        seed = int(hashlib.sha256(f"{store.id}-{order_date.isoformat()}".encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        if rng.random() > 0.55:
            continue  # not every day has an order

        product = rng.choice(products)
        qty = rng.randint(1, 3)
        order_dt = datetime.combine(order_date, datetime.min.time(), tzinfo=timezone.utc)
        order = Order(
            store_id=store.id,
            channel_id=channel.id if channel else None,
            line_items=[{"product_id": product.id, "title": product.title, "qty": qty, "unit_price": product.price}],
            subtotal=round(product.price * qty, 2),
            fulfillment_status=FulfillmentStatus.DELIVERED,
            created_at=order_dt,
            updated_at=order_dt,
        )
        db.add(order)
        created += 1
    db.commit()
    return created
