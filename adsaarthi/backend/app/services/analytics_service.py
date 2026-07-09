from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ad_account import AdAccount
from app.models.ad_metric import AdMetricDaily
from app.models.brand import Brand
from app.models.base import utcnow
from app.services.connectors import get_connector

DEFAULT_SYNC_DAYS = 90


def sync_ad_account(db: Session, ad_account: AdAccount, days: int = DEFAULT_SYNC_DAYS) -> int:
    """Pulls the last `days` of metrics from the platform connector and
    replaces any existing rows in that window (idempotent re-sync)."""
    end = date.today()
    start = end - timedelta(days=days - 1)

    connector = get_connector(ad_account.platform)
    raw_rows = connector.fetch_daily_metrics(ad_account.external_account_id, ad_account.token_reference, start, end)

    db.query(AdMetricDaily).filter(
        AdMetricDaily.ad_account_id == ad_account.id,
        AdMetricDaily.date >= start,
        AdMetricDaily.date <= end,
    ).delete()

    for row in raw_rows:
        db.add(
            AdMetricDaily(
                ad_account_id=ad_account.id,
                brand_id=ad_account.brand_id,
                date=row.date,
                campaign_name=row.campaign_name,
                spend=row.spend,
                impressions=row.impressions,
                clicks=row.clicks,
                conversions=row.conversions,
                revenue=row.revenue,
            )
        )

    ad_account.last_synced_at = utcnow().isoformat()
    db.commit()
    return len(raw_rows)


def _cac(spend: float, conversions: int) -> float | None:
    return round(spend / conversions, 2) if conversions > 0 else None


def _roas(revenue: float, spend: float) -> float | None:
    return round(revenue / spend, 2) if spend > 0 else None


