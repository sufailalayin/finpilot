from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def lock_seconds_remaining(
    user: User,
    *,
    now: datetime | None = None,
) -> int:
    now = now or utcnow()
    if user.login_locked_until is None or user.login_locked_until <= now:
        return 0
    return max(1, int((user.login_locked_until - now).total_seconds()))


def record_login_failure(
    user: User,
    *,
    now: datetime | None = None,
) -> None:
    now = now or utcnow()
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.login_max_attempts:
        user.login_locked_until = now + timedelta(
            minutes=settings.login_lock_minutes,
        )
        user.failed_login_attempts = 0


def clear_login_failures(user: User) -> None:
    user.failed_login_attempts = 0
    user.login_locked_until = None
