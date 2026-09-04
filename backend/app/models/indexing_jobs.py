from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IndexingJob(Base):
    __tablename__ = "indexing_jobs"
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # FK
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False
    )
    
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus),
        nullable=False,
        default=JobStatus.PENDING
    )
    
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    error_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )
    
    # Relationships
    repo: Mapped["Repository"] = relationship(  # type: ignore
        "Repository",
        back_populates="indexing_jobs"  
    )