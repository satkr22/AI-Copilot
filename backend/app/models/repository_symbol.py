from datetime import datetime, timezone
from uuid import uuid4
from enum import Enum
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Index,
    Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SymbolKind(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"


class SymbolLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    BASH = "bash"
    SQL = "sql"


class RepositorySymbol(Base):
    __tablename__ = "repository_symbols"
    
    __table_args__ = (
        # A symbol name should be unique per file
        UniqueConstraint(
            "repository_file_id",
            "name",
            "kind",
            "start_byte",
            name="uq_repo_file_symbol_name_kind"
        ),
        # # For faster queries on common filters
        # Index("idx_repository_symbols_repo_id", "repository_id"),
        # Index("idx_repository_symbols_branch_id", "repository_branch_id"),
        # Index("idx_repository_symbols_file_id", "repository_file_id"),
        # Index("idx_repository_symbols_kind", "kind"),
        # Index("idx_repository_symbols_language", "language"),
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
    
    repository_file_id: Mapped[str] = mapped_column(
        ForeignKey("repository_files.id"),
        nullable=False
    )
    
    # Symbol Information
    name: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=False
    )
    
    kind: Mapped[SymbolKind] = mapped_column(
        SQLEnum(SymbolKind),
        nullable=False
    )
    
    language: Mapped[SymbolLanguage | None] = mapped_column(
        SQLEnum(SymbolLanguage),
        nullable=False
    )
    
    # Position Information
    start_line: Mapped[int | None] = mapped_column(
        Integer,
        nullable=False
    )
    
    end_line: Mapped[int | None] = mapped_column(
        Integer,
        nullable=False
    )

    qualified_name: Mapped[str | None] = mapped_column(
        String(1000), 
        nullable=True
    )
    
    parent_symbol_id: Mapped[str | None] = mapped_column(
        ForeignKey("repository_symbols.id"), 
        nullable=True
    
    )
    start_byte: Mapped[int | None] = mapped_column(
        Integer, 
        nullable=True
    )
    
    end_byte: Mapped[int | None] = mapped_column(
        Integer, 
        nullable=True
    )
    signature: Mapped[str | None] = mapped_column(
        String(2000), 
        nullable=True
    
    )
    docstring: Mapped[str | None] = mapped_column(
        String, 
        nullable=True
    )
    
    content_hash: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc)
    )
    
    # Relationships (optional)
    repository: Mapped["Repository"] = relationship(  # type: ignore
        "Repository",
        back_populates="symbols" 
    )
    
    branch: Mapped["RepositoryBranch"] = relationship(  # type: ignore
        "RepositoryBranch",
        back_populates="symbols"  
    )
    
    file: Mapped["RepositoryFile"] = relationship(  # type: ignore
        "RepositoryFile",
        back_populates="symbols"  
    )
    
    chunks: Mapped["RepositoryChunk"] = relationship(  # type: ignore
        "RepositoryChunk",
        back_populates="symbol",
        cascade="all, delete-orphan"  
    )
