"""Add recurring rules and bill reminders.

Revision ID: 0003_automation
Revises: 0002_play_product
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_automation"
down_revision = "0002_play_product"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recurring_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("finance_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("next_due_on", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recurring_rules_user_id", "recurring_rules", ["user_id"])
    op.create_index("ix_recurring_rules_account_id", "recurring_rules", ["account_id"])
    op.create_index("ix_recurring_rules_next_due_on", "recurring_rules", ["next_due_on"])

    op.create_table(
        "bill_reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="once"),
        sa.Column("is_paid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_bill_reminders_user_id", "bill_reminders", ["user_id"])
    op.create_index("ix_bill_reminders_due_on", "bill_reminders", ["due_on"])


def downgrade() -> None:
    op.drop_index("ix_bill_reminders_due_on", table_name="bill_reminders")
    op.drop_index("ix_bill_reminders_user_id", table_name="bill_reminders")
    op.drop_table("bill_reminders")
    op.drop_index("ix_recurring_rules_next_due_on", table_name="recurring_rules")
    op.drop_index("ix_recurring_rules_account_id", table_name="recurring_rules")
    op.drop_index("ix_recurring_rules_user_id", table_name="recurring_rules")
    op.drop_table("recurring_rules")
