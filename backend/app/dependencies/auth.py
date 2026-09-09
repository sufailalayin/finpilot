import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token_claims
from app.db.session import get_db
from app.models.user import EntitlementStatus, User, UserStatus
from app.services.subscriptions import normalize_paid_entitlement
from app.services.trials import normalize_entitlement

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    claims = decode_access_token_claims(credentials.credentials)
    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    try:
        user_id = uuid.UUID(claims["sub"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    result = await db.execute(
        select(User).options(selectinload(User.entitlement)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")
    if claims["ver"] != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

    path = request.url.path
    access_exempt = (
        path.startswith("/api/v1/subscriptions/status")
        or path.startswith("/api/v1/subscriptions/plans")
        or path.startswith("/api/v1/subscriptions/google-play/verify")
        or path.startswith("/api/v1/admin")
        or path.startswith("/api/v1/auth")
        or path.startswith("/api/v1/app-release")
        or path.startswith("/api/v1/security")
    )

    entitlement = user.entitlement
    if entitlement is not None:
        previous_status = entitlement.status
        previous_plan = entitlement.plan_code
        normalize_entitlement(entitlement)
        normalize_paid_entitlement(entitlement)
        if (
            entitlement.status != previous_status
            or entitlement.plan_code != previous_plan
        ):
            await db.commit()

        if (
            not user.is_admin
            and not access_exempt
            and entitlement.status in {
                EntitlementStatus.EXPIRED,
                EntitlementStatus.CANCELLED,
            }
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="FinPilot trial or subscription has ended",
            )
    elif not user.is_admin and not access_exempt:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="FinPilot access entitlement is unavailable",
        )

    return user
