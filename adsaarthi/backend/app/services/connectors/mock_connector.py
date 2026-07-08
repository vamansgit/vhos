import hashlib
import random
from datetime import date, timedelta

from app.services.connectors.base import AdConnector, RawDailyMetric

_CAMPAIGN_NAMES = {
    "meta": ["Launch - Reels Awareness", "Retargeting - Website Visitors", "Prospecting - Lookalike 1%"],
    "youtube": ["Brand Awareness - Skippable In-Stream", "Shorts - Product Demo", "Search - Branded Keywords"],
    "google_ads": ["Search - Category Keywords", "Performance Max - Catalog"],
}


class MockConnector(AdConnector):
    """Deterministic synthetic data generator used when no live OAuth token is
    configured for a platform, so the product is fully demoable and testable
    without real Meta/Google credentials. Same account id + date always
    produces the same numbers (seeded), and CAC trends gently upward over the
    window to make trend alerts and the budget optimizer observable.
    """

    def __init__(self, platform: str):
        self.platform = platform

    def fetch_daily_metrics(
        self, external_account_id: str, token_reference: str | None, start: date, end: date
    ) -> list[RawDailyMetric]:
        campaigns = _CAMPAIGN_NAMES.get(self.platform, ["General Campaign"])
        rows: list[RawDailyMetric] = []
        total_days = max((end - start).days, 1)

        for day_offset in range((end - start).days + 1):
            current = start + timedelta(days=day_offset)
            drift = 1.0 + (day_offset / total_days) * 0.35  # gentle upward CAC drift toward `end`

            for campaign_name in campaigns:
                seed_key = f"{external_account_id}|{campaign_name}|{current.isoformat()}"
                seed = int(hashlib.sha256(seed_key.encode()).hexdigest(), 16) % (2**32)
                rng = random.Random(seed)

                base_spend = rng.uniform(800, 4000)
                spend = round(base_spend, 2)
                impressions = int(spend * rng.uniform(35, 60))
                clicks = int(impressions * rng.uniform(0.008, 0.025))
                conv_rate = rng.uniform(0.01, 0.035) / drift
                conversions = max(0, int(clicks * conv_rate))
                revenue = round(conversions * rng.uniform(900, 2200), 2)

                rows.append(
                    RawDailyMetric(
                        date=current,
                        campaign_name=campaign_name,
                        spend=spend,
                        impressions=impressions,
                        clicks=clicks,
                        conversions=conversions,
                        revenue=revenue,
                    )
                )
        return rows
