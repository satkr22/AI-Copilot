from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship( #type: ignore
        "Project",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    repositories: Mapped[list["Repository"]] = relationship( #type: ignore
        "Repository",
        back_populates="user",
        cascade="all, delete-orphan"
    )