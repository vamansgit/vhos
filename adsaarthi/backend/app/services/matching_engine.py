"""Rules/heuristics-based Auto-Match Engine (PRD 6.2, 8.1).

Ranks influencers against a campaign intent brief using a composite Fit Score
(engagement quality, audience-category overlap, posting consistency), then a
budget-constrained bid recommender allocates spend across the shortlist,
favoring a macro + micro portfolio mix. Deliberately rules-based for MVP;
the PRD calls for upgrading to an ML ranking/bid-optimization model once
outcome data accumulates (section 8.1) — this module is the seam where that
model would plug in behind the same `generate_shortlist` interface.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.campaign import CampaignBrief
from app.models.enums import AdPlatform, ContentFormat
from app.models.influencer import Influencer

MACRO_FOLLOWER_THRESHOLD = 100_000
DEFAULT_SHORTLIST_SIZE = 10
MIN_FIT_SCORE = 20.0

_FORMAT_TO_PLATFORM = {
    ContentFormat.REELS: AdPlatform.META,
    ContentFormat.STATIC_POST: AdPlatform.META,
    ContentFormat.YOUTUBE_SHORTS: AdPlatform.YOUTUBE,
    ContentFormat.YOUTUBE_LONG_FORM: AdPlatform.YOUTUBE,
}

# Engagement rate at/above this is treated as excellent (scores ~100).
_ENGAGEMENT_CEILING_PCT = 8.0


@dataclass
class ScoredMatch:
    influencer: Influencer
    fit_score: float
    engagement_quality_score: float
    audience_overlap_score: float
    consistency_score: float
    reason: str
    tier: str


def _tokenize(*values: str | None) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        if not value:
            continue
        tokens.update(t.strip().lower() for t in value.replace("/", ",").split(",") if t.strip())
    return tokens


def _engagement_quality_score(influencer: Influencer) -> float:
    blended = (influencer.engagement_rate_pct * 0.6) + (influencer.historical_avg_engagement_pct * 0.4)
    return round(min(100.0, (blended / _ENGAGEMENT_CEILING_PCT) * 100), 1)


def _audience_overlap_score(brief: CampaignBrief, influencer: Influencer) -> float:
    """Weights interest/category alignment above geography — two influencers
    targeting the same country shouldn't score similarly to one another just
    because they share a market; the differentiator is audience *fit*."""
    brief_interest_tokens = _tokenize(brief.target_audience_interests)
    influencer_interest_tokens = _tokenize(influencer.audience_interests)

    if not brief_interest_tokens:
        interest_overlap = 0.5  # neutral score when brief under-specifies interests
    else:
        interest_overlap = len(brief_interest_tokens & influencer_interest_tokens) / len(brief_interest_tokens)

    category_bonus = 20.0 if influencer.category.value in brief_interest_tokens else 0.0

    brief_geo_tokens = _tokenize(brief.target_audience_geography)
    influencer_geo_tokens = _tokenize(influencer.audience_geography)
    geography_match = 1.0 if brief_geo_tokens and (brief_geo_tokens & influencer_geo_tokens) else 0.0

    return round(min(100.0, interest_overlap * 60 + category_bonus + geography_match * 20), 1)


def _consistency_score(influencer: Influencer) -> float:
    return round(min(100.0, influencer.posting_consistency_score), 1)


def _tier(influencer: Influencer) -> str:
    return "macro" if influencer.follower_count >= MACRO_FOLLOWER_THRESHOLD else "micro"


def _build_reason(brief: CampaignBrief, influencer: Influencer, audience_score: float, engagement_score: float) -> str:
    parts = [f"{audience_score:.0f}% audience overlap with your target segment"]
    if engagement_score >= 70:
        parts.append(f"strong {influencer.platform.value} engagement in the {influencer.category.value} category")
    elif engagement_score >= 40:
        parts.append(f"solid engagement history in the {influencer.category.value} category")
    else:
        parts.append(f"emerging engagement in the {influencer.category.value} category")
    if influencer.historical_campaigns_count > 0:
        parts.append(f"{influencer.historical_campaigns_count} past brand campaigns on record")
    return ", ".join(parts) + "."


def score_influencer(brief: CampaignBrief, influencer: Influencer) -> ScoredMatch:
    engagement_score = _engagement_quality_score(influencer)
    audience_score = _audience_overlap_score(brief, influencer)
    consistency_score = _consistency_score(influencer)

    fit_score = round(engagement_score * 0.40 + audience_score * 0.35 + consistency_score * 0.25, 1)

    return ScoredMatch(
        influencer=influencer,
        fit_score=fit_score,
        engagement_quality_score=engagement_score,
        audience_overlap_score=audience_score,
        consistency_score=consistency_score,
        reason=_build_reason(brief, influencer, audience_score, engagement_score),
        tier=_tier(influencer),
    )


def generate_shortlist(db: Session, brief: CampaignBrief, top_n: int = DEFAULT_SHORTLIST_SIZE) -> list[ScoredMatch]:
    target_platform = _FORMAT_TO_PLATFORM.get(brief.content_format)
    query = db.query(Influencer)
    if target_platform is not None:
        query = query.filter(Influencer.platform == target_platform)
    candidates = query.all()

    scored = [score_influencer(brief, inf) for inf in candidates]
    scored = [s for s in scored if s.fit_score >= MIN_FIT_SCORE]
    scored.sort(key=lambda s: s.fit_score, reverse=True)
    return scored[:top_n]


def recommend_bids(shortlist: list[ScoredMatch], total_budget: float) -> list[dict]:
    """Budget-constrained bid allocator (PRD 6.2 Step 3). Allocates spend
    proportional to fit score, clamped to each creator's indicative price
    range, favoring a macro + micro portfolio mix rather than concentrating
    the full budget on a single creator."""
    if not shortlist or total_budget <= 0:
        return []

    weight_sum = sum(s.fit_score for s in shortlist) or 1.0
    allocations: list[dict] = []
    remaining_budget = total_budget

    for match in shortlist:
        inf = match.influencer
        proportional_share = total_budget * (match.fit_score / weight_sum)
        floor = inf.indicative_price_min or proportional_share
        ceiling = inf.indicative_price_max or proportional_share
        bid = max(floor, min(ceiling, proportional_share))
        bid = round(min(bid, remaining_budget), 2)
        if bid <= 0:
            continue

        reach_capacity = inf.follower_count * (inf.engagement_rate_pct / 100) * 8  # avg views per engaged follower
        price_ceiling = inf.indicative_price_max or bid
        fulfillment_ratio = min(1.0, bid / price_ceiling) if price_ceiling else 1.0
        projected_reach = int(reach_capacity * fulfillment_ratio)

        allocations.append(
            {
                "match": match,
                "recommended_bid": bid,
                "projected_reach": max(projected_reach, 0),
            }
        )
        remaining_budget -= bid
        if remaining_budget <= 0:
            break

    return allocations
