"""Add admin action logs.

Revision ID: 0010_admin_controls
Revises: 0009_security_privacy
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_admin_controls"
down_revision = "0009_security_privacy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_action_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "actor_admin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_admin_action_logs_actor_admin_id", "admin_action_logs", ["actor_admin_id"])
    op.create_index("ix_admin_action_logs_target_user_id", "admin_action_logs", ["target_user_id"])
    op.create_index("ix_admin_action_logs_action", "admin_action_logs", ["action"])
    op.create_index("ix_admin_action_logs_created_at", "admin_action_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_admin_action_logs_created_at", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_action", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_target_user_id", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_actor_admin_id", table_name="admin_action_logs")
    op.drop_table("admin_action_logs")