def get_daily_series(db: Session, brand_id: str, start: date, end: date) -> list[dict]:
    rows = (
        db.query(
            AdMetricDaily.date,
            func.sum(AdMetricDaily.spend).label("spend"),
            func.sum(AdMetricDaily.impressions).label("impressions"),
            func.sum(AdMetricDaily.clicks).label("clicks"),
            func.sum(AdMetricDaily.conversions).label("conversions"),
            func.sum(AdMetricDaily.revenue).label("revenue"),
        )
        .filter(AdMetricDaily.brand_id == brand_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
        .group_by(AdMetricDaily.date)
        .order_by(AdMetricDaily.date)
        .all()
    )
    return [
        {
            "date": r.date,
            "spend": round(r.spend or 0, 2),
            "impressions": int(r.impressions or 0),
            "clicks": int(r.clicks or 0),
            "conversions": int(r.conversions or 0),
            "revenue": round(r.revenue or 0, 2),
            "cac": _cac(r.spend or 0, r.conversions or 0),
            "roas": _roas(r.revenue or 0, r.spend or 0),
        }
        for r in rows
    ]


def get_platform_breakdown(db: Session, brand_id: str, start: date, end: date) -> list[dict]:
    rows = (
        db.query(
            AdAccount.platform,
            func.sum(AdMetricDaily.spend).label("spend"),
            func.sum(AdMetricDaily.conversions).label("conversions"),
        )
        .join(AdAccount, AdAccount.id == AdMetricDaily.ad_account_id)
        .filter(AdMetricDaily.brand_id == brand_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
        .group_by(AdAccount.platform)
        .all()
    )
    return [
        {
            "platform": r.platform.value,
            "spend": round(r.spend or 0, 2),
            "conversions": int(r.conversions or 0),
            "cac": _cac(r.spend or 0, r.conversions or 0),
            "roas": None,
        }
        for r in rows
    ]


def get_campaign_breakdown(db: Session, brand_id: str, start: date, end: date) -> list[dict]:
    rows = (
        db.query(
            AdMetricDaily.campaign_name,
            AdAccount.platform,
            func.sum(AdMetricDaily.spend).label("spend"),
            func.sum(AdMetricDaily.conversions).label("conversions"),
            func.sum(AdMetricDaily.revenue).label("revenue"),
        )
        .join(AdAccount, AdAccount.id == AdMetricDaily.ad_account_id)
        .filter(AdMetricDaily.brand_id == brand_id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
        .group_by(AdMetricDaily.campaign_name, AdAccount.platform)
        .order_by(func.sum(AdMetricDaily.spend).desc())
        .all()
    )
    return [
        {
            "campaign_name": r.campaign_name,
            "platform": r.platform.value,
            "spend": round(r.spend or 0, 2),
            "conversions": int(r.conversions or 0),
            "cac": _cac(r.spend or 0, r.conversions or 0),
            "roas": _roas(r.revenue or 0, r.spend or 0),
        }
        for r in rows
    ]


def get_trend_alert(db: Session, brand: Brand, window_days: int = 7) -> dict:
    """Flags when CAC crosses the brand-defined threshold (PRD 6.1)."""
    today = date.today()
    current_start = today - timedelta(days=window_days - 1)
    previous_start = current_start - timedelta(days=window_days)
    previous_end = current_start - timedelta(days=1)

    def window_cac(start: date, end: date) -> float | None:
        agg = (
            db.query(func.sum(AdMetricDaily.spend), func.sum(AdMetricDaily.conversions))
            .filter(AdMetricDaily.brand_id == brand.id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
            .one()
        )
        spend, conversions = agg[0] or 0, agg[1] or 0
        return _cac(spend, conversions)

    current_cac = window_cac(current_start, today)
    previous_cac = window_cac(previous_start, previous_end)

    change_pct = None
    triggered = False
    message = "CAC is stable within your alert threshold."

    if current_cac is not None and previous_cac is not None and previous_cac > 0:
        change_pct = round(((current_cac - previous_cac) / previous_cac) * 100, 1)
        if change_pct >= brand.cac_alert_threshold_pct:
            triggered = True
            message = (
                f"Blended CAC rose {change_pct}% over the last {window_days} days "
                f"(₹{previous_cac} → ₹{current_cac}), crossing your {brand.cac_alert_threshold_pct}% threshold."
            )
        elif change_pct <= -brand.cac_alert_threshold_pct:
            message = f"Blended CAC improved {abs(change_pct)}% over the last {window_days} days. Nice work."

    return {
        "triggered": triggered,
        "current_cac": current_cac,
        "previous_cac": previous_cac,
        "change_pct": change_pct,
        "threshold_pct": brand.cac_alert_threshold_pct,
        "message": message,
    }


def get_category_benchmark(db: Session, brand: Brand, start: date, end: date) -> dict | None:
    """Anonymized, aggregated category comparison (PRD 6.1)."""
    if not brand.category:
        return None

    peer_brand_ids = [
        b.id for b in db.query(Brand.id).filter(Brand.category == brand.category, Brand.id != brand.id).all()
    ]
    if not peer_brand_ids:
        return None

    agg = (
        db.query(func.sum(AdMetricDaily.spend), func.sum(AdMetricDaily.conversions), func.sum(AdMetricDaily.revenue))
        .filter(
            AdMetricDaily.brand_id.in_(peer_brand_ids),
            AdMetricDaily.date >= start,
            AdMetricDaily.date <= end,
        )
        .one()
    )
    spend, conversions, revenue = agg[0] or 0, agg[1] or 0, agg[2] or 0
    avg_cac = _cac(spend, conversions) or 0.0
    avg_roas = _roas(revenue, spend) or 0.0

    brand_agg = (
        db.query(func.sum(AdMetricDaily.spend), func.sum(AdMetricDaily.conversions), func.sum(AdMetricDaily.revenue))
        .filter(AdMetricDaily.brand_id == brand.id, AdMetricDaily.date >= start, AdMetricDaily.date <= end)
        .one()
    )
    b_spend, b_conversions, b_revenue = brand_agg[0] or 0, brand_agg[1] or 0, brand_agg[2] or 0

    return {
        "category": brand.category,
        "avg_cac": avg_cac,
        "avg_roas": avg_roas,
        "brand_cac": _cac(b_spend, b_conversions),
        "brand_roas": _roas(b_revenue, b_spend),
    }


def get_dashboard_summary(db: Session, brand: Brand, days: int = DEFAULT_SYNC_DAYS) -> dict:
    end = date.today()
    start = end - timedelta(days=days - 1)

    daily_series = get_daily_series(db, brand.id, start, end)
    total_spend = round(sum(d["spend"] for d in daily_series), 2)
    total_conversions = sum(d["conversions"] for d in daily_series)
    total_revenue = round(sum(d["revenue"] for d in daily_series), 2)

    return {
        "total_spend": total_spend,
        "total_conversions": total_conversions,
        "total_revenue": total_revenue,
        "blended_cac": _cac(total_spend, total_conversions),
        "blended_roas": _roas(total_revenue, total_spend),
        "daily_series": daily_series,
        "by_platform": get_platform_breakdown(db, brand.id, start, end),
        "by_campaign": get_campaign_breakdown(db, brand.id, start, end),
        "trend_alert": get_trend_alert(db, brand),
        "benchmark": get_category_benchmark(db, brand, start, end),
    }
