"""Link liabilities to cash and bank accounts.

Revision ID: 0020_liability_accounts
Revises: 0019_receivable_moves
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0020_liability_accounts"
down_revision = "0019_receivable_moves"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("liabilities", sa.Column("funding_account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_liabilities_funding_account_id", "liabilities", "finance_accounts", ["funding_account_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_liabilities_funding_account_id", "liabilities", ["funding_account_id"])

    op.add_column("liability_payments", sa.Column("payment_account_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_liability_payments_account_id", "liability_payments", "finance_accounts", ["payment_account_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_liability_payments_payment_account_id", "liability_payments", ["payment_account_id"])


def downgrade() -> None:
    op.drop_index("ix_liability_payments_payment_account_id", table_name="liability_payments")
    op.drop_constraint("fk_liability_payments_account_id", "liability_payments", type_="foreignkey")
    op.drop_column("liability_payments", "payment_account_id")
    op.drop_index("ix_liabilities_funding_account_id", table_name="liabilities")
    op.drop_constraint("fk_liabilities_funding_account_id", "liabilities", type_="foreignkey")
    op.drop_column("liabilities", "funding_account_id")
