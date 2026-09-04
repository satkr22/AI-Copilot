from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, model_validator
from app.models.repository import SourceType

from app.models.indexing_jobs import JobStatus



# ---------- Response ----------

class IndexingJobResponse(BaseModel):
    id: str
    repository_id: str
    status: JobStatus
    started_at: datetime 
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
    