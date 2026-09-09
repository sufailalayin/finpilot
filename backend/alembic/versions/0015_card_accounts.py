"""Add credit card account metadata.

Revision ID: 0015_card_accounts
Revises: 0014_plan_play_id
"""

from alembic import op
import sqlalchemy as sa

revision = "0015_card_accounts"
down_revision = "0014_plan_play_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("finance_accounts", sa.Column("credit_limit", sa.Numeric(18, 2), nullable=True))
    op.add_column("finance_accounts", sa.Column("card_last4", sa.String(length=4), nullable=True))
    op.add_column("finance_accounts", sa.Column("statement_day", sa.Integer(), nullable=True))
    op.add_column("finance_accounts", sa.Column("payment_due_day", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("finance_accounts", "payment_due_day")
    op.drop_column("finance_accounts", "statement_day")
    op.drop_column("finance_accounts", "card_last4")
    op.drop_column("finance_accounts", "credit_limit")
