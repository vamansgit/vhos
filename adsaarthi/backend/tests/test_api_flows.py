from app.models.enums import AdPlatform, InfluencerCategory
from app.models.influencer import Influencer


def _seed_influencer(db_session, **overrides) -> Influencer:
    defaults = dict(
        handle="testcreator",
        display_name="Test Creator",
        platform=AdPlatform.META,
        category=InfluencerCategory.WELLNESS,
        follower_count=40_000,
        engagement_rate_pct=6.0,
        posting_consistency_score=85.0,
        audience_interests="wellness, skincare",
        audience_geography="India",
        indicative_price_min=8_000,
        indicative_price_max=20_000,
        historical_avg_engagement_pct=6.0,
        historical_campaigns_count=3,
    )
    defaults.update(overrides)
    influencer = Influencer(**defaults)
    db_session.add(influencer)
    db_session.commit()
    return influencer


def test_connect_ad_account_and_dashboard_populates(client, auth_headers):
    connect = client.post(
        "/api/ad-accounts",
        json={"platform": "meta", "display_name": "My Meta Ads"},
        headers=auth_headers,
    )
    assert connect.status_code == 201
    assert connect.json()["status"] == "connected"

    dashboard = client.get("/api/analytics/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["total_spend"] > 0
    assert len(body["daily_series"]) > 0


def test_campaign_brief_to_match_to_content_flow(client, auth_headers, db_session):
    _seed_influencer(db_session)

    brief_response = client.post(
        "/api/campaigns",
        json={
            "objective": "launch",
            "target_audience_interests": "wellness, skincare",
            "target_audience_geography": "India",
            "content_format": "reels",
            "total_budget": 50000,
        },
        headers=auth_headers,
    )
    assert brief_response.status_code == 201
    brief_id = brief_response.json()["id"]

    match_response = client.post(f"/api/campaigns/{brief_id}/match", headers=auth_headers)
    assert match_response.status_code == 200
    matches = match_response.json()
    assert len(matches) >= 1
    assert matches[0]["status"] == "pending_review"

    match_id = matches[0]["id"]
    review = client.patch(
        f"/api/campaigns/{brief_id}/matches/{match_id}",
        json={"status": "approved"},
        headers=auth_headers,
    )
    assert review.status_code == 200
    assert review.json()["status"] == "approved"
    assert review.json()["approved_bid"] == matches[0]["recommended_bid"]

    content = client.get("/api/content", headers=auth_headers)
    assert content.status_code == 200
    assert any(d["type"] == "creator_brief" for d in content.json())


def test_influencer_directory_filter_by_category(client, auth_headers, db_session):
    _seed_influencer(db_session, handle="wellness_creator", category=InfluencerCategory.WELLNESS)
    _seed_influencer(db_session, handle="tech_creator", category=InfluencerCategory.TECH, platform=AdPlatform.YOUTUBE)

    response = client.get("/api/influencers?category=wellness", headers=auth_headers)
    assert response.status_code == 200
    handles = [i["handle"] for i in response.json()]
    assert "wellness_creator" in handles
    assert "tech_creator" not in handles


def test_content_studio_blog_generation(client, auth_headers):
    response = client.post(
        "/api/content/blog",
        json={"topic": "Vitamin C Serum Benefits", "keywords": ["vitamin c", "skincare"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "blog"
    assert "Vitamin C Serum Benefits" in body["title"]


def test_content_studio_ad_copy_generates_per_platform(client, auth_headers):
    response = client.post(
        "/api/content/ad-copy",
        json={"product_or_offer": "Vitamin C Serum", "platforms": ["instagram", "google_search"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    drafts = response.json()
    assert {d["platform_variant"] for d in drafts} == {"instagram", "google_search"}


def test_budget_recommendation_endpoint(client, auth_headers):
    response = client.get("/api/budget/recommendation", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["trend"] in {"improving", "worsening", "stable"}


def test_marketer_cannot_invite_users(client, db_session):
    signup = client.post(
        "/api/auth/signup",
        json={
            "brand_name": "RBAC Brand",
            "full_name": "Owner",
            "email": "rbac-owner@brand.com",
            "password": "password123",
        },
    )
    owner_headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}

    invite = client.post(
        "/api/brands/me/users",
        json={
            "email": "marketer@brand.com",
            "full_name": "Marketer",
            "password": "password123",
            "role": "marketer",
        },
        headers=owner_headers,
    )
    assert invite.status_code == 201

    marketer_login = client.post(
        "/api/auth/login-json", json={"email": "marketer@brand.com", "password": "password123"}
    )
    marketer_headers = {"Authorization": f"Bearer {marketer_login.json()['access_token']}"}

    forbidden = client.post(
        "/api/brands/me/users",
        json={
            "email": "another@brand.com",
            "full_name": "Another",
            "password": "password123",
            "role": "content_manager",
        },
        headers=marketer_headers,
    )
    assert forbidden.status_code == 403
