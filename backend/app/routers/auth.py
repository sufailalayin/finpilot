from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.default_categories import build_default_categories
from app.services.trials import create_trial_entitlement, normalize_entitlement

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower().strip()
    existing = await db.scalar(select(User.id).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email,
        full_name=payload.full_name.strip() if payload.full_name else None,
        password_hash=hash_password(payload.password),
    )
    user.entitlement = create_trial_entitlement()

    db.add(user)
    await db.flush()
    db.add_all(build_default_categories(user.id))
    await db.commit()

    result = await db.execute(
        select(User).options(selectinload(User.entitlement)).where(User.id == user.id)
    )
    user = result.scalar_one()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower().strip()
    result = await db.execute(
        select(User).options(selectinload(User.entitlement)).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.entitlement is not None:
        previous_status = user.entitlement.status
        normalize_entitlement(user.entitlement)
        if user.entitlement.status != previous_status:
            await db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if user.entitlement is not None:
        previous_status = user.entitlement.status
        normalize_entitlement(user.entitlement)
        if user.entitlement.status != previous_status:
            await db.commit()
    return UserResponse.model_validate(user)
