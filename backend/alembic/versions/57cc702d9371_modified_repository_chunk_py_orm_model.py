"""modified repository_chunk.py orm model

Revision ID: dd206f19d619
Revises: b2effd83dc25
Create Date: 2026-09-06 17:58:18.780164

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "57cc702d9371"
down_revision: Union[str, Sequence[str], None] = "dd206f19d619"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove TREE_SITTER from chunkprovider enum."""

    op.execute(
        """
        ALTER TYPE chunkprovider
        RENAME TO chunkprovider_old
        """
    )

    op.execute(
        """
        CREATE TYPE chunkprovider AS ENUM (
            'JCODE',
            'SYMLENS'
        )
        """
    )

    op.execute(
        """
        ALTER TABLE repository_chunks
        ALTER COLUMN provider
        TYPE chunkprovider
        USING provider::text::chunkprovider
        """
    )

    op.execute(
        """
        DROP TYPE chunkprovider_old
        """
    )


def downgrade() -> None:
    """Restore TREE_SITTER to chunkprovider enum."""

    op.execute(
        """
        ALTER TYPE chunkprovider
        RENAME TO chunkprovider_old
        """
    )

    op.execute(
        """
        CREATE TYPE chunkprovider AS ENUM (
            'JCODE',
            'SYMLENS',
            'TREE_SITTER'
        )
        """
    )

    op.execute(
        """
        ALTER TABLE repository_chunks
        ALTER COLUMN provider
        TYPE chunkprovider
        USING provider::text::chunkprovider
        """
    )

    op.execute(
        """
        DROP TYPE chunkprovider_old
        """
    )