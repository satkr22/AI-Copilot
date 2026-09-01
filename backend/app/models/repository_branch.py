from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class RepositoryBranch(Base):
    __tablename__ = "repository_branches"
    
    __table_args__ = (UniqueConstraint
        (
            "repository_id",
            "branch_name",
            name="uq_repository_branch"
        ), 
    )
    
    
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

    branch_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    latest_commit_hash: Mapped[str] = mapped_column(
        String(40),
        nullable=False
    )

    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    repo: Mapped["Repository"] = relationship( #type: ignore
        "Repository",
        back_populates="branches"
    )
