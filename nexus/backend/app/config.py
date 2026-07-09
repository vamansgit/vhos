from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEXUS_", env_file=".env", extra="ignore")

    app_name: str = "Nexus"
    environment: str = "development"

    database_url: str = "sqlite:///./nexus.db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    # AI layer (NL parsing, orchestrator intent classification, site-copy
    # generation). Falls back to deterministic heuristics/templates when no
    # key is configured, so the platform is fully demoable offline.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    # Storefront/payment/B2B network connectors — leave unset to use mock
    # connectors (see services/connectors).
    shopify_api_key: str | None = None
    razorpay_key_id: str | None = None

    document_storage_dir: str = "./document_vault"

    cors_origins: list[str] = ["http://localhost:5174", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
