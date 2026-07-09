"""Cross-cutting help layer (PRD §6.2E, §10.1) — every module carries FAQ /
how-to / best-practice content so users are never staring at a blank
screen. Seeded once at startup; read-only via the API."""

from sqlalchemy.orm import Session

from app.models.enums import HelpContentType
from app.models.sell import HelpContent

_SEED_CONTENT: list[dict] = [
    {"module": "onboard", "topic": "What documents do I need before I launch?", "type": HelpContentType.FAQ,
     "body": "At minimum: a business structure decision and a bank account. GST becomes mandatory once you sell "
             "cross-state or cross a turnover threshold. Category-specific licenses (FSSAI for food, BIS for "
             "electronics/cosmetics) are needed before you sell in that category.",
     "category_tags": "documents,gst,launch"},
    {"module": "onboard", "topic": "How do I update my brand's target market?", "type": HelpContentType.HOW_TO,
     "body": "Say something like \"update my brand's target market to include the US\" in chat, or edit it directly "
             "under Brand Profile — this flows automatically into Sell's shipping zones and Grow's audience defaults.",
     "category_tags": "brand profile"},
    {"module": "source", "topic": "How is a supplier's Fit Score calculated?", "type": HelpContentType.FAQ,
     "body": "It blends how close their price is to your target (45%), their rating (30%), and their lead time "
             "(25%) — never just follower count or listing position.",
     "category_tags": "matching,fit score"},
    {"module": "source", "topic": "Should I pick the cheapest supplier?", "type": HelpContentType.BEST_PRACTICE,
     "body": "Not always — a slightly higher price from a verified supplier with a track record often beats a "
             "marginal saving from an unverified one, especially for a first order. Use RFQs to negotiate once "
             "you've shortlisted 2-3.",
     "category_tags": "sourcing,negotiation"},
    {"module": "sell", "topic": "How do I add a discount code?", "type": HelpContentType.HOW_TO,
     "body": "Ask in chat — \"add a 10% discount code WELCOME10 for first-time buyers\" — or manage codes directly "
             "under Store Settings once your store is live.",
     "category_tags": "discounts,checkout"},
    {"module": "sell", "topic": "What's a good return policy for apparel?", "type": HelpContentType.BEST_PRACTICE,
     "body": "7-15 days for exchanges/returns is standard for Indian D2C apparel brands; be explicit about who "
             "bears return shipping cost to avoid disputes.",
     "category_tags": "returns,apparel"},
    {"module": "sell", "topic": "Which payment providers should I enable?", "type": HelpContentType.FAQ,
     "body": "UPI and cards cover the vast majority of Indian D2C checkouts. Add EMI only if your average order "
             "value is high (₹5,000+) — otherwise it adds friction without meaningfully lifting conversion.",
     "category_tags": "payments"},
    {"module": "finance", "topic": "How is margin calculated?", "type": HelpContentType.FAQ,
     "body": "Gross margin = (revenue − COGS) / revenue. COGS here is your actual sourced unit cost, not a "
             "guess — it's pulled directly from your accepted supplier quotes.",
     "category_tags": "margin,p&l"},
    {"module": "finance", "topic": "Is Nexus a substitute for my CA?", "type": HelpContentType.FAQ,
     "body": "No — Nexus prepares and pre-fills GST drafts and financial records, but final review and sign-off "
             "by you (or your CA) is required before anything is filed.",
     "category_tags": "compliance,gst"},
]


def seed_help_content(db: Session) -> None:
    if db.query(HelpContent).count() > 0:
        return
    for entry in _SEED_CONTENT:
        db.add(HelpContent(**entry))
    db.commit()
