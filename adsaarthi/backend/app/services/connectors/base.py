from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RawDailyMetric:
    date: date
    campaign_name: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float


class ConnectorNotConfiguredError(RuntimeError):
    """Raised when a live platform connector is used without OAuth credentials."""


class AdConnector(ABC):
    """Read-only interface every ad platform integration implements.

    MVP scope is read-only (PRD 8.3): no ad account passwords are ever stored,
    only a token reference the connector uses to call the official platform API.
    """

    platform: str

    @abstractmethod
    def fetch_daily_metrics(
        self, external_account_id: str, token_reference: str | None, start: date, end: date
    ) -> list[RawDailyMetric]:
        raise NotImplementedError
