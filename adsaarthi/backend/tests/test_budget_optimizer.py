from datetime import date, timedelta

from app.models.ad_account import AdAccount
from app.models.ad_metric import AdMetricDaily
from app.models.brand import Brand
from app.models.enums import AdAccountStatus, AdPlatform
from app.services.budget_optimizer import generate_recommendation


def _seed_brand_with_metrics(db_session, *, worsening: bool) -> Brand:
    brand = Brand(name="Test Brand", category="wellness", cac_alert_threshold_pct=15.0)
    db_session.add(brand)
    db_session.flush()

    account = AdAccount(
        brand_id=brand.id,
        platform=AdPlatform.META,
        display_name="Meta",
        external_account_id="acct-1",
        status=AdAccountStatus.CONNECTED,
    )
    db_session.add(account)
    db_session.flush()

    today = date.today()
    for offset in range(14):
        day = today - timedelta(days=offset)
        # Recent 7 days (offset 0-6) vs prior 7 days (offset 7-13).
        conversions = 5 if (offset < 7 and worsening) else 20
        db_session.add(
            AdMetricDaily(
                ad_account_id=account.id,
                brand_id=brand.id,
                date=day,
                campaign_name="Test Campaign",
                spend=1000.0,
                impressions=10_000,
                clicks=200,
                conversions=conversions,
                revenue=5000.0,
            )
        )
    db_session.commit()
    return brand


def test_generate_recommendation_flags_worsening_cac(db_session):
    brand = _seed_brand_with_metrics(db_session, worsening=True)

    recommendation = generate_recommendation(db_session, brand)

    assert recommendation.trend == "worsening"
    assert recommendation.suggested_content_pct > 20.0  # shifted up from the wellness baseline of 20%


def test_generate_recommendation_stable_uses_category_baseline(db_session):
    brand = _seed_brand_with_metrics(db_session, worsening=False)

    recommendation = generate_recommendation(db_session, brand)

    assert recommendation.trend == "stable"
    assert recommendation.suggested_paid_pct == 50.0
    assert recommendation.suggested_influencer_pct == 30.0
    assert recommendation.suggested_content_pct == 20.0


def test_generate_recommendation_unknown_category_uses_default_split(db_session):
    brand = Brand(name="No Category Brand", category=None)
    db_session.add(brand)
    db_session.commit()

    recommendation = generate_recommendation(db_session, brand)

    assert recommendation.suggested_paid_pct == 60.0
    assert recommendation.suggested_influencer_pct == 25.0
    assert recommendation.suggested_content_pct == 15.0
