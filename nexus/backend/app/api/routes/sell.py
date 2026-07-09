from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand
from app.models.sell import Channel, HelpContent, Order, PaymentProvider, Product, ShippingZone, Store
from app.models.source import SourcedOrder
from app.schemas.sell import (
    ChannelOut,
    HelpContentOut,
    OrderOut,
    PaymentProviderOut,
    ProductFromSourcedOrderRequest,
    ProductOut,
    ProductUpdate,
    ShippingZoneOut,
    StoreOut,
)
from app.services.help_service import seed_help_content
from app.services.sell_service import (
    activate_payment_provider,
    add_sourced_order_to_catalog,
    create_store,
    generate_demo_orders,
)

router = APIRouter(prefix="/api/sell", tags=["sell"])


def _get_store(db: Session, brand: Brand) -> Store:
    store = db.query(Store).filter(Store.brand_id == brand.id).first()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not created yet")
    return store


@router.post("/store", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
def create_or_get_store(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> Store:
    """PRD §6.2A — generates site structure, theme, and pre-enabled payment
    providers from the Onboard brand profile in one call."""
    return create_store(db, brand)


@router.get("/store", response_model=StoreOut)
def get_store(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> Store:
    return _get_store(db, brand)


@router.get("/products", response_model=list[ProductOut])
def list_products(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[Product]:
    store = _get_store(db, brand)
    return db.query(Product).filter(Product.store_id == store.id).all()


@router.post("/products/from-sourced-order", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def add_product_from_sourced_order(
    payload: ProductFromSourcedOrderRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> Product:
    """PRD §6.2B — pull a sourced item straight into the catalog at a
    confirmed markup, no manual re-entry of cost data."""
    store = _get_store(db, brand)
    sourced_order = (
        db.query(SourcedOrder)
        .filter(SourcedOrder.id == payload.sourced_order_id, SourcedOrder.brand_id == brand.id)
        .first()
    )
    if sourced_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sourced order not found")
    return add_sourced_order_to_catalog(db, store, sourced_order, payload.markup_multiplier)


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str, payload: ProductUpdate, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> Product:
    store = _get_store(db, brand)
    product = db.query(Product).filter(Product.id == product_id, Product.store_id == store.id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.get("/channels", response_model=list[ChannelOut])
def list_channels(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[Channel]:
    store = _get_store(db, brand)
    return db.query(Channel).filter(Channel.store_id == store.id).all()


@router.get("/shipping-zones", response_model=list[ShippingZoneOut])
def list_shipping_zones(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[ShippingZone]:
    store = _get_store(db, brand)
    return db.query(ShippingZone).filter(ShippingZone.store_id == store.id).all()


@router.get("/payment-providers", response_model=list[PaymentProviderOut])
def list_payment_providers(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[PaymentProvider]:
    store = _get_store(db, brand)
    return db.query(PaymentProvider).filter(PaymentProvider.store_id == store.id).all()


@router.post("/payment-providers/{provider_id}/activate", response_model=PaymentProviderOut)
def activate_provider(
    provider_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> PaymentProvider:
    store = _get_store(db, brand)
    provider = (
        db.query(PaymentProvider).filter(PaymentProvider.id == provider_id, PaymentProvider.store_id == store.id).first()
    )
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment provider not found")
    return activate_payment_provider(db, provider)


@router.get("/orders", response_model=list[OrderOut])
def list_orders(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[Order]:
    store = _get_store(db, brand)
    return db.query(Order).filter(Order.store_id == store.id).order_by(Order.created_at.desc()).all()


@router.post("/demo-orders", status_code=status.HTTP_201_CREATED)
def create_demo_orders(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> dict:
    store = _get_store(db, brand)
    count = generate_demo_orders(db, store)
    return {"created": count}


help_router = APIRouter(prefix="/api/help", tags=["help"])


@help_router.get("", response_model=list[HelpContentOut])
def get_help_content(
    module: str | None = Query(default=None), db: Session = Depends(get_db)
) -> list[HelpContent]:
    seed_help_content(db)  # idempotent — ensures content exists regardless of which engine startup seeded
    query = db.query(HelpContent)
    if module:
        query = query.filter(HelpContent.module == module)
    return query.all()
