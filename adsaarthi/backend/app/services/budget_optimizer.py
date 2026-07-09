"""Rules-based Budget & Channel Optimizer (PRD 6.5) — a transparent advisory
layer, not a black-box auto-optimizer. Nudges the brand toward organic
content or a different influencer tier when paid CAC trends worse, and
suggests a starting budget split across paid/influencer/content."""

from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.budget import BudgetRecommendation
from app.services.analytics_service import get_trend_alert

# Category benchmark starting splits (paid %, influencer %, content %).
_CATEGORY_SPLITS: dict[str, tuple[float, float, float]] = {
    "beauty": (55.0, 30.0, 15.0),
    "fashion": (55.0, 30.0, 15.0),
    "wellness": (50.0, 30.0, 20.0),
    "food": (55.0, 25.0, 20.0),
    "tech": (60.0, 20.0, 20.0),
    "home": (60.0, 20.0, 20.0),
    "fitness": (50.0, 30.0, 20.0),
    "parenting": (55.0, 25.0, 20.0),
    "finance": (65.0, 15.0, 20.0),
    "travel": (55.0, 25.0, 20.0),
}
_DEFAULT_SPLIT = (60.0, 25.0, 15.0)

WORSENING_SHIFT_PCT = 10.0  # points shifted from paid toward content when CAC worsens


def generate_recommendation(db: Session, brand: Brand) -> BudgetRecommendation:
    alert = get_trend_alert(db, brand)
    paid_pct, influencer_pct, content_pct = _CATEGORY_SPLITS.get(
        (brand.category or "").lower(), _DEFAULT_SPLIT
    )

    if alert["triggered"]:
        trend = "worsening"
        shift = min(WORSENING_SHIFT_PCT, paid_pct)
        paid_pct -= shift
        content_pct += shift
        message = (
            f"Your paid CAC is trending up ({alert['message']}). Consider shifting "
            f"~{shift:.0f}% of budget toward organic content output, or testing a new "
            f"influencer tier (e.g. more micro-creators at lower cost per collaboration)."
        )
    elif alert["change_pct"] is not None and alert["change_pct"] <= -5:
        trend = "improving"
        message = f"Paid CAC is improving ({alert['message']}). Your current channel mix is working — keep it."
    else:
        trend = "stable"
        message = (
            f"CAC is stable. Suggested starting split for {brand.category or 'your category'}: "
            f"{paid_pct:.0f}% paid ads, {influencer_pct:.0f}% influencer collabs, {content_pct:.0f}% content production."
        )

    recommendation = BudgetRecommendation(
        brand_id=brand.id,
        trend=trend,
        message=message,
        suggested_paid_pct=round(paid_pct, 1),
        suggested_influencer_pct=round(influencer_pct, 1),
        suggested_content_pct=round(content_pct, 1),
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation
