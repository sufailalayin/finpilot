"""Store Google Play product id on entitlements.

Revision ID: 0002_play_product
Revises: 0001_initial_core
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_play_product"
down_revision = "0001_initial_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "entitlements",
        sa.Column("provider_product_id", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("entitlements", "provider_product_id")
