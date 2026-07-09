from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ADSAARTHI_", env_file=".env", extra="ignore")

    app_name: str = "AdSaarthi"
    environment: str = "development"

    database_url: str = "sqlite:///./adsaarthi.db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    # Ad platform OAuth (read-only scopes only; see PRD 8.3 compliance notes).
    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # AI content generation. Falls back to deterministic template provider
    # when no key is configured, so the platform is fully demoable offline.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    cac_alert_default_threshold_pct: float = 15.0

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
