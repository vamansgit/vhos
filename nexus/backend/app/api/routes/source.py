from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand
from app.models.enums import SourcingCategory
from app.models.source import RFQ, Quote, SourcedOrder, SourcingMatch, SourcingRequest
from app.schemas.source import (
    QuoteAcceptRequest,
    QuoteOut,
    QuoteSubmitRequest,
    RFQCreateRequest,
    RFQOut,
    SourcedOrderOut,
    SourcingMatchOut,
    SourcingRequestCreate,
    SourcingRequestOut,
)
from app.services.nlp import get_sourcing_parser
from app.services.source_service import accept_quote, create_rfqs, generate_matches, submit_quote

router = APIRouter(prefix="/api/source", tags=["source"])


def _get_request(db: Session, brand: Brand, request_id: str) -> SourcingRequest:
    request = (
        db.query(SourcingRequest)
        .filter(SourcingRequest.id == request_id, SourcingRequest.brand_id == brand.id)
        .first()
    )
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sourcing request not found")
    return request


@router.post("/requests", response_model=SourcingRequestOut, status_code=status.HTTP_201_CREATED)
def create_sourcing_request(
    payload: SourcingRequestCreate, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> dict:
    """PRD §5.2A — parses free text into a structured request and confirms
    the interpretation back in one line before searching."""
    parser = get_sourcing_parser()
    parsed = parser.parse(payload.raw_text)

    deadline = date.today() + timedelta(days=parsed.deadline_days) if parsed.deadline_days else None

    request = SourcingRequest(
        brand_id=brand.id,
        raw_text=payload.raw_text,
        category=SourcingCategory(parsed.category),
        parsed_spec=parsed.spec_attributes,
        quantity=parsed.quantity,
        target_price=parsed.target_price,
        destination=parsed.destination,
        deadline=deadline,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    out = SourcingRequestOut.model_validate(request).model_dump()
    out["confirmation_line"] = parsed.confirmation_line
    return out


@router.get("/requests", response_model=list[SourcingRequestOut])
def list_sourcing_requests(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[SourcingRequest]:
    return (
        db.query(SourcingRequest)
        .filter(SourcingRequest.brand_id == brand.id)
        .order_by(SourcingRequest.created_at.desc())
        .all()
    )


@router.get("/requests/{request_id}", response_model=SourcingRequestOut)
def get_sourcing_request(request_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> SourcingRequest:
    return _get_request(db, brand, request_id)


@router.post("/requests/{request_id}/match", response_model=list[SourcingMatchOut])
def match_suppliers(request_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[SourcingMatch]:
    request = _get_request(db, brand, request_id)
    return generate_matches(db, request)


@router.get("/requests/{request_id}/matches", response_model=list[SourcingMatchOut])
def list_matches(request_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[SourcingMatch]:
    _get_request(db, brand, request_id)
    return (
        db.query(SourcingMatch)
        .filter(SourcingMatch.request_id == request_id)
        .order_by(SourcingMatch.rank)
        .all()
    )


@router.post("/requests/{request_id}/rfqs", response_model=list[RFQOut], status_code=status.HTTP_201_CREATED)
def send_rfqs(
    request_id: str, payload: RFQCreateRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> list[RFQ]:
    request = _get_request(db, brand, request_id)
    return create_rfqs(db, request, payload.supplier_ids)


@router.get("/requests/{request_id}/rfqs", response_model=list[RFQOut])
def list_rfqs(request_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[RFQ]:
    _get_request(db, brand, request_id)
    return db.query(RFQ).filter(RFQ.request_id == request_id).all()


@router.post("/rfqs/{rfq_id}/quote", response_model=QuoteOut, status_code=status.HTTP_201_CREATED)
def submit_rfq_quote(
    rfq_id: str, payload: QuoteSubmitRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> Quote:
    """Simulates the supplier side responding with a quote — in the Phase-1
    manual-RFQ flow this is entered by the brand after receiving a reply
    over email/WhatsApp (PRD §5.5 Phase 1)."""
    rfq = db.query(RFQ).join(SourcingRequest).filter(RFQ.id == rfq_id, SourcingRequest.brand_id == brand.id).first()
    if rfq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")
    return submit_quote(db, rfq, payload.unit_price, payload.moq, payload.lead_time_days, payload.terms)


@router.post("/quotes/{quote_id}/accept", response_model=SourcedOrderOut, status_code=status.HTTP_201_CREATED)
def accept_rfq_quote(
    quote_id: str, payload: QuoteAcceptRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> SourcedOrder:
    quote = (
        db.query(Quote)
        .join(RFQ, RFQ.id == Quote.rfq_id)
        .join(SourcingRequest, SourcingRequest.id == RFQ.request_id)
        .filter(Quote.id == quote_id, SourcingRequest.brand_id == brand.id)
        .first()
    )
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return accept_quote(db, quote, brand.id, payload.quantity)


@router.get("/orders", response_model=list[SourcedOrderOut])
def list_sourced_orders(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[SourcedOrder]:
    return db.query(SourcedOrder).filter(SourcedOrder.brand_id == brand.id).order_by(SourcedOrder.created_at.desc()).all()
