"""Seeds demo data mirroring the PRD's own end-to-end scenario (§14): a
pre-launch founder with a textile background building a copper water
bottle brand — brand/founder profile, documents, a supplier directory
across product/packaging/logistics, an accepted sourcing order, a
generated storefront with demo sales, so every module has real data
immediately after `python -m app.seed`.
"""

from datetime import date, timedelta

from app.database import Base, SessionLocal, engine
from app.models.brand import Brand, FounderProfile
from app.models.enums import DocumentType, SourcingCategory, SourceNetwork, SupplierType, VerificationStatus, BrandStage, BusinessStructure
from app.models.source import CatalogItem, Supplier
from app.models.user import User
from app.security import hash_password
from app.services.finance_service import sync_ledger
from app.services.help_service import seed_help_content
from app.services.onboard_service import seed_checklist_for_brand, upsert_document
from app.services.sell_service import activate_payment_provider, add_sourced_order_to_catalog, create_store, generate_demo_orders
from app.models.sell import PaymentProvider, PaymentProviderName
from app.services.source_service import accept_quote, create_rfqs, generate_matches, submit_quote

DEMO_EMAIL = "demo@nexus.app"
DEMO_PASSWORD = "demo12345"

_SUPPLIERS: list[dict] = [
    {"name": "Moradabad Copperware Co", "supplier_type": SupplierType.PRODUCT, "category_tags": "copper bottles, drinkware",
     "verification_status": VerificationStatus.VERIFIED, "rating": 4.6, "lead_time_avg_days": 12, "location": "Moradabad, UP",
     "items": [{"title": "Copper Water Bottle 1L", "moq": 100, "price_breaks": [{"min_qty": 100, "unit_price": 280}, {"min_qty": 500, "unit_price": 230}, {"min_qty": 1000, "unit_price": 200}]}]},
    {"name": "Haldwani Metal Crafts", "supplier_type": SupplierType.PRODUCT, "category_tags": "copper bottles, metal drinkware",
     "verification_status": VerificationStatus.VERIFIED, "rating": 4.3, "lead_time_avg_days": 18, "location": "Haldwani, UK",
     "items": [{"title": "Copper Water Bottle 1L", "moq": 200, "price_breaks": [{"min_qty": 200, "unit_price": 260}, {"min_qty": 500, "unit_price": 215}, {"min_qty": 1000, "unit_price": 190}]}]},
    {"name": "Jaipur Handicrafts Export", "supplier_type": SupplierType.PRODUCT, "category_tags": "copper bottles, brass items",
     "verification_status": VerificationStatus.UNVERIFIED, "rating": 3.8, "lead_time_avg_days": 25, "location": "Jaipur, RJ",
     "items": [{"title": "Copper Water Bottle 1L", "moq": 50, "price_breaks": [{"min_qty": 50, "unit_price": 300}, {"min_qty": 500, "unit_price": 245}]}]},
    {"name": "SS Copperware Industries", "supplier_type": SupplierType.PRODUCT, "category_tags": "copper bottles, drinkware",
     "verification_status": VerificationStatus.FEATURED, "rating": 4.8, "lead_time_avg_days": 10, "location": "Moradabad, UP",
     "items": [{"title": "Copper Water Bottle 1L", "moq": 500, "price_breaks": [{"min_qty": 500, "unit_price": 235}, {"min_qty": 1000, "unit_price": 205}, {"min_qty": 2000, "unit_price": 180}]}]},
    {"name": "EcoMetal Traders", "supplier_type": SupplierType.PRODUCT, "category_tags": "copper bottles, steel bottles",
     "verification_status": VerificationStatus.DOCUMENTS_SUBMITTED, "rating": 4.0, "lead_time_avg_days": 20, "location": "Delhi",
     "items": [{"title": "Copper Water Bottle 1L", "moq": 100, "price_breaks": [{"min_qty": 100, "unit_price": 270}, {"min_qty": 500, "unit_price": 220}]}]},
    {"name": "Print & Pack Solutions", "supplier_type": SupplierType.PACKAGING, "category_tags": "branded boxes, mailers",
     "verification_status": VerificationStatus.VERIFIED, "rating": 4.5, "lead_time_avg_days": 7, "location": "Noida, UP",
     "items": [{"title": "Branded Mailer Box (custom print)", "moq": 500, "price_breaks": [{"min_qty": 500, "unit_price": 18}, {"min_qty": 1000, "unit_price": 14}, {"min_qty": 5000, "unit_price": 10}]}]},
    {"name": "GreenBox Packaging", "supplier_type": SupplierType.PACKAGING, "category_tags": "eco boxes, mailers",
     "verification_status": VerificationStatus.VERIFIED, "rating": 4.2, "lead_time_avg_days": 10, "location": "Pune, MH",
     "items": [{"title": "Recycled Kraft Box", "moq": 500, "price_breaks": [{"min_qty": 500, "unit_price": 20}, {"min_qty": 2000, "unit_price": 15}]}]},
    {"name": "Rapid Print Co", "supplier_type": SupplierType.PACKAGING, "category_tags": "labels, inserts, boxes",
     "verification_status": VerificationStatus.UNVERIFIED, "rating": 3.5, "lead_time_avg_days": 5, "location": "Mumbai, MH",
     "items": [{"title": "Product Label & Insert Set", "moq": 1000, "price_breaks": [{"min_qty": 1000, "unit_price": 8}, {"min_qty": 5000, "unit_price": 6}]}]},
    {"name": "Artisan Carton Works", "supplier_type": SupplierType.PACKAGING, "category_tags": "custom cartons",
     "verification_status": VerificationStatus.FEATURED, "rating": 4.7, "lead_time_avg_days": 12, "location": "Delhi",
     "items": [{"title": "Rigid Gift Carton", "moq": 500, "price_breaks": [{"min_qty": 500, "unit_price": 22}, {"min_qty": 1000, "unit_price": 17}]}]},
    {"name": "Delhivery Partner Network", "supplier_type": SupplierType.LOGISTICS, "category_tags": "pan-india courier, cod",
     "verification_status": VerificationStatus.VERIFIED, "rating": 4.4, "lead_time_avg_days": 5, "location": "Pan-India",
     "items": [{"title": "Pan-India COD Courier", "moq": 1, "price_breaks": [{"min_qty": 1, "unit_price": 55}, {"min_qty": 1000, "unit_price": 45}]}]},
    {"name": "Shiprocket Aggregator", "supplier_type": SupplierType.LOGISTICS, "category_tags": "multi-carrier, cod, international",
     "verification_status": VerificationStatus.VERIFIED, "rating": 4.3, "lead_time_avg_days": 4, "location": "Pan-India",
     "items": [{"title": "Multi-Carrier Shipping", "moq": 1, "price_breaks": [{"min_qty": 1, "unit_price": 60}]}]},
    {"name": "GlobalFreight Forwarders", "supplier_type": SupplierType.LOGISTICS, "category_tags": "international freight, bulk import",
     "verification_status": VerificationStatus.DOCUMENTS_SUBMITTED, "rating": 4.0, "lead_time_avg_days": 20, "location": "Mumbai Port",
     "items": [{"title": "Bulk Import Freight Forwarding", "moq": 1, "price_breaks": [{"min_qty": 1, "unit_price": 150}]}]},
]

