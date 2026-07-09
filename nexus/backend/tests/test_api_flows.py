from app.models.enums import SourceNetwork, SourcingCategory, SupplierType, VerificationStatus
from app.models.source import CatalogItem, Supplier


def _seed_supplier(db_session, **overrides):
    defaults = dict(
        name="API Test Supplier", source_network=SourceNetwork.INTERNAL, supplier_type=SupplierType.PRODUCT,
        category_tags="widgets", verification_status=VerificationStatus.VERIFIED, rating=4.5,
        lead_time_avg_days=10, location="Delhi",
    )
    defaults.update(overrides)
    supplier = Supplier(**defaults)
    db_session.add(supplier)
    db_session.flush()
    db_session.add(
        CatalogItem(
            supplier_id=supplier.id, category=SourcingCategory.PRODUCT, title="Widget",
            moq=100, price_breaks=[{"min_qty": 100, "unit_price": 50}],
        )
    )
    db_session.commit()
    return supplier


def test_signup_seeds_checklist(client):
    signup = client.post(
        "/api/auth/signup",
        json={"brand_name": "New Co", "category": "food", "full_name": "Founder", "email": "f@new.com", "password": "password123"},
    )
    assert signup.status_code == 201
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}

    checklist = client.get("/api/onboard/checklist", headers=headers)
    assert checklist.status_code == 200
    assert any("fssai" in item["requirement"].lower() for item in checklist.json())


def test_founder_profile_update(client, auth_headers):
    response = client.patch(
        "/api/onboard/founder",
        json={"background_text": "10 years in retail", "risk_appetite": "medium", "time_availability_hours_per_week": 20},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["background_text"] == "10 years in retail"


def test_document_upload_and_versioning(client, auth_headers):
    first = client.post(
        "/api/onboard/documents",
        json={"type": "gst", "label": "GST Cert", "file_ref": "vault/v1.pdf", "extracted_value": "27ABCDE1234F1Z5"},
        headers=auth_headers,
    )
    assert first.status_code == 201
    assert len(first.json()["versions"]) == 1

    second = client.post(
        "/api/onboard/documents",
        json={"type": "gst", "label": "GST Cert renewed", "file_ref": "vault/v2.pdf"},
        headers=auth_headers,
    )
    assert second.json()["id"] == first.json()["id"]
    assert len(second.json()["versions"]) == 2


def test_full_source_to_sell_to_finance_flow(client, auth_headers, db_session):
    _seed_supplier(db_session)

    brief = client.post("/api/source/requests", json={"raw_text": "500 widgets under 60 rs each"}, headers=auth_headers)
    assert brief.status_code == 201
    request_id = brief.json()["id"]
    assert brief.json()["confirmation_line"]

    matches = client.post(f"/api/source/requests/{request_id}/match", headers=auth_headers)
    assert matches.status_code == 200
    assert len(matches.json()) == 1
    supplier_id = matches.json()[0]["supplier"]["id"]

    rfqs = client.post(f"/api/source/requests/{request_id}/rfqs", json={"supplier_ids": [supplier_id]}, headers=auth_headers)
    assert rfqs.status_code == 201
    rfq_id = rfqs.json()[0]["id"]

    quote = client.post(
        f"/api/source/rfqs/{rfq_id}/quote",
        json={"unit_price": 48.0, "moq": 100, "lead_time_days": 10, "terms": "50% advance"},
        headers=auth_headers,
    )
    assert quote.status_code == 201
    quote_id = quote.json()["id"]

    order = client.post(f"/api/source/quotes/{quote_id}/accept", json={"quantity": 500}, headers=auth_headers)
    assert order.status_code == 201
    assert order.json()["total_cost"] == 48.0 * 500
    sourced_order_id = order.json()["id"]

    store = client.post("/api/sell/store", headers=auth_headers)
    assert store.status_code == 201

    product = client.post(
        "/api/sell/products/from-sourced-order",
        json={"sourced_order_id": sourced_order_id, "markup_multiplier": 2.0},
        headers=auth_headers,
    )
    assert product.status_code == 201
    assert product.json()["price"] == 48.0 * 2.0

    dashboard = client.get("/api/finance/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["cogs"] == 48.0 * 500


def test_chat_endpoint_routes_and_persists_history(client, auth_headers, db_session):
    _seed_supplier(db_session)

    response = client.post("/api/chat", json={"text": "I need 500 widgets under 60 rs each"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["module"] == "source"

    history = client.get("/api/chat/history", headers=auth_headers)
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_help_content_filterable_by_module(client, auth_headers):
    response = client.get("/api/help?module=finance", headers=auth_headers)
    assert response.status_code == 200
    assert all(item["module"] == "finance" for item in response.json())
    assert len(response.json()) > 0


def test_payment_provider_pre_enabled_then_activated(client, auth_headers):
    client.post("/api/sell/store", headers=auth_headers)
    providers = client.get("/api/sell/payment-providers", headers=auth_headers).json()
    assert all(p["status"] == "pre_enabled" for p in providers)

    razorpay = next(p for p in providers if p["provider"] == "razorpay")
    activated = client.post(f"/api/sell/payment-providers/{razorpay['id']}/activate", headers=auth_headers)
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
    assert activated.json()["kyc_status"] == "complete"
