from app.models.enums import BrandStage, BusinessStructure
from pydantic import BaseModel, ConfigDict


class BrandOut(BaseModel):
    id: str
    name: str
    category: str | None
    stage: BrandStage
    structure: BusinessStructure
    target_geographies: str | None
    style_descriptors: str | None
    team_size: int

    model_config = ConfigDict(from_attributes=True)


class BrandUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    stage: BrandStage | None = None
    structure: BusinessStructure | None = None
    target_geographies: str | None = None
    style_descriptors: str | None = None
    team_size: int | None = None


class FounderProfileOut(BaseModel):
    background_text: str | None
    skills: str | None
    aspirations_text: str | None
    risk_appetite: str | None
    time_availability_hours_per_week: int | None

    model_config = ConfigDict(from_attributes=True)


class FounderProfileUpdate(BaseModel):
    background_text: str | None = None
    skills: str | None = None
    aspirations_text: str | None = None
    risk_appetite: str | None = None
    time_availability_hours_per_week: int | None = None
