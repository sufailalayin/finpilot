"""Publish FinPilot 1.2.0 build 8 through the app update channel.

Revision ID: 0028_publish_app_release_1_2_0
Revises: 0027_finance_account_archive
"""

from alembic import op


revision = "0028_publish_app_release_1_2_0"
down_revision = "0027_finance_account_archive"
branch_labels = None
depends_on = None

UPDATE_URL = (
    "https://github.com/sufailalayin/finpilot/releases/download/"
    "v1.2.0-build8/FinPilot-1.2.0-build8-production.apk"
)

RELEASE_NOTES = """FinPilot 1.2.0 build 8

- Redesigned Home screen account display with compact candy-chip cards showing individual account names, account types, and balances.
- Added support for Outside / External transfers with full directional accounting and transaction records.
- Enhanced real-time entitlement synchronization when Pro subscriptions are updated.
- Verified financial calculations, net worth accuracy, and decimal precision throughout all modules."""


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE app_release
        SET
            latest_version = '1.2.0',
            latest_build_number = 8,
            update_url = '{UPDATE_URL}',
            release_notes = '{RELEASE_NOTES.replace("'", "''")}',
            distribution = 'apk',
            is_update_enabled = true,
            updated_at = now()
        WHERE id = 1
          AND latest_build_number < 8
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE app_release
        SET
            latest_version = '1.1.4',
            latest_build_number = 7,
            updated_at = now()
        WHERE id = 1
          AND latest_version = '1.2.0'
          AND latest_build_number = 8
        """
    )
