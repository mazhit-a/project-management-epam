from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document import DocumentRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, examples=["Website Redesign"])
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    """Request body for PUT /project/{id}/info. Every field optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class ProjectWithDocuments(ProjectRead):
    """Full project info: details + documents, as returned by GET /projects."""

    documents: list[DocumentRead] = []
