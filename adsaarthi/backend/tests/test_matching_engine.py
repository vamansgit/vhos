from app.models.campaign import CampaignBrief
from app.models.enums import AdPlatform, CampaignObjective, ContentFormat, InfluencerCategory
from app.models.influencer import Influencer
from app.services.matching_engine import generate_shortlist, recommend_bids, score_influencer


def _make_brief(**overrides) -> CampaignBrief:
    defaults = dict(
        brand_id="brand-1",
        objective=CampaignObjective.LAUNCH,
        target_audience_interests="wellness, skincare",
        target_audience_geography="India",
        content_format=ContentFormat.REELS,
        total_budget=100_000,
    )
    defaults.update(overrides)
    return CampaignBrief(**defaults)


def _make_influencer(**overrides) -> Influencer:
    defaults = dict(
        handle="creator1",
        display_name="Creator One",
        platform=AdPlatform.META,
        category=InfluencerCategory.WELLNESS,
        follower_count=50_000,
        engagement_rate_pct=5.0,
        posting_consistency_score=80.0,
        audience_interests="wellness, self-care",
        audience_geography="India",
        indicative_price_min=10_000,
        indicative_price_max=25_000,
        historical_avg_engagement_pct=5.0,
        historical_campaigns_count=5,
    )
    defaults.update(overrides)
    return Influencer(**defaults)


def test_wellness_influencer_scores_higher_than_unrelated_category():
    brief = _make_brief()
    on_category = _make_influencer(category=InfluencerCategory.WELLNESS, audience_interests="wellness, self-care")
    off_category = _make_influencer(
        handle="creator2", category=InfluencerCategory.TECH, audience_interests="gadgets, tech reviews"
    )

    on_score = score_influencer(brief, on_category)
    off_score = score_influencer(brief, off_category)

    assert on_score.audience_overlap_score > off_score.audience_overlap_score


def test_generate_shortlist_filters_by_platform_and_min_score(db_session):
    brief = _make_brief(content_format=ContentFormat.REELS)  # -> META platform
    db_session.add(brief)

    meta_influencer = _make_influencer(handle="meta_creator")
    youtube_influencer = _make_influencer(
        handle="yt_creator", platform=AdPlatform.YOUTUBE, engagement_rate_pct=9.0
    )
    db_session.add_all([meta_influencer, youtube_influencer])
    db_session.commit()

    shortlist = generate_shortlist(db_session, brief)

    assert all(s.influencer.platform == AdPlatform.META for s in shortlist)
    assert any(s.influencer.handle == "meta_creator" for s in shortlist)
    assert not any(s.influencer.handle == "yt_creator" for s in shortlist)


def test_shortlist_is_ranked_descending_by_fit_score(db_session):
    brief = _make_brief()
    db_session.add(brief)

    strong = _make_influencer(handle="strong", engagement_rate_pct=8.0, posting_consistency_score=95.0)
    weak = _make_influencer(handle="weak", engagement_rate_pct=1.0, posting_consistency_score=30.0)
    db_session.add_all([strong, weak])
    db_session.commit()

    shortlist = generate_shortlist(db_session, brief)

    scores = [s.fit_score for s in shortlist]
    assert scores == sorted(scores, reverse=True)
    assert shortlist[0].influencer.handle == "strong"


def test_recommend_bids_respects_total_budget():
    brief = _make_brief(total_budget=50_000)
    influencers = [
        _make_influencer(handle=f"creator{i}", indicative_price_min=20_000, indicative_price_max=40_000)
        for i in range(4)
    ]
    shortlist = [score_influencer(brief, inf) for inf in influencers]

    allocations = recommend_bids(shortlist, brief.total_budget)

    total_allocated = sum(a["recommended_bid"] for a in allocations)
    assert total_allocated <= brief.total_budget + 0.01


def test_recommend_bids_clamps_to_indicative_price_range():
    brief = _make_brief(total_budget=1_000_000)
    influencer = _make_influencer(indicative_price_min=10_000, indicative_price_max=15_000)
    shortlist = [score_influencer(brief, influencer)]

    allocations = recommend_bids(shortlist, brief.total_budget)

    assert len(allocations) == 1
    assert 10_000 <= allocations[0]["recommended_bid"] <= 15_000


def test_recommend_bids_empty_shortlist_returns_empty():
    assert recommend_bids([], 100_000) == []


def test_recommend_bids_zero_budget_returns_empty():
    brief = _make_brief()
    influencer = _make_influencer()
    shortlist = [score_influencer(brief, influencer)]
    assert recommend_bids(shortlist, 0) == []
