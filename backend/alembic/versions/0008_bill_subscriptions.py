"""Upgrade bill reminders and subscriptions.

Revision ID: 0008_bill_subscriptions
Revises: 0007_goal_types
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_bill_subscriptions"
down_revision = "0007_goal_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bill_reminders", sa.Column("bill_type", sa.String(length=30), nullable=False, server_default="bill"))
    op.add_column("bill_reminders", sa.Column("provider", sa.String(length=120), nullable=True))
    op.add_column("bill_reminders", sa.Column("reminder_days_before", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("bill_reminders", sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("bill_reminders", "auto_renew")
    op.drop_column("bill_reminders", "reminder_days_before")
    op.drop_column("bill_reminders", "provider")
    op.drop_column("bill_reminders", "bill_type")
