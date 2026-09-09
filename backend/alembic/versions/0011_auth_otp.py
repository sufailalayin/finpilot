"""Add email verification and OTP challenges.

Revision ID: 0011_auth_otp
Revises: 0010_admin_controls
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_auth_otp"
down_revision = "0010_admin_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.create_table(
        "auth_otp_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resend_available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_otp_challenges_email", "auth_otp_challenges", ["email"])
    op.create_index("ix_auth_otp_challenges_purpose", "auth_otp_challenges", ["purpose"])
    op.create_index("ix_auth_otp_challenges_created_at", "auth_otp_challenges", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_auth_otp_challenges_created_at", table_name="auth_otp_challenges")
    op.drop_index("ix_auth_otp_challenges_purpose", table_name="auth_otp_challenges")
    op.drop_index("ix_auth_otp_challenges_email", table_name="auth_otp_challenges")
    op.drop_table("auth_otp_challenges")
    op.drop_column("users", "email_verified")
