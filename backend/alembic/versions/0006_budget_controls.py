"""Upgrade budgets with rollover and alerts.

Revision ID: 0006_budget_controls
Revises: 0005_assets
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_budget_controls"
down_revision = "0005_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("budgets", sa.Column("rollover_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("budgets", sa.Column("alert_threshold_pct", sa.Numeric(5, 2), nullable=False, server_default="80"))


def downgrade() -> None:
    op.drop_column("budgets", "alert_threshold_pct")
    op.drop_column("budgets", "rollover_enabled")
