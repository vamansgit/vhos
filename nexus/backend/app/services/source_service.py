"""Source module services (PRD §5) — NL sourcing assistant, ranked supplier
matching (never a bare filter grid), RFQ generation, and quote acceptance."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import RFQStatus, SourcedOrderStatus, SourcingCategory, SourcingRequestStatus
from app.models.source import RFQ, CatalogItem, Quote, SourcedOrder, SourcingMatch, SourcingRequest, Supplier

DEFAULT_MATCH_COUNT = 5


def _price_at_quantity(catalog_item: CatalogItem, quantity: int) -> float:
    breaks = sorted(catalog_item.price_breaks, key=lambda b: b["min_qty"])
    price = breaks[0]["unit_price"] if breaks else 0.0
    for b in breaks:
        if quantity >= b["min_qty"]:
            price = b["unit_price"]
    return price


def _score_match(request: SourcingRequest, supplier: Supplier, item: CatalogItem, unit_price: float) -> tuple[float, str]:
    price_score = 100.0
    if request.target_price:
        if unit_price <= request.target_price:
            price_score = 100.0
        else:
            overage = (unit_price - request.target_price) / request.target_price
            price_score = max(0.0, 100.0 - overage * 150)

    rating_score = (supplier.rating / 5.0) * 100
    lead_time_score = max(0.0, 100.0 - supplier.lead_time_avg_days * 2)

    fit_score = round(price_score * 0.45 + rating_score * 0.30 + lead_time_score * 0.25, 1)

    reason_parts = [f"₹{unit_price:g}/unit at your quantity"]
    if request.target_price and unit_price <= request.target_price:
        reason_parts.append("within your target price")
    elif request.target_price:
        reason_parts.append(f"{round((unit_price / request.target_price - 1) * 100)}% over your target")
    reason_parts.append(f"{supplier.rating}★ rating")
    reason_parts.append(f"{supplier.lead_time_avg_days}-day lead time")
    if supplier.verification_status.value in ("verified", "featured"):
        reason_parts.append("verified supplier")
    reason = ", ".join(reason_parts) + "."

    return fit_score, reason


def generate_matches(db: Session, request: SourcingRequest, top_n: int = DEFAULT_MATCH_COUNT) -> list[SourcingMatch]:
    request.status = SourcingRequestStatus.MATCHING
    db.commit()

    db.query(SourcingMatch).filter(SourcingMatch.request_id == request.id).delete()
    db.commit()

    category = SourcingCategory(request.category)
    candidates = (
        db.query(Supplier, CatalogItem)
        .join(CatalogItem, CatalogItem.supplier_id == Supplier.id)
        .filter(CatalogItem.category == category)
        .all()
    )
    if request.quantity:
        candidates = [(s, i) for s, i in candidates if request.quantity >= i.moq]

    scored: list[tuple[float, str, Supplier, CatalogItem, float]] = []
    for supplier, item in candidates:
        unit_price = _price_at_quantity(item, request.quantity or item.moq)
        fit_score, reason = _score_match(request, supplier, item, unit_price)
        scored.append((fit_score, reason, supplier, item, unit_price))

    scored.sort(key=lambda t: t[0], reverse=True)

    matches: list[SourcingMatch] = []
    for rank, (fit_score, reason, supplier, item, unit_price) in enumerate(scored[:top_n], start=1):
        match = SourcingMatch(
            request_id=request.id,
            supplier_id=supplier.id,
            catalog_item_id=item.id,
            fit_score=fit_score,
            estimated_unit_price=unit_price,
            reason=reason,
            rank=rank,
        )
        db.add(match)
        matches.append(match)

    request.status = SourcingRequestStatus.MATCHED if matches else SourcingRequestStatus.DRAFT
    db.commit()
    for m in matches:
        db.refresh(m)
    return matches


def generate_rfq_message(request: SourcingRequest, supplier: Supplier, item: CatalogItem) -> str:
    lines = [
        f"Hi {supplier.name},",
        "",
        f"We're interested in sourcing: {item.title}",
        f"Quantity: {request.quantity or item.moq:,} units",
    ]
    if request.target_price:
        lines.append(f"Target price: ₹{request.target_price:g}/unit")
    if request.destination:
        lines.append(f"Delivery to: {request.destination}")
    if request.deadline:
        lines.append(f"Needed by: {request.deadline.isoformat()}")
    lines += ["", "Could you share your best quote (unit price, MOQ, lead time, and terms)?", "", "Thanks!"]
    return "\n".join(lines)


def create_rfqs(db: Session, request: SourcingRequest, supplier_ids: list[str]) -> list[RFQ]:
    rfqs = []
    for supplier_id in supplier_ids:
        match = next((m for m in request.matches if m.supplier_id == supplier_id), None)
        if match is None:
            continue
        message = generate_rfq_message(request, match.supplier, match.catalog_item)
        rfq = RFQ(request_id=request.id, supplier_id=supplier_id, message=message)
        db.add(rfq)
        rfqs.append(rfq)
    request.status = SourcingRequestStatus.RFQ_SENT
    db.commit()
    for r in rfqs:
        db.refresh(r)
    return rfqs


def submit_quote(db: Session, rfq: RFQ, unit_price: float, moq: int, lead_time_days: int, terms: str | None) -> Quote:
    quote = Quote(rfq_id=rfq.id, unit_price=unit_price, moq=moq, lead_time_days=lead_time_days, terms=terms)
    db.add(quote)
    rfq.status = RFQStatus.QUOTED
    # A sibling RFQ on the same request may already be accepted — don't
    # regress the request's status backwards when quoting another one.
    if rfq.request.status != SourcingRequestStatus.ACCEPTED:
        rfq.request.status = SourcingRequestStatus.QUOTED
    db.commit()
    db.refresh(quote)
    return quote


def accept_quote(db: Session, quote: Quote, brand_id: str, quantity: int) -> SourcedOrder:
    rfq = quote.rfq
    supplier = rfq.supplier
    catalog_item = next((m.catalog_item for m in rfq.request.matches if m.supplier_id == supplier.id), None)
    title = catalog_item.title if catalog_item else f"Sourced item from {supplier.name}"
    category = catalog_item.category if catalog_item else SourcingCategory.PRODUCT

    order = SourcedOrder(
        brand_id=brand_id,
        quote_id=quote.id,
        supplier_id=supplier.id,
        title=title,
        category=category,
        quantity=quantity,
        unit_cost=quote.unit_price,
        total_cost=round(quote.unit_price * quantity, 2),
        status=SourcedOrderStatus.CONFIRMED,
    )
    db.add(order)
    rfq.status = RFQStatus.CLOSED
    rfq.request.status = SourcingRequestStatus.ACCEPTED
    db.commit()
    db.refresh(order)
    return order
