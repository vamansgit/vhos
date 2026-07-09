"""The unified conversational layer (PRD §10.1). A single chat endpoint
classifies intent and delegates to the relevant module service, returning a
structured payload plus a natural-language reply the frontend renders as a
chat bubble (with inline widgets keyed off the payload shape).

Classification is deterministic keyword-scoring — it doesn't need an LLM to
route reliably between five well-separated domains, and keeping it
heuristic makes routing testable/auditable (PRD §11). The Source module's
own NL parser (services/nlp) is what carries the LLM-vs-fallback pattern
for actually understanding a sourcing ask in depth.
"""

import re
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from app.models.brand import Brand, FounderProfile
from app.models.chat import ChatMessage
from app.models.enums import ChatRole, ModuleName
from app.services import finance_service, onboard_service, source_service
from app.services.nlp import get_sourcing_parser
from app.services.sell_service import create_store

_QUANTITY_PRICE_HINT_RE = re.compile(
    r"(\d[\d,]*\s*(?:units?|pcs|pieces?|nos\.?)\b)|(?:under|budget)\s*(?:₹|rs\.?|inr)?\s*\d",
    re.IGNORECASE,
)

_KEYWORDS: dict[ModuleName, list[str]] = {
    ModuleName.SOURCE: [
        "supplier", "source", "sourcing", "rfq", "quote", "packaging", "logistics",
        "courier", "manufactur", "vendor", "moq", "bottles", "units of", "material",
    ],
    ModuleName.SELL: [
        "store", "storefront", "site", "shop", "catalog", "homepage", "banner",
        "checkout", "payment", "shipping", "website", "product page", "publish",
    ],
    ModuleName.FINANCE: [
        "margin", "revenue", "profit", "p&l", "pnl", "tax", "gst filing", "cash",
        "how much did i make", "how much would i make", "expenses", "cogs",
    ],
    ModuleName.ONBOARD: [
        "background", "aspiration", "brand name", "target market", "founder",
        "incorporat", "document", "checklist", "gst registration", "gstin",
        "hours a week", "risk appetite",
    ],
}


@dataclass
class ChatResult:
    module: ModuleName
    reply: str
    payload: dict = field(default_factory=dict)


def classify_intent(text: str) -> ModuleName:
    lower = text.lower()
    scores = {module: sum(1 for kw in keywords if kw in lower) for module, keywords in _KEYWORDS.items()}

    # A "N units ... under ₹X" shape is a strong sourcing signal even when the
    # product noun itself isn't in our keyword list (e.g. "500 widgets").
    if _QUANTITY_PRICE_HINT_RE.search(text):
        scores[ModuleName.SOURCE] += 2

    best_module, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_module if best_score > 0 else ModuleName.NONE


