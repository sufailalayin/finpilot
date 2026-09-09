"""Add persistent login throttling.

Revision ID: 0021_login_throttle
Revises: 0020_liability_accounts
"""

from alembic import op
import sqlalchemy as sa

revision = "0021_login_throttle"
down_revision = "0020_liability_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "login_locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "login_locked_until")
    op.drop_column("users", "failed_login_attempts")
