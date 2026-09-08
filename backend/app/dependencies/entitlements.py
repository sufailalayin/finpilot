from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.entitlements import has_pro_access


async def require_pro_user(
    user: User = Depends(get_current_user),
) -> User:
    if not has_pro_access(user.entitlement):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="This feature requires FinPilot Pro",
        )
    return user
