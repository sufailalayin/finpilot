from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.admin import get_current_admin
from app.models.user import AppRelease, User
from app.schemas.admin import AppReleaseResponse, AppReleaseUpdate

router = APIRouter(tags=["app-release"])


async def _get_or_create_release(db: AsyncSession) -> AppRelease:
    release = await db.scalar(select(AppRelease).where(AppRelease.id == 1))
    if release is None:
        release = AppRelease(id=1)
        db.add(release)
        await db.commit()
        await db.refresh(release)
    return release


@router.get("/app-release", response_model=AppReleaseResponse)
async def current_app_release(
    db: AsyncSession = Depends(get_db),
) -> AppReleaseResponse:
    release = await _get_or_create_release(db)
    return AppReleaseResponse.model_validate(release, from_attributes=True)


@router.get("/admin/app-release", response_model=AppReleaseResponse)
async def admin_app_release(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AppReleaseResponse:
    release = await _get_or_create_release(db)
    return AppReleaseResponse.model_validate(release, from_attributes=True)


@router.patch("/admin/app-release", response_model=AppReleaseResponse)
async def update_app_release(
    payload: AppReleaseUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AppReleaseResponse:
    if payload.minimum_build_number > payload.latest_build_number:
        raise HTTPException(
            status_code=400,
            detail="Minimum supported build cannot exceed latest build",
        )

    release = await _get_or_create_release(db)
    for field, value in payload.model_dump().items():
        if field in {"update_url", "release_notes"} and isinstance(value, str):
            value = value.strip() or None
        setattr(release, field, value)

    await db.commit()
    await db.refresh(release)
    return AppReleaseResponse.model_validate(release, from_attributes=True)
