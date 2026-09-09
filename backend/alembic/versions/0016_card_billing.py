"""Add credit card statement payment fields.

Revision ID: 0016_card_billing
Revises: 0015_card_accounts
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0016_card_billing"
down_revision = "0015_card_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bill_reminders", sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("bill_reminders", sa.Column("minimum_due", sa.Numeric(18, 2), nullable=True))
    op.add_column("bill_reminders", sa.Column("paid_amount", sa.Numeric(18, 2), nullable=False, server_default="0"))
    op.create_foreign_key("fk_bill_reminders_account_id", "bill_reminders", "finance_accounts", ["account_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_bill_reminders_account_id", "bill_reminders", ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_bill_reminders_account_id", table_name="bill_reminders")
    op.drop_constraint("fk_bill_reminders_account_id", "bill_reminders", type_="foreignkey")
    op.drop_column("bill_reminders", "paid_amount")
    op.drop_column("bill_reminders", "minimum_due")
    op.drop_column("bill_reminders", "account_id")
