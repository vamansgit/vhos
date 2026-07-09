from datetime import date

from pydantic import BaseModel


class DailyPoint(BaseModel):
    date: date
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    cac: float | None
    roas: float | None


class PlatformBreakdown(BaseModel):
    platform: str
    spend: float
    conversions: int
    cac: float | None
    roas: float | None


class CampaignBreakdown(BaseModel):
    campaign_name: str
    platform: str
    spend: float
    conversions: int
    cac: float | None
    roas: float | None


class TrendAlert(BaseModel):
    triggered: bool
    current_cac: float | None
    previous_cac: float | None
    change_pct: float | None
    threshold_pct: float
    message: str


class CategoryBenchmark(BaseModel):
    category: str
    avg_cac: float
    avg_roas: float
    brand_cac: float | None
    brand_roas: float | None


class DashboardSummary(BaseModel):
    total_spend: float
    total_conversions: int
    total_revenue: float
    blended_cac: float | None
    blended_roas: float | None
    daily_series: list[DailyPoint]
    by_platform: list[PlatformBreakdown]
    by_campaign: list[CampaignBreakdown]
    trend_alert: TrendAlert
    benchmark: CategoryBenchmark | None
