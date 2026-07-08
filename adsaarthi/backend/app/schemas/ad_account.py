from app.models.enums import AdAccountStatus, AdPlatform
from pydantic import ConfigDict, BaseModel


class AdAccountConnectRequest(BaseModel):
    platform: AdPlatform
    # In a real OAuth flow this would be an authorization `code` exchanged
    # server-side for a token. MVP mock connector accepts a display name
    # directly so the platform is demoable without live API credentials.
    display_name: str
    external_account_id: str | None = None


class AdAccountOut(BaseModel):
    id: str
    platform: AdPlatform
    display_name: str
    external_account_id: str
    status: AdAccountStatus
    last_synced_at: str | None

    model_config = ConfigDict(from_attributes=True)
