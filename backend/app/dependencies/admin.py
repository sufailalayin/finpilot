from fastapi import Depends, HTTPException, Request, status

from app.dependencies.auth import get_current_user
from app.models.user import User


async def get_current_admin(
    request: Request,
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    claims = getattr(request.state, "token_claims", {})
    if claims.get("admin_mfa") is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator MFA verification required",
        )
    return user
