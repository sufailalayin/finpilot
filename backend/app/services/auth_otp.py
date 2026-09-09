import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import AuthOtpChallenge

settings = get_settings()


class OtpCooldownError(RuntimeError):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("OTP resend cooldown active")
        self.retry_after_seconds = retry_after_seconds


class OtpVerificationError(RuntimeError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_code(*, email: str, purpose: str, code: str) -> str:
    message = f"{email.lower().strip()}|{purpose}|{code}".encode()
    return hmac.new(
        settings.jwt_secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


async def issue_otp(
    db: AsyncSession,
    *,
    email: str,
    purpose: str,
) -> tuple[AuthOtpChallenge, str]:
    normalized = email.lower().strip()
    now = _utcnow()

    latest = await db.scalar(
        select(AuthOtpChallenge)
        .where(
            AuthOtpChallenge.email == normalized,
            AuthOtpChallenge.purpose == purpose,
            AuthOtpChallenge.consumed_at.is_(None),
        )
        .order_by(AuthOtpChallenge.created_at.desc())
        .limit(1)
    )

    if latest is not None and latest.resend_available_at > now:
        retry = max(
            1,
            int((latest.resend_available_at - now).total_seconds()),
        )
        raise OtpCooldownError(retry)

    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = AuthOtpChallenge(
        email=normalized,
        purpose=purpose,
        code_hash=_hash_code(
            email=normalized,
            purpose=purpose,
            code=code,
        ),
        expires_at=now + timedelta(minutes=settings.otp_expiry_minutes),
        resend_available_at=now + timedelta(seconds=settings.otp_resend_seconds),
    )
    db.add(challenge)
    await db.flush()
    return challenge, code


async def verify_otp(
    db: AsyncSession,
    *,
    email: str,
    purpose: str,
    code: str,
) -> AuthOtpChallenge:
    normalized = email.lower().strip()
    now = _utcnow()

    challenge = await db.scalar(
        select(AuthOtpChallenge)
        .where(
            AuthOtpChallenge.email == normalized,
            AuthOtpChallenge.purpose == purpose,
            AuthOtpChallenge.consumed_at.is_(None),
        )
        .order_by(AuthOtpChallenge.created_at.desc())
        .limit(1)
    )

    if challenge is None:
        raise OtpVerificationError("Invalid or expired verification code")

    if challenge.expires_at <= now:
        raise OtpVerificationError("Invalid or expired verification code")

    if challenge.attempts >= settings.otp_max_attempts:
        raise OtpVerificationError("Too many incorrect verification attempts")

    expected = _hash_code(
        email=normalized,
        purpose=purpose,
        code=code,
    )
    if not hmac.compare_digest(challenge.code_hash, expected):
        challenge.attempts += 1
        await db.flush()
        raise OtpVerificationError("Invalid or expired verification code")

    challenge.consumed_at = now
    await db.flush()
    return challenge
