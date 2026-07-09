from datetime import date

from app.models.enums import SourceNetwork, SourcingCategory, SupplierType, VerificationStatus
from app.models.source import CatalogItem, SourcingRequest, Supplier
from app.services.source_service import accept_quote, create_rfqs, generate_matches, submit_quote


def _make_supplier(db, **overrides):
    defaults = dict(
        name="Test Supplier",
        source_network=SourceNetwork.INTERNAL,
        supplier_type=SupplierType.PRODUCT,
        category_tags="widgets",
        verification_status=VerificationStatus.VERIFIED,
        rating=4.5,
        lead_time_avg_days=10,
        location="Delhi",
    )
    defaults.update(overrides)
    supplier = Supplier(**defaults)
    db.add(supplier)
    db.flush()
    return supplier


def _make_catalog_item(db, supplier, **overrides):
    defaults = dict(
        supplier_id=supplier.id,
        category=SourcingCategory.PRODUCT,
        title="Widget",
        moq=100,
        price_breaks=[{"min_qty": 100, "unit_price": 50}, {"min_qty": 500, "unit_price": 40}],
    )
    defaults.update(overrides)
    item = CatalogItem(**defaults)
    db.add(item)
    db.flush()
    return item


def _make_request(db, brand_id="brand-1", **overrides):
    defaults = dict(
        brand_id=brand_id,
        raw_text="500 widgets under 45 rs each",
        category=SourcingCategory.PRODUCT,
        quantity=500,
        target_price=45.0,
    )
    defaults.update(overrides)
    request = SourcingRequest(**defaults)
    db.add(request)
    db.commit()
    return request


def test_generate_matches_filters_by_category_and_moq(db_session):
    cheap_supplier = _make_supplier(db_session, name="Cheap Co")
    _make_catalog_item(db_session, cheap_supplier)

    high_moq_supplier = _make_supplier(db_session, name="High MOQ Co")
    _make_catalog_item(db_session, high_moq_supplier, moq=10_000)

    packaging_supplier = _make_supplier(db_session, name="Packaging Co", supplier_type=SupplierType.PACKAGING)
    _make_catalog_item(db_session, packaging_supplier, category=SourcingCategory.PACKAGING)

    db_session.commit()
    request = _make_request(db_session)

    matches = generate_matches(db_session, request)

    names = [m.supplier.name for m in matches]
    assert "Cheap Co" in names
    assert "High MOQ Co" not in names  # request quantity (500) below this supplier's MOQ
    assert "Packaging Co" not in names  # wrong category


def test_matches_ranked_by_fit_score_descending(db_session):
    cheap = _make_supplier(db_session, name="Cheap Reliable", rating=4.8, lead_time_avg_days=5)
    _make_catalog_item(db_session, cheap, price_breaks=[{"min_qty": 100, "unit_price": 40}])

    expensive = _make_supplier(db_session, name="Pricey Slow", rating=3.0, lead_time_avg_days=30)
    _make_catalog_item(db_session, expensive, price_breaks=[{"min_qty": 100, "unit_price": 90}])

    db_session.commit()
    request = _make_request(db_session)

    matches = generate_matches(db_session, request)

    assert matches[0].supplier.name == "Cheap Reliable"
    assert matches[0].fit_score > matches[1].fit_score


def test_rfq_to_accepted_order_flow(db_session):
    supplier = _make_supplier(db_session)
    _make_catalog_item(db_session, supplier)
    db_session.commit()
    request = _make_request(db_session)
    matches = generate_matches(db_session, request)

    rfqs = create_rfqs(db_session, request, [matches[0].supplier_id])
    assert len(rfqs) == 1
    assert "Test Supplier" in rfqs[0].message

    quote = submit_quote(db_session, rfqs[0], unit_price=42.0, moq=100, lead_time_days=14, terms="50% advance")
    assert quote.unit_price == 42.0

    order = accept_quote(db_session, quote, brand_id="brand-1", quantity=500)
    assert order.total_cost == 42.0 * 500
    assert order.quantity == 500


def test_accepted_request_status_survives_later_quote_on_sibling_rfq(db_session):
    """A request with two RFQs: accepting one shouldn't get downgraded back
    to 'quoted' when the second sibling RFQ is quoted afterward."""
    supplier_a = _make_supplier(db_session, name="Supplier A")
    _make_catalog_item(db_session, supplier_a)
    supplier_b = _make_supplier(db_session, name="Supplier B")
    _make_catalog_item(db_session, supplier_b)
    db_session.commit()

    request = _make_request(db_session)
    matches = generate_matches(db_session, request)
    rfqs = create_rfqs(db_session, request, [m.supplier_id for m in matches])
    assert len(rfqs) == 2

    quote_a = submit_quote(db_session, rfqs[0], unit_price=40.0, moq=100, lead_time_days=10, terms=None)
    accept_quote(db_session, quote_a, brand_id="brand-1", quantity=500)
    db_session.refresh(request)
    assert request.status.value == "accepted"

    submit_quote(db_session, rfqs[1], unit_price=45.0, moq=100, lead_time_days=12, terms=None)
    db_session.refresh(request)
    assert request.status.value == "accepted"
