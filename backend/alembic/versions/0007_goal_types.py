"""Upgrade goals with goal type.

Revision ID: 0007_goal_types
Revises: 0006_budget_controls
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_goal_types"
down_revision = "0006_budget_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "savings_goals",
        sa.Column("goal_type", sa.String(length=40), nullable=False, server_default="other"),
    )


def downgrade() -> None:
    op.drop_column("savings_goals", "goal_type")
