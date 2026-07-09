"""Finance & Compliance module services (PRD §7) — the Ledger is a
materialized view over Source/Sell records, never a duplicate manual
re-entry system, and TaxProfile is read from Onboard's Document vault."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentType, LedgerEntryType
from app.models.finance import LedgerEntry, TaxProfile
from app.models.sell import Order, Store
from app.models.source import SourcedOrder


def sync_ledger(db: Session, brand_id: str) -> int:
    """Rebuilds the ledger from source-of-truth records. Idempotent — safe
    to call after every sourcing acceptance or new order."""
    db.query(LedgerEntry).filter(LedgerEntry.brand_id == brand_id).delete()

    count = 0
    for sourced_order in db.query(SourcedOrder).filter(SourcedOrder.brand_id == brand_id).all():
        db.add(
            LedgerEntry(
                brand_id=brand_id,
                date=sourced_order.created_at.date(),
                type=LedgerEntryType.COGS,
                amount=sourced_order.total_cost,
                description=f"Sourced: {sourced_order.title} x{sourced_order.quantity}",
                source_ref=f"sourced_order:{sourced_order.id}",
            )
        )
        count += 1

    store = db.query(Store).filter(Store.brand_id == brand_id).first()
    if store:
        for order in db.query(Order).filter(Order.store_id == store.id).all():
            db.add(
                LedgerEntry(
                    brand_id=brand_id,
                    date=order.created_at.date(),
                    type=LedgerEntryType.REVENUE,
                    amount=order.subtotal,
                    description=f"Order {order.id[:8]}",
                    source_ref=f"order:{order.id}",
                )
            )
            count += 1

    db.commit()
    return count


def get_dashboard_summary(db: Session, brand_id: str, days: int = 90) -> dict:
    start = date.today() - timedelta(days=days - 1)
    entries = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.brand_id == brand_id, LedgerEntry.date >= start)
        .all()
    )

    revenue = sum(e.amount for e in entries if e.type == LedgerEntryType.REVENUE)
    cogs = sum(e.amount for e in entries if e.type == LedgerEntryType.COGS)
    expenses = sum(e.amount for e in entries if e.type == LedgerEntryType.EXPENSE)
    ad_spend = sum(e.amount for e in entries if e.type == LedgerEntryType.AD_SPEND)

    gross_profit = revenue - cogs
    gross_margin_pct = round((gross_profit / revenue) * 100, 1) if revenue > 0 else None
    net_profit = gross_profit - expenses - ad_spend

    by_date: dict[str, dict] = {}
    for e in sorted(entries, key=lambda x: x.date):
        key = e.date.isoformat()
        row = by_date.setdefault(key, {"date": key, "revenue": 0.0, "cogs": 0.0, "expenses": 0.0, "ad_spend": 0.0})
        row[e.type.value if e.type.value != "ad_spend" else "ad_spend"] += e.amount

    return {
        "revenue": round(revenue, 2),
        "cogs": round(cogs, 2),
        "expenses": round(expenses, 2),
        "ad_spend": round(ad_spend, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": gross_margin_pct,
        "net_profit": round(net_profit, 2),
        "cash_position": round(net_profit, 2),  # simplified: no separate bank-feed reconciliation in MVP
        "daily_series": sorted(by_date.values(), key=lambda r: r["date"]),
    }


def sync_tax_profile(db: Session, brand) -> TaxProfile:
    """Pulls GSTIN from the Onboard vault's GST document rather than asking
    the user to re-enter it (PRD §7.2B)."""
    profile = db.query(TaxProfile).filter(TaxProfile.brand_id == brand.id).first()
    if profile is None:
        profile = TaxProfile(brand_id=brand.id)
        db.add(profile)

    gst_doc = db.query(Document).filter(Document.brand_id == brand.id, Document.type == DocumentType.GST).first()
    profile.gstin = gst_doc.extracted_value if gst_doc else None
    profile.applicable_schemes = "Composition" if brand.structure.value == "not_incorporated" else "Regular"

    db.commit()
    db.refresh(profile)
    return profile
