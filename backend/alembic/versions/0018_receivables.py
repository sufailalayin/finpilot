"""Add receivables and repayment history.

Revision ID: 0018_receivables
Revises: 0017_app_release
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0018_receivables"
down_revision = "0017_app_release"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "receivables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_name", sa.String(length=140), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("original_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("amount_received", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("given_on", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_receivables_user_id", "receivables", ["user_id"])

    op.create_table(
        "receivable_repayments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("receivable_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("received_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["receivable_id"], ["receivables.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_receivable_repayments_receivable_id", "receivable_repayments", ["receivable_id"])
    op.create_index("ix_receivable_repayments_user_id", "receivable_repayments", ["user_id"])
    op.create_index("ix_receivable_repayments_received_on", "receivable_repayments", ["received_on"])


def downgrade() -> None:
    op.drop_table("receivable_repayments")
    op.drop_table("receivables")
