import argparse
import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import EntitlementStatus, PlanCode, User, UserStatus
from app.services.subscriptions import ensure_user_entitlement


async def create_admin(email: str, password: str, full_name: str | None) -> None:
    normalized_email = email.strip().lower()

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(
            select(User)
            .options(selectinload(User.entitlement))
            .where(User.email == normalized_email)
        )

        if existing is None:
            user = User(
                email=normalized_email,
                full_name=full_name.strip() if full_name else None,
                password_hash=hash_password(password),
                is_admin=True,
                email_verified=True,
                status=UserStatus.ACTIVE,
            )
            db.add(user)
            entitlement = ensure_user_entitlement(user)
            entitlement.plan_code = PlanCode.PRO
            entitlement.status = EntitlementStatus.ACTIVE
            entitlement.trial_started_at = None
            entitlement.trial_ends_at = None
            await db.commit()
            print("ADMIN CREATED:", normalized_email)
            return

        existing.is_admin = True
        existing.email_verified = True
        existing.status = UserStatus.ACTIVE
        existing.failed_login_attempts = 0
        existing.login_locked_until = None
        if full_name:
            existing.full_name = full_name.strip()
        if password:
            existing.password_hash = hash_password(password)
            existing.token_version += 1

        entitlement = ensure_user_entitlement(existing)
        entitlement.plan_code = PlanCode.PRO
        entitlement.status = EntitlementStatus.ACTIVE
        entitlement.trial_started_at = None
        entitlement.trial_ends_at = None

        await db.commit()
        print("ADMIN UPDATED:", normalized_email)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote a FinPilot admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    if len(args.password) < 8:
        raise SystemExit("Password must be at least 8 characters")

    asyncio.run(create_admin(args.email, args.password, args.name))


if __name__ == "__main__":
    main()
