from app.models.enums import ChecklistItemStatus
from pydantic import BaseModel, ConfigDict


class ChecklistItemOut(BaseModel):
    id: str
    requirement: str
    due_context: str | None
    status: ChecklistItemStatus

    model_config = ConfigDict(from_attributes=True)


class ChecklistItemUpdate(BaseModel):
    status: ChecklistItemStatus
