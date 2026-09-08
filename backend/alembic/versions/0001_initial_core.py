"""Initial FinPilot core schema.

Revision ID: 0001_initial_core
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_status = sa.Enum("ACTIVE", "SUSPENDED", "DELETED", name="user_status")
    plan_code = sa.Enum("FREE", "PRO", name="plan_code")
    entitlement_status = sa.Enum("TRIAL", "ACTIVE", "EXPIRED", "CANCELLED", name="entitlement_status")
    account_type = sa.Enum("CASH", "BANK", "CARD", "WALLET", "OTHER", name="account_type")
    category_transaction_type = sa.Enum("INCOME", "EXPENSE", "TRANSFER", name="category_transaction_type")
    transaction_type = sa.Enum("INCOME", "EXPENSE", "TRANSFER", name="transaction_type")

    user_status.create(op.get_bind(), checkfirst=True)
    plan_code.create(op.get_bind(), checkfirst=True)
    entitlement_status.create(op.get_bind(), checkfirst=True)
    account_type.create(op.get_bind(), checkfirst=True)
    category_transaction_type.create(op.get_bind(), checkfirst=True)
    transaction_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("status", user_status, nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_code", plan_code, nullable=False),
        sa.Column("status", entitlement_status, nullable=False),
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_entitlements_user_id", "entitlements", ["user_id"], unique=True)

    op.create_table(
        "finance_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("account_type", account_type, nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("opening_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_finance_accounts_user_id", "finance_accounts", ["user_id"])

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("transaction_type", category_transaction_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("finance_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("merchant", sa.String(length=120), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])
    op.create_index("ix_transactions_occurred_on", "transactions", ["occurred_on"])

    op.create_table(
        "budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_budgets_category_id", "budgets", ["category_id"])

    op.create_table(
        "savings_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("target_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("current_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_savings_goals_user_id", "savings_goals", ["user_id"])

    op.create_table(
        "ai_usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("prompt_chars", sa.Integer(), nullable=False),
        sa.Column("response_chars", sa.Integer(), nullable=False),
        sa.Column("question_preview", sa.String(length=180), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_usage_events_user_id", "ai_usage_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_events_user_id", table_name="ai_usage_events")
    op.drop_table("ai_usage_events")
    op.drop_index("ix_savings_goals_user_id", table_name="savings_goals")
    op.drop_table("savings_goals")
    op.drop_index("ix_budgets_category_id", table_name="budgets")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_table("budgets")
    op.drop_index("ix_transactions_occurred_on", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_finance_accounts_user_id", table_name="finance_accounts")
    op.drop_table("finance_accounts")
    op.drop_index("ix_entitlements_user_id", table_name="entitlements")
    op.drop_table("entitlements")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    sa.Enum(name="transaction_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="category_transaction_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="account_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="entitlement_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="plan_code").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_status").drop(op.get_bind(), checkfirst=True)
