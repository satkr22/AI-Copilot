"""Add fields required by the query/cAST indexing pipeline."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "9f1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "57cc702d9371"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for value in ("interface", "struct", "enum", "type_alias"):
        op.execute(f"ALTER TYPE symbolkind ADD VALUE IF NOT EXISTS '{value.upper()}'")
    for value in (
        "interface",
        "struct",
        "enum",
        "type_alias",
        "gap",
        "merged",
    ):
        op.execute(f"ALTER TYPE chunktype ADD VALUE IF NOT EXISTS '{value.upper()}'")
    for enum_name in ("symbollanguage", "importlanguage"):
        for value in ("csharp", "php", "ruby", "bash", "sql"):
            op.execute(
                f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value.upper()}'"
            )

    op.add_column(
        "repository_files",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )

    op.add_column(
        "repository_symbols",
        sa.Column("qualified_name", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "repository_symbols", sa.Column("parent_symbol_id", sa.String(), nullable=True)
    )
    op.add_column(
        "repository_symbols", sa.Column("start_byte", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_symbols", sa.Column("end_byte", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_symbols",
        sa.Column("signature", sa.String(length=2000), nullable=True),
    )
    op.add_column(
        "repository_symbols", sa.Column("docstring", sa.String(), nullable=True)
    )
    op.add_column(
        "repository_symbols",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "fk_repository_symbols_parent",
        "repository_symbols",
        "repository_symbols",
        ["parent_symbol_id"],
        ["id"],
    )
    op.drop_constraint(
        "uq_repo_file_symbol_name_kind", "repository_symbols", type_="unique"
    )
    op.create_unique_constraint(
        "uq_repo_file_symbol_name_kind",
        "repository_symbols",
        ["repository_file_id", "name", "kind", "start_byte"],
    )

    op.add_column(
        "repository_imports", sa.Column("alias", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "repository_imports",
        sa.Column(
            "is_relative", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    op.add_column(
        "repository_imports", sa.Column("start_byte", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_imports", sa.Column("end_byte", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_imports", sa.Column("raw_statement", sa.String(), nullable=True)
    )
    op.drop_constraint(
        "uq_repo_file_import_path_name", "repository_imports", type_="unique"
    )
    op.create_unique_constraint(
        "uq_repo_file_import_path_name",
        "repository_imports",
        ["repository_file_id", "import_path", "import_name", "start_byte"],
    )

    """Remove TREE_SITTER from chunkprovider enum."""
    op.execute("""
        ALTER TYPE chunkprovider
        RENAME TO chunkprovider_old
        """)
    op.execute("""
        CREATE TYPE chunkprovider AS ENUM (
            'JCODE',
            'SYMLENS',
            'TREE_SITTER'
        )
        """)
    op.execute("""
        ALTER TABLE repository_chunks
        ALTER COLUMN provider
        TYPE chunkprovider
        USING provider::text::chunkprovider
        """)
    op.execute("""
        DROP TYPE chunkprovider_old
        """)

    op.drop_constraint(
        "uq_repo_chunk_file_symbol_type", "repository_chunks", type_="unique"
    )
    op.add_column(
        "repository_chunks",
        sa.Column(
            "origin",
            sa.String(length=40),
            server_default="query_symbol",
            nullable=False,
        ),
    )
    op.add_column(
        "repository_chunks",
        sa.Column(
            "symbol_ids",
            postgresql.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "repository_chunks",
        sa.Column(
            "scope_chain",
            postgresql.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "repository_chunks", sa.Column("start_byte", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_chunks", sa.Column("end_byte", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_chunks", sa.Column("enriched_content", sa.Text(), nullable=True)
    )
    op.add_column(
        "repository_chunks", sa.Column("contextual_summary", sa.Text(), nullable=True)
    )
    op.add_column(
        "repository_chunks",
        sa.Column(
            "is_partial", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    op.add_column(
        "repository_chunks", sa.Column("part_index", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_chunks", sa.Column("part_total", sa.Integer(), nullable=True)
    )
    op.add_column(
        "repository_chunks",
        sa.Column(
            "content_hash", sa.String(length=64), server_default="", nullable=False
        ),
    )
    op.create_unique_constraint(
        "uq_repo_chunk_file_content_hash",
        "repository_chunks",
        ["repository_file_id", "content_hash"],
    )


def downgrade() -> None:
    """Restore TREE_SITTER to chunkprovider enum."""
    op.execute("""
        ALTER TYPE chunkprovider
        RENAME TO chunkprovider_old
        """)
    op.execute("""
        CREATE TYPE chunkprovider AS ENUM (
            'JCODE',
            'SYMLENS',
        )
        """)
    op.execute("""
        ALTER TABLE repository_chunks
        ALTER COLUMN provider
        TYPE chunkprovider
        USING provider::text::chunkprovider
        """)
    op.execute("""
        DROP TYPE chunkprovider_old
        """)

    op.drop_constraint(
        "uq_repo_chunk_file_content_hash", "repository_chunks", type_="unique"
    )
    for column in (
        "content_hash",
        "part_total",
        "part_index",
        "is_partial",
        "contextual_summary",
        "enriched_content",
        "end_byte",
        "start_byte",
        "scope_chain",
        "symbol_ids",
        "origin",
    ):
        op.drop_column("repository_chunks", column)
    op.create_unique_constraint(
        "uq_repo_chunk_file_symbol_type",
        "repository_chunks",
        ["repository_file_id", "symbol_id", "chunk_type"],
    )
    op.drop_constraint(
        "uq_repo_file_import_path_name", "repository_imports", type_="unique"
    )
    op.create_unique_constraint(
        "uq_repo_file_import_path_name",
        "repository_imports",
        ["repository_file_id", "import_path", "import_name"],
    )
    op.drop_constraint(
        "uq_repo_file_import_path_name", "repository_imports", type_="unique"
    )
    for column in ("raw_statement", "end_byte", "start_byte", "is_relative", "alias"):
        op.drop_column("repository_imports", column)
    op.drop_constraint(
        "fk_repository_symbols_parent", "repository_symbols", type_="foreignkey"
    )
    op.drop_constraint(
        "uq_repo_file_symbol_name_kind", "repository_symbols", type_="unique"
    )
    for column in (
        "content_hash",
        "docstring",
        "signature",
        "end_byte",
        "start_byte",
        "parent_symbol_id",
        "qualified_name",
    ):
        op.drop_column("repository_symbols", column)
    op.create_unique_constraint(
        "uq_repo_file_symbol_name_kind",
        "repository_symbols",
        ["repository_file_id", "name", "kind"],
    )
    op.drop_column("repository_files", "content_hash")
