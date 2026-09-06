from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChunkProvider(str, Enum):
    JCODE = "jcode"
    SYMLENS = "symlens"
    TREE_SITTER = "tree_sitter"


class ChunkType(str, Enum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class RepositoryChunk(Base):
    __tablename__ = "repository_chunks"

    __table_args__ = (
        UniqueConstraint(
            "repository_file_id",
            "symbol_id",
            "chunk_type",
            name="uq_repo_chunk_file_symbol_type",
        ),
    )

    # ------------------------------------------------------------------
    # Primary Key
    # ------------------------------------------------------------------

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # ------------------------------------------------------------------
    # Foreign Keys
    # ------------------------------------------------------------------

    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False,
    )

    repository_branch_id: Mapped[str] = mapped_column(
        ForeignKey("repository_branches.id"),
        nullable=False,
    )

    repository_file_id: Mapped[str] = mapped_column(
        ForeignKey("repository_files.id"),
        nullable=False,
    )

    symbol_id: Mapped[str | None] = mapped_column(
        ForeignKey("repository_symbols.id"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Chunk Metadata
    # ------------------------------------------------------------------

    provider: Mapped[ChunkProvider] = mapped_column(
        SQLEnum(ChunkProvider),
        nullable=False,
    )

    chunk_type: Mapped[ChunkType] = mapped_column(
        SQLEnum(ChunkType),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Source Code
    # ------------------------------------------------------------------

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    repository: Mapped["Repository"] = relationship(  # type: ignore
        "Repository",
        back_populates="chunks",
    )

    branch: Mapped["RepositoryBranch"] = relationship(  # type: ignore
        "RepositoryBranch",
        back_populates="chunks",
    )

    file: Mapped["RepositoryFile"] = relationship(  # type: ignore
        "RepositoryFile",
        back_populates="chunks",
    )

    symbol: Mapped["RepositorySymbol | None"] = relationship(  # type: ignore
        "RepositorySymbol",
    )