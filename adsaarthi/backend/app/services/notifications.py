import structlog

from app.models.brand import Brand

logger = structlog.get_logger(__name__)


def compose_weekly_digest(brand: Brand, summary: dict) -> str:
    """Weekly digest email/WhatsApp summary for founders who won't log in
    daily (PRD 6.1)."""
    alert = summary["trend_alert"]
    lines = [
        f"AdSaarthi Weekly Digest — {brand.name}",
        "",
        f"Spend: ₹{summary['total_spend']:,.0f}  |  Conversions: {summary['total_conversions']}",
        f"Blended CAC: {'₹' + str(summary['blended_cac']) if summary['blended_cac'] else 'n/a'}",
        f"Blended ROAS: {summary['blended_roas'] if summary['blended_roas'] else 'n/a'}",
        "",
        f"CAC trend: {alert['message']}",
    ]
    if summary.get("benchmark"):
        b = summary["benchmark"]
        lines.append(f"Category benchmark ({b['category']}): avg CAC ₹{b['avg_cac']} vs your ₹{b['brand_cac']}")
    return "\n".join(lines)


def send_digest(brand: Brand, channel: str, message: str) -> None:
    """Stub dispatcher — wires to a real email/WhatsApp Business API provider
    in production. MVP logs the composed digest so the flow is fully testable
    without external notification credentials."""
    logger.info("digest.send", brand_id=brand.id, channel=channel, message=message)


def send_cac_alert(brand: Brand, alert: dict) -> None:
    if not alert["triggered"]:
        return
    logger.info("cac_alert.triggered", brand_id=brand.id, message=alert["message"])
