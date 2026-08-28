from app.db.base import Base
from datetime import datetime
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from uuid import uuid4

class ProjectStatus(str, Enum):
    CREATED = "created"
    IMPORTED = "imported"
    INDEXED = "indexed"
    FAILED = "failed"
    
class Project(Base):
    __tablename__ = "projects"
    
    # PK
    id: Mapped[str] = mapped_column(
        String, 
        primary_key=True,
        default=lambda: str(uuid4())
        
    )
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )
    
    # FK
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    repository_id: Mapped[str | None] = mapped_column(
        ForeignKey("repositories.id", ondelete="RESTRICT"),
        nullable=True        # Project is created first
    )
    
    description: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus, name="project_status"),
        nullable=False,
        default=ProjectStatus.CREATED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # Relationships
    source: Mapped["Repository"] = relationship( # type: ignore
        "Repository",
        back_populates="projects"
    )
    
    user: Mapped["User"] = relationship( # type: ignore
        "User",
        back_populates="projects"
    )