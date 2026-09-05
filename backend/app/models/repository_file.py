from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    BigInteger,
    UniqueConstraint,
    Text,
    Index,
    Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ParseStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class RepositoryFile(Base):
    __tablename__ = "repository_files"
    
    __table_args__ = (
        # A file path should be unique per repository branch
        UniqueConstraint(
            "repository_branch_id",
            "path",
            name="uq_repo_branch_file_path"
        ),
        # # For faster queries on common filters
        # Index("idx_repository_files_repo_id", "repository_id"),
        # Index("idx_repository_files_branch_id", "repository_branch_id"),
        # Index("idx_repository_files_language", "language"),
        # Index("idx_repository_files_commit_hash", "commit_hash"),
    )
    
    # Primary Key
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # FKs
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False
    )
    
    repository_branch_id: Mapped[str] = mapped_column(
        ForeignKey("repository_branches.id"),
        nullable=False
    )
    
    repository_branch_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    # File Information
    path: Mapped[str] = mapped_column(
        String(1000),  # File paths can be long
        nullable=False
    )
    
    commit_hash: Mapped[str] = mapped_column(
        String(40),  # Git commit hash
        nullable=False
    )
    
    size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,  # For large files
        nullable=True
    )
    
    language: Mapped[str | None] = mapped_column(
        String(100),  # e.g., "Python", "JavaScript", "Go"
        nullable=True
    )
    
    # Parse Status Fields
    parse_status: Mapped[ParseStatus] = mapped_column(
        SQLEnum(ParseStatus),
        nullable=False,
        default=ParseStatus.PENDING,
    )
    
    parse_error: Mapped[str | None] = mapped_column(
        Text,  # Use Text for error messages as they can be long
        nullable=True
    )
    
    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Timestamps
    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )
    
    # Relationships (optional)
    repository: Mapped["Repository"] = relationship(  # type: ignore
        "Repository",
        back_populates="files" 
    )
    
    branch: Mapped["RepositoryBranch"] = relationship(  # type: ignore
        "RepositoryBranch",
        back_populates="files"  
    )
    
    symbols: Mapped[list["RepositorySymbol"]] = relationship( # type: ignore
        "RepositorySymbol",
        back_populates="file"
    )
    
    imports: Mapped[list["RepositoryImport"]] = relationship( # type: ignore
        "RepositoryImport",
        back_populates="file"
    )