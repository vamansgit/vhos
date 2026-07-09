from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand
from app.models.chat import ChatMessage
from app.schemas.chat import ChatMessageOut, ChatSendRequest, ChatSendResponse
from app.services.orchestrator import handle_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatSendResponse)
def send_message(payload: ChatSendRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> ChatSendResponse:
    result = handle_message(db, brand, payload.text)
    return ChatSendResponse(reply=result.reply, module=result.module, payload=result.payload)


@router.get("/history", response_model=list[ChatMessageOut])
def get_history(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.brand_id == brand.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
