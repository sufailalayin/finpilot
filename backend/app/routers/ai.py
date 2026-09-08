from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.ai import AIUsageEvent
from app.models.user import User
from app.schemas.ai import AIAskRequest, AIAskResponse
from app.services.ai_context import build_finance_context
from app.services.ai_provider import get_ai_provider
from app.services.entitlements import has_pro_access

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/ask", response_model=AIAskResponse)
async def ask_finpilot(
    payload: AIAskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIAskResponse:
    if not has_pro_access(user.entitlement):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="FinPilot AI requires an active Pro trial or subscription",
        )

    context = await build_finance_context(db, user.id)
    provider = get_ai_provider()
    answer = await provider.answer(payload.question, context)

    db.add(
        AIUsageEvent(
            user_id=user.id,
            provider=provider.provider_name,
            model=provider.model_name,
            prompt_chars=len(payload.question),
            response_chars=len(answer),
            question_preview=payload.question[:180],
        )
    )
    await db.commit()

    return AIAskResponse(
        answer=answer,
        provider=provider.provider_name,
        model=provider.model_name,
    )
