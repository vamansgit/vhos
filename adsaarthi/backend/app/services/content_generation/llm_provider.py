import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.content_generation.base import ContentProvider

_SYSTEM_PROMPT = (
    "You are AdSaarthi's content assistant for small D2C brands in India. "
    "Write concise, on-brand marketing content. Always return output as plain "
    "text with a first line 'TITLE: <title>' followed by a blank line and the body."
)


class LLMProvider(ContentProvider):
    """Anthropic-backed generator, used when ADSAARTHI_ANTHROPIC_API_KEY is set."""

    name = "llm"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("Anthropic API key not configured")
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _complete(self, user_prompt: str, max_tokens: int = 1024) -> dict:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return _parse_title_body(text)

    def generate_blog(self, topic: str, keywords: list[str], brand_voice: str | None) -> dict:
        prompt = (
            f"Write a short SEO-aware blog post about '{topic}'. "
            f"Target keywords: {', '.join(keywords) or topic}. "
            f"Brand voice: {brand_voice or 'friendly and direct'}. "
            f"Include an intro, 2-3 subsections with headers, and a call to action."
        )
        return self._complete(prompt, max_tokens=1200)

    def generate_ad_copy(self, product_or_offer: str, platform: str, brand_voice: str | None) -> dict:
        prompt = (
            f"Write 3 short ad copy variants (headline + caption) for '{product_or_offer}' on {platform}. "
            f"Brand voice: {brand_voice or 'friendly and direct'}. Number each variant."
        )
        return self._complete(prompt, max_tokens=500)

    def generate_creator_brief(
        self,
        brand_name: str,
        brand_voice: str | None,
        campaign_objective: str,
        influencer_handle: str,
        influencer_style: str | None,
        content_format: str,
    ) -> dict:
        prompt = (
            f"Write a creator content brief for influencer @{influencer_handle} promoting {brand_name}. "
            f"Campaign objective: {campaign_objective}. Content format: {content_format}. "
            f"Brand voice: {brand_voice or 'friendly and direct'}. "
            f"Creator's usual content style: {influencer_style or 'not specified'}. "
            f"Include a creative concept, talking points, and deliverables."
        )
        return self._complete(prompt, max_tokens=700)

    def generate_image_concept(self, prompt: str, image_format: str, brand_name: str) -> dict:
        full_prompt = (
            f"Write a structured visual creative brief (not an image) for a {image_format} for brand "
            f"'{brand_name}', based on this concept: {prompt}. Include composition notes and suggested "
            f"copy overlay."
        )
        return self._complete(full_prompt, max_tokens=400)


def _parse_title_body(text: str) -> dict:
    lines = text.strip().splitlines()
    if lines and lines[0].upper().startswith("TITLE:"):
        title = lines[0].split(":", 1)[1].strip()
        body = "\n".join(lines[1:]).strip()
    else:
        title = lines[0].strip() if lines else "Untitled Draft"
        body = text.strip()
    return {"title": title, "body": body}