def _handle_source(db: Session, brand: Brand, text: str) -> ChatResult:
    parser = get_sourcing_parser()
    parsed = parser.parse(text)
    deadline = date.today() if parsed.deadline_days is None else date.today()

    from app.models.enums import SourcingCategory
    from app.models.source import SourcingRequest

    request = SourcingRequest(
        brand_id=brand.id,
        raw_text=text,
        category=SourcingCategory(parsed.category),
        parsed_spec=parsed.spec_attributes,
        quantity=parsed.quantity,
        target_price=parsed.target_price,
        destination=parsed.destination,
        deadline=deadline if parsed.deadline_days else None,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    matches = source_service.generate_matches(db, request)
    if not matches:
        reply = (
            f"{parsed.confirmation_line} I couldn't find any matching suppliers in the "
            f"{parsed.category} category yet — try broadening the spec or check back as more suppliers join."
        )
    else:
        top = matches[0]
        reply = (
            f"{parsed.confirmation_line} Found {len(matches)} matches — top pick is "
            f"{top.supplier.name} at ~₹{top.estimated_unit_price:g}/unit ({top.reason})"
        )
    return ChatResult(
        module=ModuleName.SOURCE,
        reply=reply,
        payload={"sourcing_request_id": request.id, "match_count": len(matches)},
    )


def _handle_sell(db: Session, brand: Brand, text: str) -> ChatResult:
    lower = text.lower()
    if any(k in lower for k in ("build", "create", "make me a store", "make me a site")):
        store = create_store(db, brand)
        reply = (
            f"Your store draft is ready at {store.domain} — theme: {store.theme_config.get('style_label')}. "
            f"Razorpay and UPI are pre-enabled; confirm KYC when you're ready to go live."
        )
        return ChatResult(module=ModuleName.SELL, reply=reply, payload={"store_id": store.id})

    return ChatResult(
        module=ModuleName.SELL,
        reply="Got it — noted for your storefront. Open the Sell tab to see and confirm the change.",
        payload={},
    )


def _handle_finance(db: Session, brand: Brand, text: str) -> ChatResult:
    finance_service.sync_ledger(db, brand.id)
    summary = finance_service.get_dashboard_summary(db, brand.id)
    margin_line = f"{summary['gross_margin_pct']}% gross margin" if summary["gross_margin_pct"] is not None else "no sales yet"
    reply = (
        f"Revenue: ₹{summary['revenue']:,.0f} · COGS: ₹{summary['cogs']:,.0f} · {margin_line} · "
        f"Net: ₹{summary['net_profit']:,.0f} (last 90 days)."
    )
    return ChatResult(module=ModuleName.FINANCE, reply=reply, payload=summary)


_TARGET_MARKET_RE = re.compile(r"target market to include\s+(.+)", re.IGNORECASE)


def _handle_onboard(db: Session, brand: Brand, text: str) -> ChatResult:
    market_match = _TARGET_MARKET_RE.search(text)
    if market_match:
        addition = market_match.group(1).strip().rstrip(".")
        existing = [g.strip() for g in (brand.target_geographies or "").split(",") if g.strip()]
        if addition.lower() not in [e.lower() for e in existing]:
            existing.append(addition)
        brand.target_geographies = ", ".join(existing)
        db.commit()
        return ChatResult(
            module=ModuleName.ONBOARD,
            reply=f"Updated — your target market now includes {brand.target_geographies}.",
            payload={"target_geographies": brand.target_geographies},
        )

    profile = db.query(FounderProfile).filter(FounderProfile.brand_id == brand.id).first()
    if profile is None:
        profile = FounderProfile(brand_id=brand.id)
        db.add(profile)
        db.flush()

    if not profile.background_text:
        profile.background_text = text
        reply = "Thanks — I've saved that to your founder profile. This'll help shape sourcing and category suggestions."
    else:
        profile.aspirations_text = ((profile.aspirations_text or "") + " " + text).strip()
        reply = "Noted — added to your founder profile."
    db.commit()

    seed_checklist_items = onboard_service.seed_checklist_for_brand(db, brand)
    return ChatResult(
        module=ModuleName.ONBOARD,
        reply=reply,
        payload={"checklist_item_count": len(seed_checklist_items)},
    )


def _handle_none(text: str) -> ChatResult:
    reply = (
        "I can help with sourcing suppliers, building your store, tracking your finances, or your brand "
        "profile — try something like \"find me suppliers for 500 units of X\" or \"how much did I make this month\"."
    )
    return ChatResult(module=ModuleName.NONE, reply=reply, payload={})


def handle_message(db: Session, brand: Brand, text: str) -> ChatResult:
    db.add(ChatMessage(brand_id=brand.id, role=ChatRole.USER, module=ModuleName.NONE, content=text))
    db.commit()

    module = classify_intent(text)
    handlers = {
        ModuleName.SOURCE: lambda: _handle_source(db, brand, text),
        ModuleName.SELL: lambda: _handle_sell(db, brand, text),
        ModuleName.FINANCE: lambda: _handle_finance(db, brand, text),
        ModuleName.ONBOARD: lambda: _handle_onboard(db, brand, text),
        ModuleName.NONE: lambda: _handle_none(text),
    }
    result = handlers[module]()

    db.add(
        ChatMessage(
            brand_id=brand.id,
            role=ChatRole.ASSISTANT,
            module=result.module,
            content=result.reply,
            structured_payload=result.payload,
        )
    )
    db.commit()
    return result
