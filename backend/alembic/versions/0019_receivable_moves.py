"""Add receivable movement ledger.

Revision ID: 0019_receivable_moves
Revises: 0018_receivables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019_receivable_moves"
down_revision = "0018_receivables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "receivable_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("destination_type", sa.String(length=20), nullable=False),
        sa.Column("source_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_receivable_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination_receivable_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_account_id"], ["finance_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["destination_account_id"], ["finance_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_receivable_id"], ["receivables.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["destination_receivable_id"], ["receivables.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_receivable_movements_user_id", "receivable_movements", ["user_id"])
    op.create_index("ix_receivable_movements_source_account_id", "receivable_movements", ["source_account_id"])
    op.create_index("ix_receivable_movements_destination_account_id", "receivable_movements", ["destination_account_id"])
    op.create_index("ix_receivable_movements_source_receivable_id", "receivable_movements", ["source_receivable_id"])
    op.create_index("ix_receivable_movements_destination_receivable_id", "receivable_movements", ["destination_receivable_id"])
    op.create_index("ix_receivable_movements_occurred_on", "receivable_movements", ["occurred_on"])


def downgrade() -> None:
    op.drop_table("receivable_movements")
