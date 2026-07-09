from datetime import datetime

from app.models.enums import ChatRole, ModuleName
from pydantic import BaseModel, ConfigDict, Field


class ChatSendRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class ChatMessageOut(BaseModel):
    id: str
    role: ChatRole
    module: ModuleName
    content: str
    structured_payload: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSendResponse(BaseModel):
    reply: str
    module: ModuleName
    payload: dict
