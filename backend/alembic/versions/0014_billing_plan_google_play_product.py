"""Add Google Play product mapping to billing plans.

Revision ID: 0014_billing_plan_google_play_product
Revises: 0013_merge_admin_auth_credit_card
"""

from alembic import op
import sqlalchemy as sa

revision = "0014_plan_play_id"
down_revision = "0013_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "billing_plans",
        sa.Column("google_play_product_id", sa.String(length=200), nullable=True),
    )
    op.create_unique_constraint(
        "uq_billing_plans_google_play_product_id",
        "billing_plans",
        ["google_play_product_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_billing_plans_google_play_product_id",
        "billing_plans",
        type_="unique",
    )
    op.drop_column("billing_plans", "google_play_product_id")
