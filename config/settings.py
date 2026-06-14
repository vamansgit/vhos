from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "VHOS v2.4"
    debug: bool = False
    log_level: str = "INFO"

    # Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    intent_model: str = "claude-haiku-4-5-20251001"
    reasoning_model: str = "claude-sonnet-4-6"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 3600

    # Auth
    jwt_secret: str = Field(default="vhos-dev-secret-change-in-prod")
    capability_token_secret: str = Field(default="vhos-cap-token-secret")
    token_ttl_seconds: int = 900

    # FHIR
    fhir_base_url: str = "http://localhost:8080/fhir"
    fhir_client_id: str = ""
    fhir_client_secret: str = ""
    use_demo_data: bool = True  # Use demo Excel data when FHIR unavailable

    # Demo data
    demo_data_dir: str = "demo_data"

    # Telephony
    exotel_sid: str = ""
    exotel_token: str = ""
    twilio_sid: str = ""
    twilio_token: str = ""

    # Messaging
    whatsapp_token: str = ""
    sms_gateway_key: str = ""

    # TTS/STT
    sarvam_api_key: str = ""
    elevenlabs_api_key: str = ""
    deepgram_api_key: str = ""

    # Vector store (Qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # Audit
    audit_hmac_secret: str = Field(default="vhos-audit-secret-change-in-prod")

    # Rate limits
    outreach_rate_limit_per_hour: int = 50
    campaign_rate_limit_per_hour: int = 200


settings = Settings()
