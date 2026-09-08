"""Add liabilities and liability payments.

Revision ID: 0004_liabilities
Revises: 0003_automation
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_liabilities"
down_revision = "0003_automation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "liabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("liability_type", sa.String(length=40), nullable=False),
        sa.Column("lender", sa.String(length=140), nullable=True),
        sa.Column("original_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("outstanding_principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_rate", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("emi_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("next_due_on", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_liabilities_user_id", "liabilities", ["user_id"])

    op.create_table(
        "liability_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("liability_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("liabilities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("principal_component", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_component", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_liability_payments_liability_id", "liability_payments", ["liability_id"])
    op.create_index("ix_liability_payments_user_id", "liability_payments", ["user_id"])
    op.create_index("ix_liability_payments_paid_on", "liability_payments", ["paid_on"])


def downgrade() -> None:
    op.drop_index("ix_liability_payments_paid_on", table_name="liability_payments")
    op.drop_index("ix_liability_payments_user_id", table_name="liability_payments")
    op.drop_index("ix_liability_payments_liability_id", table_name="liability_payments")
    op.drop_table("liability_payments")
    op.drop_index("ix_liabilities_user_id", table_name="liabilities")
    op.drop_table("liabilities")
