"""Add credit card bill statement metadata.

Revision ID: 0012_credit_card_bills
Revises: 0011_auth_otp
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_credit_card_bills"
down_revision = "0011_auth_otp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bill_reminders",
        sa.Column("bill_generated_on", sa.Date(), nullable=True),
    )
    op.add_column(
        "bill_reminders",
        sa.Column("card_last4", sa.String(length=4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bill_reminders", "card_last4")
    op.drop_column("bill_reminders", "bill_generated_on")
