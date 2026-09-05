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


class ImportLanguage(str, Enum):
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


class RepositoryImport(Base):
    __tablename__ = "repository_imports"
    
    __table_args__ = (
        # An import should be unique per file (import_path + import_name)
        UniqueConstraint(
            "repository_file_id",
            "import_path",
            "import_name",
            name="uq_repo_file_import_path_name"
        ),
        # # For faster queries on common filters
        # Index("idx_repository_imports_repo_id", "repository_id"),
        # Index("idx_repository_imports_branch_id", "repository_branch_id"),
        # Index("idx_repository_imports_file_id", "repository_file_id"),
        # Index("idx_repository_imports_import_path", "import_path"),
        # Index("idx_repository_imports_import_name", "import_name"),
        # Index("idx_repository_imports_language", "language"),
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
    
    # Import Information
    import_path: Mapped[str] = mapped_column(
        String(1000), 
        nullable=False
    )
    
    import_name: Mapped[str | None] = mapped_column(
        String(255),  # The actual imported name/alias (e.g., numpy as np here 'np' is alias)
        nullable=True
    )
    
    language: Mapped[ImportLanguage | None] = mapped_column(
        SQLEnum(ImportLanguage),
        nullable=True
    )
    
    # Position Information
    line_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
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
        back_populates="imports" 
    )
    
    branch: Mapped["RepositoryBranch"] = relationship(  # type: ignore
        "RepositoryBranch",
        back_populates="imports"  
    )
    
    file: Mapped["RepositoryFile"] = relationship(  # type: ignore
        "RepositoryFile",
        back_populates="imports"  
    )