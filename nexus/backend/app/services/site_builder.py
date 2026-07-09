"""Deterministic NL -> storefront generator (PRD §6.2A). Draws on the
Onboard brand profile (category, style descriptors, target geographies) so
the first draft is personalized rather than generic. No LLM dependency —
color/tone selection is keyword-driven, matching the platform's
pluggable-with-fallback pattern used elsewhere (Source NLP, AdSaarthi
content generation)."""

import re

from app.models.brand import Brand

_PALETTES = {
    "minimal": {"primary": "#1f2329", "accent": "#697585", "background": "#ffffff"},
    "earthy": {"primary": "#6b4f3a", "accent": "#a97155", "background": "#f5efe6"},
    "bold": {"primary": "#e11d48", "accent": "#111827", "background": "#ffffff"},
    "playful": {"primary": "#f59e0b", "accent": "#ec4899", "background": "#fffbeb"},
    "luxury": {"primary": "#0b0b0b", "accent": "#c9a227", "background": "#f8f7f4"},
}
_DEFAULT_PALETTE = {"primary": "#1eb371", "accent": "#12744b", "background": "#ffffff"}

_STANDARD_PAGES = ["home", "shop", "product", "cart", "checkout", "shipping_policy", "returns_policy", "contact"]


def _pick_palette(style_descriptors: str | None) -> dict:
    if not style_descriptors:
        return _DEFAULT_PALETTE
    lower = style_descriptors.lower()
    for keyword, palette in _PALETTES.items():
        if keyword in lower:
            return palette
    return _DEFAULT_PALETTE


def _slugify(name: str) -> str:
    raw = "".join(c.lower() if c.isalnum() else "-" for c in name)
    return re.sub(r"-+", "-", raw).strip("-")


def generate_theme_and_pages(brand: Brand) -> tuple[dict, list[dict], str]:
    palette = _pick_palette(brand.style_descriptors)
    style_label = brand.style_descriptors or "clean, modern"
    tagline = f"{brand.name} — thoughtfully made" + (f" for {brand.category}" if brand.category else "")

    theme_config = {
        "palette": palette,
        "typography": "sans-serif, generous whitespace" if "minimal" in style_label.lower() else "sans-serif",
        "style_label": style_label,
        "tagline": tagline,
    }
    pages = [{"slug": p, "title": p.replace("_", " ").title()} for p in _STANDARD_PAGES]
    domain = f"{_slugify(brand.name)}.nexus.store"
    return theme_config, pages, domain
