"""Merge admin/auth and credit-card bill migration heads.

Revision ID: 0013_merge_admin_auth_credit_card
Revises: 0012_merge_admin_auth, 0012_credit_card_bills
"""

revision = "0013_merge_admin_auth_credit_card"
down_revision = ("0012_merge_admin_auth", "0012_credit_card_bills")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
