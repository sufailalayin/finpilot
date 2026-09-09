"""Merge auth OTP and admin operations migration heads.

Revision ID: 0012_merge_admin_auth
Revises: 0011_auth_otp, 0011_admin_ops
"""

revision = "0012_merge_admin_auth"
down_revision = ("0011_auth_otp", "0011_admin_ops")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
