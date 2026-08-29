from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, model_validator
from app.models.repository import SourceType


# ---------- Request ----------

class RepositoryCreate(BaseModel):
    source_type: SourceType
    source_url: HttpUrl | None = None
    branch: str | None = Field(default="main", max_length=100)

    @model_validator(mode="after")
    def validate_github(self):
        if self.source_type == SourceType.GITHUB and self.source_url is None:
            raise ValueError("Source url is required for GitHub repositories")
        
        return self


class GithubRepositoryCreate(BaseModel):
    source_url: HttpUrl
    branch: str | None = Field(default="main", max_length=100)


# ---------- Response ----------

class RepositoryResponse(BaseModel):
    id: str
    source_type: SourceType
    source_url: str | None
    local_path: str | None
    branch: str | None
    commit_hash: str | None
    created_at: datetime
    indexed_at: datetime | None

    model_config = {"from_attributes": True}
