from datetime import date

from app.models.brand import Brand
from app.models.enums import FulfillmentStatus, SourcedOrderStatus, SourcingCategory
from app.models.sell import Order, Store
from app.models.source import SourcedOrder
from app.services.finance_service import get_dashboard_summary, sync_ledger


def _make_brand(db):
    brand = Brand(name="Test Brand")
    db.add(brand)
    db.commit()
    return brand


def test_sync_ledger_materializes_cogs_from_sourced_orders(db_session):
    brand = _make_brand(db_session)
    db_session.add(
        SourcedOrder(
            brand_id=brand.id,
            quote_id="q1",
            supplier_id="s1",
            title="Widgets",
            category=SourcingCategory.PRODUCT,
            quantity=100,
            unit_cost=50.0,
            total_cost=5000.0,
            status=SourcedOrderStatus.CONFIRMED,
        )
    )
    db_session.commit()

    count = sync_ledger(db_session, brand.id)

    assert count == 1
    summary = get_dashboard_summary(db_session, brand.id)
    assert summary["cogs"] == 5000.0
    assert summary["revenue"] == 0.0


def test_sync_ledger_materializes_revenue_from_orders(db_session):
    brand = _make_brand(db_session)
    store = Store(brand_id=brand.id, domain="test.nexus.store")
    db_session.add(store)
    db_session.flush()
    db_session.add(
        Order(store_id=store.id, line_items=[], subtotal=1200.0, fulfillment_status=FulfillmentStatus.DELIVERED)
    )
    db_session.commit()

    sync_ledger(db_session, brand.id)
    summary = get_dashboard_summary(db_session, brand.id)

    assert summary["revenue"] == 1200.0


def test_gross_margin_calculation(db_session):
    brand = _make_brand(db_session)
    store = Store(brand_id=brand.id, domain="test.nexus.store")
    db_session.add(store)
    db_session.flush()
    db_session.add(Order(store_id=store.id, line_items=[], subtotal=1000.0, fulfillment_status=FulfillmentStatus.DELIVERED))
    db_session.add(
        SourcedOrder(
            brand_id=brand.id, quote_id="q1", supplier_id="s1", title="Widgets",
            category=SourcingCategory.PRODUCT, quantity=10, unit_cost=40.0, total_cost=400.0,
            status=SourcedOrderStatus.CONFIRMED,
        )
    )
    db_session.commit()

    sync_ledger(db_session, brand.id)
    summary = get_dashboard_summary(db_session, brand.id)

    assert summary["gross_profit"] == 600.0
    assert summary["gross_margin_pct"] == 60.0


def test_dashboard_with_no_data_returns_none_margin(db_session):
    brand = _make_brand(db_session)
    sync_ledger(db_session, brand.id)
    summary = get_dashboard_summary(db_session, brand.id)

    assert summary["revenue"] == 0.0
    assert summary["gross_margin_pct"] is None
