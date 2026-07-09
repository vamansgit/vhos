from pydantic import BaseModel, ConfigDict


class LedgerDailyPoint(BaseModel):
    date: str
    revenue: float
    cogs: float
    expenses: float
    ad_spend: float


class FinanceDashboard(BaseModel):
    revenue: float
    cogs: float
    expenses: float
    ad_spend: float
    gross_profit: float
    gross_margin_pct: float | None
    net_profit: float
    cash_position: float
    daily_series: list[LedgerDailyPoint]


class TaxProfileOut(BaseModel):
    gstin: str | None
    state: str | None
    applicable_schemes: str | None

    model_config = ConfigDict(from_attributes=True)
