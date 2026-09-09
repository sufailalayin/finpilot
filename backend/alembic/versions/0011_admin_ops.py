"""Add billing plans, user locations and payment records.

Revision ID: 0011_admin_ops
Revises: 0010_admin_controls
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_admin_ops"
down_revision = "0010_admin_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=60), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("access_level", sa.String(length=20), nullable=False),
        sa.Column("billing_period", sa.String(length=20), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_billing_plans_code", "billing_plans", ["code"])

    op.create_table(
        "user_locations",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("last_ip_address", sa.String(length=64), nullable=True),
        sa.Column("last_user_agent", sa.String(length=500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "payment_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("billing_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("billing_plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("reference", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by_admin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payment_records_user_id", "payment_records", ["user_id"])
    op.create_index("ix_payment_records_billing_plan_id", "payment_records", ["billing_plan_id"])
    op.create_index("ix_payment_records_reference", "payment_records", ["reference"])
    op.create_index("ix_payment_records_recorded_by_admin_id", "payment_records", ["recorded_by_admin_id"])
    op.create_index("ix_payment_records_created_at", "payment_records", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_payment_records_created_at", table_name="payment_records")
    op.drop_index("ix_payment_records_recorded_by_admin_id", table_name="payment_records")
    op.drop_index("ix_payment_records_reference", table_name="payment_records")
    op.drop_index("ix_payment_records_billing_plan_id", table_name="payment_records")
    op.drop_index("ix_payment_records_user_id", table_name="payment_records")
    op.drop_table("payment_records")
    op.drop_table("user_locations")
    op.drop_index("ix_billing_plans_code", table_name="billing_plans")
    op.drop_table("billing_plans")
