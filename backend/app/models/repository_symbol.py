from datetime import datetime
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


class RepositorySymbol(Base):
    __tablename__ = "repository_symbols"
    
    __table_args__ = (
        # A symbol name should be unique per file
        UniqueConstraint(
            "repository_file_id",
            "name",
            "kind",
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
    name: Mapped[str] = mapped_column(
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
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
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