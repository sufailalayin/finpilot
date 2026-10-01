"""Add structural marker for internal transfers.

Revision ID: 0026_internal_transfer_marker
Revises: 0025_github_release_url
"""

from alembic import op
import sqlalchemy as sa


revision = "0026_internal_transfer_marker"
down_revision = "0025_github_release_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column(
            "is_internal_transfer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Preserve the behavior of historical transfer rows that were identified
    # only by these system-generated merchant labels before this marker existed.
    op.execute(
        """
        UPDATE transactions
        SET is_internal_transfer = TRUE
        WHERE merchant IN ('Transfer out', 'Transfer in')
        """
    )


def downgrade() -> None:
    op.drop_column("transactions", "is_internal_transfer")
