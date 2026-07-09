"""Seeds demo data: a sample brand, connected mock ad accounts with 90 days
of synced metrics, an influencer directory, and one auto-matched campaign —
enough to explore every MVP module immediately after `python -m app.seed`.
"""

import random

from app.database import Base, SessionLocal, engine
from app.models.ad_account import AdAccount
from app.models.brand import Brand
from app.models.enums import (
    AdAccountStatus,
    AdPlatform,
    CampaignObjective,
    ContentFormat,
    InfluencerCategory,
    UserRole,
)
from app.models.influencer import Influencer
from app.models.campaign import CampaignBrief
from app.models.user import User
from app.security import hash_password
from app.services.analytics_service import sync_ad_account
from app.services.campaign_service import run_auto_match

DEMO_EMAIL = "demo@adsaarthi.app"
DEMO_PASSWORD = "demo12345"

_HANDLES = [
    ("glow.with.aisha", "beauty", "meta", 45000),
    ("meera.skincare", "beauty", "meta", 120000),
    ("thefitguru.in", "fitness", "meta", 32000),
    ("wellnesswithriya", "wellness", "youtube", 88000),
    ("kabirs.kitchen", "food", "youtube", 210000),
    ("homedecor.by.tanvi", "home", "meta", 27000),
    ("techtalks.rohan", "tech", "youtube", 340000),
    ("mommy.diaries.in", "parenting", "meta", 61000),
    ("budgetwithpriya", "finance", "meta", 19000),
    ("wanderlust.arjun", "travel", "youtube", 150000),
    ("streetstyle.nisha", "fashion", "meta", 73000),
    ("yogawithkiran", "wellness", "meta", 41000),
    ("gymrat.dev", "fitness", "youtube", 56000),
    ("bakewithbela", "food", "meta", 22000),
    ("minimalhome.co", "home", "meta", 38000),
    ("gadgetguide.in", "tech", "meta", 95000),
    ("newmom.notes", "parenting", "youtube", 44000),
    ("moneymindset.raj", "finance", "youtube", 67000),
    ("solotravel.diaries", "travel", "meta", 29000),
    ("couture.by.zara", "fashion", "youtube", 180000),
]

_STYLES = {
    "beauty": "before/after transformation Reels with soft natural lighting",
    "fitness": "high-energy workout clips with on-screen form tips",
    "wellness": "calm talking-head videos with routine breakdowns",
    "food": "fast-cut recipe Reels with satisfying overhead shots",
    "home": "aesthetic room tours and styling tips",
    "tech": "unboxing and honest first-impressions reviews",
    "parenting": "relatable day-in-the-life vlogs",
    "finance": "whiteboard-style explainer videos",
    "travel": "cinematic destination highlight reels",
    "fashion": "outfit-of-the-day try-on hauls",
}


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Brand).filter(Brand.name == "Glow Wellness Co").first():
            print("Demo data already present — skipping.")
            return

        brand = Brand(
            name="Glow Wellness Co",
            category="wellness",
            target_audience="women 22-35, urban India, interested in skincare and self-care",
            brand_voice="warm, encouraging, and jargon-free",
        )
        db.add(brand)
        db.flush()

        owner = User(
            brand_id=brand.id,
            email=DEMO_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Ritu Sharma",
            role=UserRole.OWNER,
        )
        db.add(owner)

        rng = random.Random(42)
        for handle, category, platform, followers in _HANDLES:
            engagement = round(rng.uniform(1.5, 9.5), 2)
            price_min = round(followers * rng.uniform(0.8, 1.5), -2)
            price_max = round(price_min * rng.uniform(1.4, 2.2), -2)
            db.add(
                Influencer(
                    handle=handle,
                    display_name=handle.replace(".", " ").title(),
                    platform=AdPlatform(platform),
                    category=InfluencerCategory(category),
                    follower_count=followers,
                    engagement_rate_pct=engagement,
                    posting_consistency_score=round(rng.uniform(55, 98), 1),
                    audience_age_range=rng.choice(["18-24", "22-35", "25-40", "18-34"]),
                    audience_geography="India, Tier 1 & 2 cities",
                    audience_interests=f"{category}, self-care, lifestyle",
                    indicative_price_min=price_min,
                    indicative_price_max=price_max,
                    top_content_style=_STYLES.get(category, "engaging short-form video"),
                    historical_avg_engagement_pct=round(engagement * rng.uniform(0.85, 1.1), 2),
                    historical_campaigns_count=rng.randint(0, 24),
                    opted_in=rng.random() > 0.5,
                )
            )
        db.commit()

        meta_account = AdAccount(
            brand_id=brand.id,
            platform=AdPlatform.META,
            display_name="Glow Wellness Co — Meta Ads",
            external_account_id="demo-meta-001",
            status=AdAccountStatus.CONNECTED,
        )
        youtube_account = AdAccount(
            brand_id=brand.id,
            platform=AdPlatform.YOUTUBE,
            display_name="Glow Wellness Co — YouTube/Google Ads",
            external_account_id="demo-youtube-001",
            status=AdAccountStatus.CONNECTED,
        )
        db.add_all([meta_account, youtube_account])
        db.commit()
        db.refresh(meta_account)
        db.refresh(youtube_account)

        sync_ad_account(db, meta_account)
        sync_ad_account(db, youtube_account)

        brief = CampaignBrief(
            brand_id=brand.id,
            objective=CampaignObjective.LAUNCH,
            target_audience_age="22-35",
            target_audience_gender="female",
            target_audience_geography="India, Tier 1 & 2 cities",
            target_audience_interests="wellness, self-care, skincare",
            desired_reach=250000,
            content_format=ContentFormat.REELS,
            total_budget=150000,
            notes="Launch campaign for our new vitamin-C serum.",
        )
        db.add(brief)
        db.commit()
        db.refresh(brief)

        run_auto_match(db, brand, brief)

        print("Seed complete.")
        print(f"  Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  Brand: {brand.name} ({brand.id})")
        print(f"  Sample campaign brief: {brief.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
