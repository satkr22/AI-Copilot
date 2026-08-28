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

    # Relationships
    projects: Mapped[list["Project"]] = relationship( # type: ignore
        "Project",
        back_populates="source"
    )
    
    user: Mapped["User"] = relationship( # type: ignore
        "User",
        back_populates="repositories"
    )