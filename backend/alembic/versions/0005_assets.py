"""Add assets.

Revision ID: 0005_assets
Revises: 0004_liabilities
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_assets"
down_revision = "0004_liabilities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("asset_type", sa.String(length=40), nullable=False),
        sa.Column("institution", sa.String(length=140), nullable=True),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=False, server_default="1"),
        sa.Column("cost_basis", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("current_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("maturity_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assets_user_id", "assets", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_assets_user_id", table_name="assets")
    op.drop_table("assets")
