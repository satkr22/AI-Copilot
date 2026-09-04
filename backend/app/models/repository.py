from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class SourceType(str, Enum):
    ZIP = "zip"
    GITHUB = "github"
    DUPLICATE = "duplicate"


class Repository(Base):
    __tablename__ = "repositories"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # FK
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    source_type: Mapped[SourceType] = mapped_column(
        SQLEnum(SourceType, name="source_type"),
        nullable=False
    )

    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    local_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    branch: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    commit_hash: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # contains id of the repo from this repo is created
    duplicate: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship( #type: ignore
        "Project",
        back_populates="repository"
    )

    user: Mapped["User"] = relationship( #type: ignore
        "User",
        back_populates="repositories"
    )
    
    branches: Mapped[list["RepositoryBranch"]] = relationship( #type: ignore
        "RepositoryBranch",
        back_populates="repo"
    )
    
    indexing_jobs: Mapped[list["IndexingJob"]] = relationship( #type: ignore
        "IndexingJob",
        back_populates="repo"
    )
    
    files: Mapped[list["RepositoryFile"]] = relationship( #type: ignore
        "RepositoryFile",
        back_populates="repository"
    )