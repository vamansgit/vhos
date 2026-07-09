import re

from app.services.nlp.base import ParsedSourcingRequest, SourcingParser

_QUANTITY_RE = re.compile(r"(\d[\d,]*)\s*(?:units?|pcs|pieces?|nos\.?|boxes|bottles|pairs)", re.IGNORECASE)
_QUANTITY_FALLBACK_RE = re.compile(r"\b(\d[\d,]{1,6})\b")
_PRICE_RE = re.compile(
    r"(?:under|below|budget(?:\s*of|\s*under)?)\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*(?:\.\d+)?)", re.IGNORECASE
)
_PRICE_FALLBACK_RE = re.compile(r"(?:₹|rs\.?|inr)\s*(\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)
_DEADLINE_RE = re.compile(r"(?:in|within)\s+(\d+)\s*(day|week|month)s?", re.IGNORECASE)
_DESTINATION_RE = re.compile(
    r"(?:to|delivered to|deliver to|in)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
)

_PACKAGING_KEYWORDS = ["box", "mailer", "label", "packaging", "pouch", "wrap", "carton", "insert"]
_LOGISTICS_KEYWORDS = ["courier", "shipping", "3pl", "freight", "delivery", "logistics", "forwarder", "cod"]

_UNIT_TO_DAYS = {"day": 1, "week": 7, "month": 30}


class HeuristicSourcingParser(SourcingParser):
    """Deterministic regex-based parser — used when no LLM key is
    configured, so Source is fully usable offline."""

    name = "heuristic"

    def parse(self, raw_text: str) -> ParsedSourcingRequest:
        text = raw_text.strip()
        lower = text.lower()

        quantity = None
        qty_match = _QUANTITY_RE.search(text)
        if qty_match:
            quantity = int(qty_match.group(1).replace(",", ""))
        else:
            fallback = _QUANTITY_FALLBACK_RE.search(text)
            if fallback:
                quantity = int(fallback.group(1).replace(",", ""))

        target_price = None
        price_match = _PRICE_RE.search(text) or _PRICE_FALLBACK_RE.search(text)
        if price_match:
            target_price = float(price_match.group(1).replace(",", ""))

        deadline_days = None
        deadline_match = _DEADLINE_RE.search(text)
        if deadline_match:
            count = int(deadline_match.group(1))
            unit = deadline_match.group(2).lower()
            deadline_days = count * _UNIT_TO_DAYS.get(unit, 1)

        destination = None
        dest_match = _DESTINATION_RE.search(text)
        if dest_match:
            destination = dest_match.group(1).strip()

        if any(k in lower for k in _PACKAGING_KEYWORDS):
            category = "packaging"
        elif any(k in lower for k in _LOGISTICS_KEYWORDS):
            category = "logistics"
        else:
            category = "product"

        parts = []
        parts.append(f"a {category} sourcing request")
        if quantity:
            parts.append(f"for {quantity:,} units")
        if target_price:
            parts.append(f"under ₹{target_price:g}/unit")
        if destination:
            parts.append(f"delivered to {destination}")
        if deadline_days:
            parts.append(f"within {deadline_days} days")
        confirmation_line = "Got it — " + " ".join(parts) + ". Searching now."

        return ParsedSourcingRequest(
            category=category,
            quantity=quantity,
            target_price=target_price,
            destination=destination,
            deadline_days=deadline_days,
            spec_attributes={"raw_text": text},
            confirmation_line=confirmation_line,
        )
