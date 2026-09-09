from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import SecurityAuditEvent, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    GenericAuthMessage,
    LoginRequest,
    OtpRequestResponse,
    OtpVerifyRequest,
    RegisterRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_otp import (
    OtpCooldownError,
    OtpVerificationError,
    issue_otp,
    verify_otp,
)
from app.services.default_categories import build_default_categories
from app.services.email_delivery import EmailDeliveryError, send_otp_email
from app.services.trials import create_trial_entitlement, normalize_entitlement

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host[:64]
    return None


def _user_agent(request: Request) -> str | None:
    value = request.headers.get("user-agent")
    return value[:500] if value else None


def _otp_response(email: str, message: str) -> OtpRequestResponse:
    return OtpRequestResponse(
        email=email,
        expires_in_seconds=settings.otp_expiry_minutes * 60,
        resend_after_seconds=settings.otp_resend_seconds,
        message=message,
    )


async def _send_signup_otp(
    *,
    db: AsyncSession,
    email: str,
) -> None:
    try:
        _, code = await issue_otp(db, email=email, purpose="signup")
    except OtpCooldownError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {exc.retry_after_seconds} seconds before requesting another code",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc

    try:
        await send_otp_email(
            to_email=email,
            code=code,
            purpose="signup",
        )
    except EmailDeliveryError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send verification email right now",
        ) from exc


@router.post(
    "/register",
    response_model=OtpRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> OtpRequestResponse:
    email = payload.email.lower().strip()
    result = await db.execute(
        select(User)
        .options(selectinload(User.entitlement))
        .where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is not None and user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if user is None:
        user = User(
            email=email,
            full_name=payload.full_name.strip() if payload.full_name else None,
            password_hash=hash_password(payload.password),
            email_verified=False,
        )
        db.add(user)
        await db.flush()
    else:
        user.full_name = (
            payload.full_name.strip()
            if payload.full_name
            else user.full_name
        )
        user.password_hash = hash_password(payload.password)

    await _send_signup_otp(db=db, email=email)

    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="signup_otp_sent",
            description="Signup verification code requested.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()

    return _otp_response(
        email,
        "We sent a 6-digit verification code to your email.",
    )


@router.post("/register/resend", response_model=OtpRequestResponse)
async def resend_register_otp(
    payload: ResendOtpRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> OtpRequestResponse:
    email = payload.email.lower().strip()
    user = await db.scalar(select(User).where(User.email == email))

    if user is None or user.email_verified:
        return _otp_response(
            email,
            "If verification is pending, a new code will be sent when allowed.",
        )

    await _send_signup_otp(db=db, email=email)
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="signup_otp_resent",
            description="Signup verification code resent.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()

    return _otp_response(
        email,
        "A new verification code was sent.",
    )


@router.post("/register/verify", response_model=TokenResponse)
async def verify_register_otp(
    payload: OtpVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    email = payload.email.lower().strip()

    try:
        await verify_otp(
            db,
            email=email,
            purpose="signup",
            code=payload.code,
        )
    except OtpVerificationError as exc:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await db.execute(
        select(User)
        .options(selectinload(User.entitlement))
        .where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    if not user.email_verified:
        user.email_verified = True
        if user.entitlement is None:
            user.entitlement = create_trial_entitlement()
        db.add_all(build_default_categories(user.id))

    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="email_verified",
            description="Signup email verified successfully.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()

    result = await db.execute(
        select(User)
        .options(selectinload(User.entitlement))
        .where(User.id == user.id)
    )
    user = result.scalar_one()

    return TokenResponse(
        access_token=create_access_token(
            str(user.id),
            user.token_version,
        ),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    email = payload.email.lower().strip()
    result = await db.execute(
        select(User)
        .options(selectinload(User.entitlement))
        .where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )

    if user.entitlement is not None:
        previous_status = user.entitlement.status
        normalize_entitlement(user.entitlement)
        if user.entitlement.status != previous_status:
            await db.commit()

    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="login_success",
            description="Successful sign in.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(
            str(user.id),
            user.token_version,
        ),
        user=UserResponse.model_validate(user),
    )


@router.post("/password/forgot", response_model=GenericAuthMessage)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> GenericAuthMessage:
    email = payload.email.lower().strip()
    user = await db.scalar(select(User).where(User.email == email))

    if user is not None and user.email_verified:
        try:
            _, code = await issue_otp(
                db,
                email=email,
                purpose="password_reset",
            )
            await send_otp_email(
                to_email=email,
                code=code,
                purpose="password_reset",
            )
            db.add(
                SecurityAuditEvent(
                    user_id=user.id,
                    event_type="password_reset_otp_sent",
                    description="Password reset verification code requested.",
                    ip_address=_request_ip(request),
                    user_agent=_user_agent(request),
                )
            )
            await db.commit()
        except OtpCooldownError:
            await db.rollback()
        except EmailDeliveryError:
            await db.rollback()

    return GenericAuthMessage(
        message=(
            "If an account exists for that email, "
            "a password reset code has been sent."
        )
    )


@router.post("/password/reset", response_model=GenericAuthMessage)
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> GenericAuthMessage:
    email = payload.email.lower().strip()

    try:
        await verify_otp(
            db,
            email=email,
            purpose="password_reset",
            code=payload.code,
        )
    except OtpVerificationError as exc:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1

    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="password_reset",
            description=(
                "Password reset completed and previous sessions revoked."
            ),
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()

    return GenericAuthMessage(
        message="Password changed successfully. Please sign in again.",
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
