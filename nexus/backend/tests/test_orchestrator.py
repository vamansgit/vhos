from app.models.brand import Brand
from app.models.enums import ModuleName
from app.services.orchestrator import classify_intent, handle_message


def test_classify_intent_source():
    assert classify_intent("I need 500 units of amber glass bottles from a supplier") == ModuleName.SOURCE


def test_classify_intent_sell():
    assert classify_intent("Build me a storefront with checkout and payments") == ModuleName.SELL


def test_classify_intent_finance():
    assert classify_intent("How much did I make last month, what's my margin") == ModuleName.FINANCE


def test_classify_intent_onboard():
    assert classify_intent("Update my brand's target market to include the US") == ModuleName.ONBOARD


def test_classify_intent_none_for_unrelated_text():
    assert classify_intent("hello there") == ModuleName.NONE


def _make_brand(db):
    brand = Brand(name="Test Brand", target_geographies="India")
    db.add(brand)
    db.commit()
    return brand


def test_handle_message_source_creates_request_and_matches(db_session):
    from app.models.enums import SourceNetwork, SourcingCategory, SupplierType, VerificationStatus
    from app.models.source import CatalogItem, Supplier

    supplier = Supplier(
        name="Test Supplier", source_network=SourceNetwork.INTERNAL, supplier_type=SupplierType.PRODUCT,
        category_tags="bottles", verification_status=VerificationStatus.VERIFIED, rating=4.5,
        lead_time_avg_days=10, location="Delhi",
    )
    db_session.add(supplier)
    db_session.flush()
    db_session.add(
        CatalogItem(
            supplier_id=supplier.id, category=SourcingCategory.PRODUCT, title="Bottle",
            moq=100, price_breaks=[{"min_qty": 100, "unit_price": 50}],
        )
    )
    db_session.commit()

    brand = _make_brand(db_session)
    result = handle_message(db_session, brand, "I need 500 bottles under 60 rs each")

    assert result.module == ModuleName.SOURCE
    assert "sourcing_request_id" in result.payload
    assert result.payload["match_count"] == 1


def test_handle_message_onboard_updates_target_market(db_session):
    brand = _make_brand(db_session)
    result = handle_message(db_session, brand, "update my brand's target market to include the US")

    assert result.module == ModuleName.ONBOARD
    assert "US" in brand.target_geographies


def test_handle_message_finance_returns_summary(db_session):
    brand = _make_brand(db_session)
    result = handle_message(db_session, brand, "how much did I make this month, what's my margin")

    assert result.module == ModuleName.FINANCE
    assert "revenue" in result.payload


def test_handle_message_persists_chat_history(db_session):
    from app.models.chat import ChatMessage

    brand = _make_brand(db_session)
    handle_message(db_session, brand, "hello there")

    messages = db_session.query(ChatMessage).filter(ChatMessage.brand_id == brand.id).all()
    assert len(messages) == 2  # user turn + assistant turn
    assert messages[0].role.value == "user"
    assert messages[1].role.value == "assistant"
