"""Add archive state for legacy finance currency remediation.

Revision ID: 0027_finance_account_archive
Revises: 0026_internal_transfer_marker
"""

from alembic import op
import sqlalchemy as sa


revision = "0027_finance_account_archive"
down_revision = "0026_internal_transfer_marker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "finance_accounts",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("finance_accounts", "is_archived")
