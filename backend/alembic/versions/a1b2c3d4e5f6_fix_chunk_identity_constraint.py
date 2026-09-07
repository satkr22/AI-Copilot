"""Make chunk idempotency unique by logical chunk identity."""

from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9f1b2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_repo_chunk_file_content_hash",
        "repository_chunks",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_repo_chunk_file_identity",
        "repository_chunks",
        [
            "repository_file_id",
            "content_hash",
            "start_byte",
            "end_byte",
            "origin",
            "symbol_id",
            "part_index",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_repo_chunk_file_identity",
        "repository_chunks",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_repo_chunk_file_content_hash",
        "repository_chunks",
        ["repository_file_id", "content_hash"],
    )
