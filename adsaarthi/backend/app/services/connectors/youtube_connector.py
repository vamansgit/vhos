from datetime import date

import httpx

from app.config import get_settings
from app.services.connectors.base import AdConnector, ConnectorNotConfiguredError, RawDailyMetric

GOOGLE_ADS_API_BASE = "https://googleads.googleapis.com/v17"


class YouTubeConnector(AdConnector):
    """YouTube/Google Ads connector (read-only reporting scope).

    Requires a per-brand OAuth refresh token exchanged for the platform via the
    standard Google OAuth consent flow; only the resulting token reference is
    persisted (PRD 8.3 — no credential storage, token-based access only).
    """

    platform = "youtube"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.google_client_id or not settings.google_client_secret:
            raise ConnectorNotConfiguredError("Google Ads client credentials are not configured")

    def fetch_daily_metrics(
        self, external_account_id: str, token_reference: str | None, start: date, end: date
    ) -> list[RawDailyMetric]:
        if not token_reference:
            raise ConnectorNotConfiguredError("Ad account is missing an access token reference")

        query = f"""
            SELECT campaign.name, segments.date, metrics.cost_micros,
                   metrics.impressions, metrics.clicks, metrics.conversions,
                   metrics.conversions_value
            FROM campaign
            WHERE segments.date BETWEEN '{start.isoformat()}' AND '{end.isoformat()}'
        """
        url = f"{GOOGLE_ADS_API_BASE}/customers/{external_account_id}/googleAds:search"
        headers = {"Authorization": f"Bearer {token_reference}"}

        rows: list[RawDailyMetric] = []
        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=headers, json={"query": query})
            response.raise_for_status()
            payload = response.json()

        for result in payload.get("results", []):
            metrics = result.get("metrics", {})
            rows.append(
                RawDailyMetric(
                    date=date.fromisoformat(result["segments"]["date"]),
                    campaign_name=result.get("campaign", {}).get("name", "Unknown Campaign"),
                    spend=float(metrics.get("costMicros", 0)) / 1_000_000,
                    impressions=int(metrics.get("impressions", 0)),
                    clicks=int(metrics.get("clicks", 0)),
                    conversions=int(float(metrics.get("conversions", 0))),
                    revenue=float(metrics.get("conversionsValue", 0)),
                )
            )
        return rows