_CATEGORY_BY_TYPE = {
    SupplierType.PRODUCT: SourcingCategory.PRODUCT,
    SupplierType.PACKAGING: SourcingCategory.PACKAGING,
    SupplierType.LOGISTICS: SourcingCategory.LOGISTICS,
}


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Brand).filter(Brand.name == "Copper & Co").first():
            print("Demo data already present — skipping.")
            return

        brand = Brand(
            name="Copper & Co",
            category="home",
            stage=BrandStage.PRE_LAUNCH,
            structure=BusinessStructure.NOT_INCORPORATED,
            target_geographies="India",
            style_descriptors="minimal, earthy",
            team_size=1,
        )
        db.add(brand)
        db.flush()

        owner = User(brand_id=brand.id, email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD), full_name="Aarav Mehta")
        db.add(owner)

        db.add(
            FounderProfile(
                brand_id=brand.id,
                background_text="Used to work in textile manufacturing.",
                aspirations_text="Always wanted to start something in home goods. Can give this about 15 hours a week for now.",
                risk_appetite="medium",
                time_availability_hours_per_week=15,
            )
        )
        db.commit()

        seed_checklist_for_brand(db, brand)

        upsert_document(
            db,
            brand,
            doc_type=DocumentType.GST,
            label="GST Registration Certificate",
            file_ref="vault/gst-cert-v1.pdf",
            note="Initial upload",
            expiry_date=date.today() + timedelta(days=365),
            extracted_value="09ABCPM1234F1Z5",
        )

        seed_help_content(db)

        for entry in _SUPPLIERS:
            supplier = Supplier(
                name=entry["name"],
                source_network=SourceNetwork.INTERNAL,
                supplier_type=entry["supplier_type"],
                category_tags=entry["category_tags"],
                verification_status=entry["verification_status"],
                rating=entry["rating"],
                lead_time_avg_days=entry["lead_time_avg_days"],
                location=entry["location"],
            )
            db.add(supplier)
            db.flush()
            for item in entry["items"]:
                db.add(
                    CatalogItem(
                        supplier_id=supplier.id,
                        category=_CATEGORY_BY_TYPE[entry["supplier_type"]],
                        title=item["title"],
                        moq=item["moq"],
                        price_breaks=item["price_breaks"],
                    )
                )
        db.commit()

        from app.models.enums import SourcingRequestStatus
        from app.models.source import SourcingRequest

        request = SourcingRequest(
            brand_id=brand.id,
            raw_text="Find me suppliers for 500 units, 1L capacity copper water bottles under ₹250 each, delivered to Mumbai in 3 weeks.",
            category=SourcingCategory.PRODUCT,
            parsed_spec={"capacity": "1L", "material": "copper"},
            quantity=500,
            target_price=250,
            destination="Mumbai",
            deadline=date.today() + timedelta(days=21),
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        matches = generate_matches(db, request)
        top_supplier_ids = [m.supplier_id for m in matches[:2]]
        rfqs = create_rfqs(db, request, top_supplier_ids)

        accepted_order = None
        for i, rfq in enumerate(rfqs):
            match = next(m for m in matches if m.supplier_id == rfq.supplier_id)
            quote = submit_quote(
                db, rfq, unit_price=match.estimated_unit_price, moq=match.catalog_item.moq, lead_time_days=12, terms="50% advance, 50% on delivery"
            )
            if i == 0:
                accepted_order = accept_quote(db, quote, brand.id, quantity=500)

        store = create_store(db, brand)
        if accepted_order:
            add_sourced_order_to_catalog(db, store, accepted_order, markup_multiplier=2.4)

        for provider in db.query(PaymentProvider).filter(PaymentProvider.store_id == store.id).all():
            if provider.provider in (PaymentProviderName.RAZORPAY, PaymentProviderName.UPI):
                activate_payment_provider(db, provider)

        generate_demo_orders(db, store, days=60)
        sync_ledger(db, brand.id)

        print("Seed complete.")
        print(f"  Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  Brand: {brand.name} ({brand.id})")
        print(f"  Sourcing request: {request.id}")
        print(f"  Store: {store.domain}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
