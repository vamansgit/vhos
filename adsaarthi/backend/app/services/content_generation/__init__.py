from app.config import get_settings
from app.services.content_generation.base import ContentProvider
from app.services.content_generation.template_provider import TemplateProvider

_provider: ContentProvider | None = None


def get_content_provider() -> ContentProvider:
    global _provider
    if _provider is not None:
        return _provider

    settings = get_settings()
    if settings.anthropic_api_key:
        from app.services.content_generation.llm_provider import LLMProvider

        try:
            _provider = LLMProvider()
            return _provider
        except Exception:
            pass

    _provider = TemplateProvider()
    return _provider


__all__ = ["get_content_provider", "ContentProvider"]
