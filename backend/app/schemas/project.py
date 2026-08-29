from datetime import datetime
from pydantic import BaseModel, Field
from app.models.project import ProjectStatus
from uuid import UUID

# ---------- Requests ----------

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    repository_id: str | None = None


# ---------- Update ----------

class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    status: ProjectStatus | None = None


class ProjectRepositoryAttach(BaseModel):
    repository_id: str


# ---------- Response ----------

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    repository_id: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
