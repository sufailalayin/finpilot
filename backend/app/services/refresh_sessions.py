import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.user import RefreshSession, User, UserStatus

settings = get_settings()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def issue_refresh_session(
    db: AsyncSession,
    *,
    user: User,
) -> tuple[RefreshSession, str]:
    now = _utcnow()
    token = secrets.token_urlsafe(48)
    session = RefreshSession(
        user_id=user.id,
        token_hash=_hash_token(token),
        token_version=user.token_version,
        expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    await db.flush()
    return session, token


async def rotate_refresh_session(
    db: AsyncSession,
    *,
    token: str,
) -> tuple[User, str] | None:
    now = _utcnow()
    session = await db.scalar(
        select(RefreshSession)
        .where(RefreshSession.token_hash == _hash_token(token))
        .with_for_update()
    )
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        return None

    user = await db.scalar(
        select(User)
        .options(selectinload(User.entitlement))
        .where(User.id == session.user_id)
    )
    if (
        user is None
        or user.status != UserStatus.ACTIVE
        or session.token_version != user.token_version
    ):
        session.revoked_at = now
        await db.flush()
        return None

    session.revoked_at = now
    session.last_used_at = now
    _, new_token = await issue_refresh_session(db, user=user)
    return user, new_token


async def revoke_refresh_token(
    db: AsyncSession,
    *,
    token: str,
) -> None:
    now = _utcnow()
    session = await db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == _hash_token(token)
        )
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = now
        await db.flush()


async def revoke_all_refresh_sessions(
    db: AsyncSession,
    *,
    user_id,
) -> None:
    now = _utcnow()
    await db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
