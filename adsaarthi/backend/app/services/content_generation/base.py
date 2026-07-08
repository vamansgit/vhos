from abc import ABC, abstractmethod


class ContentProvider(ABC):
    """Pluggable content generation backend. LLMProvider (Anthropic) is used
    when an API key is configured; TemplateProvider is a deterministic
    fallback so the AI Content Studio (PRD 6.4) is fully usable offline/in
    tests without external API access.
    """

    name: str

    @abstractmethod
    def generate_blog(self, topic: str, keywords: list[str], brand_voice: str | None) -> dict:
        """Returns {title, body}."""

    @abstractmethod
    def generate_ad_copy(self, product_or_offer: str, platform: str, brand_voice: str | None) -> dict:
        """Returns {title, body} — title is the primary headline, body holds
        the full set of headline/caption variants for the platform."""

    @abstractmethod
    def generate_creator_brief(
        self,
        brand_name: str,
        brand_voice: str | None,
        campaign_objective: str,
        influencer_handle: str,
        influencer_style: str | None,
        content_format: str,
    ) -> dict:
        """Per-creator tailored content brief + creative concept (PRD 6.2 Step 4). Returns {title, body}."""

    @abstractmethod
    def generate_image_concept(self, prompt: str, image_format: str, brand_name: str) -> dict:
        """MVP produces a structured visual-direction brief (dimensions, brand
        colors/logo placement, composition notes) rather than a binary image —
        this is the seam where a real image generation API plugs in later.
        Returns {title, body}."""
