from datetime import date

import httpx

from app.config import get_settings
from app.services.connectors.base import AdConnector, ConnectorNotConfiguredError, RawDailyMetric

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class MetaConnector(AdConnector):
    """Meta Marketing API connector (read-only `ads_read` scope).

    Requires a per-brand OAuth access token stored as `token_reference` on the
    AdAccount (obtained via the standard Meta OAuth dialog, exchanged server-side —
    the raw token is never persisted client-side or logged).
    """

    platform = "meta"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.meta_app_id or not settings.meta_app_secret:
            raise ConnectorNotConfiguredError("Meta app credentials are not configured")

    def fetch_daily_metrics(
        self, external_account_id: str, token_reference: str | None, start: date, end: date
    ) -> list[RawDailyMetric]:
        if not token_reference:
            raise ConnectorNotConfiguredError("Ad account is missing an access token reference")

        params = {
            "access_token": token_reference,
            "level": "campaign",
            "time_range": f'{{"since":"{start.isoformat()}","until":"{end.isoformat()}"}}',
            "time_increment": 1,
            "fields": "campaign_name,spend,impressions,clicks,actions,action_values",
        }
        url = f"{GRAPH_API_BASE}/act_{external_account_id}/insights"

        rows: list[RawDailyMetric] = []
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        for entry in payload.get("data", []):
            conversions = int(_sum_action(entry.get("actions"), "offsite_conversion.purchase"))
            revenue = _sum_action(entry.get("action_values"), "offsite_conversion.purchase")
            rows.append(
                RawDailyMetric(
                    date=date.fromisoformat(entry["date_start"]),
                    campaign_name=entry.get("campaign_name", "Unknown Campaign"),
                    spend=float(entry.get("spend", 0)),
                    impressions=int(entry.get("impressions", 0)),
                    clicks=int(entry.get("clicks", 0)),
                    conversions=conversions,
                    revenue=revenue,
                )
            )
        return rows


def _sum_action(actions: list[dict] | None, action_type: str) -> float:
    if not actions:
        return 0.0
    return sum(float(a["value"]) for a in actions if a.get("action_type") == action_type)
