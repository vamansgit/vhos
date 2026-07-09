import json

import anthropic

from app.config import get_settings
from app.services.nlp.base import ParsedSourcingRequest, SourcingParser

_SYSTEM_PROMPT = """You extract structured sourcing requirements from a D2C founder's free-text ask.
Return ONLY a JSON object with keys: category (one of "product","packaging","logistics","other"),
quantity (integer or null), target_price (number or null, per-unit price in INR), destination (string or null),
deadline_days (integer or null), spec_attributes (object of any other relevant attributes like material/color/size),
confirmation_line (a single friendly sentence confirming what you understood, ending with "Searching now.")."""


class LLMSourcingParser(SourcingParser):
    """Anthropic-backed parser, used when NEXUS_ANTHROPIC_API_KEY is set."""

    name = "llm"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("Anthropic API key not configured")
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    def parse(self, raw_text: str) -> ParsedSourcingRequest:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=400,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": raw_text}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        data = json.loads(text)
        return ParsedSourcingRequest(
            category=data.get("category") or "product",
            quantity=data.get("quantity"),
            target_price=data.get("target_price"),
            destination=data.get("destination"),
            deadline_days=data.get("deadline_days"),
            spec_attributes=data.get("spec_attributes") or {},
            confirmation_line=data.get("confirmation_line") or "Got it — searching now.",
        )
