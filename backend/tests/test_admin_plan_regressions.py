from decimal import Decimal
from uuid import uuid4

from app.models.user import Entitlement, EntitlementStatus, PlanCode, User, UserStatus
from app.routers.admin import _state
from app.schemas.admin import AdminBillingPlanCreate, AdminUserUpdate


def test_billing_plan_schema_accepts_google_play_product_id():
    payload = AdminBillingPlanCreate(
        code="pro_monthly",
        name="Pro Monthly",
        access_level="pro",
        billing_period="monthly",
        google_play_product_id="finpilot_pro_monthly",
        price=Decimal("149.50"),
        currency="INR",
    )

    assert payload.google_play_product_id == "finpilot_pro_monthly"
    assert payload.price == Decimal("149.50")


def test_admin_state_tracks_billing_plan_changes():
    first_plan_id = uuid4()
    second_plan_id = uuid4()
    user = User(
        email="admin-plan-test@example.com",
        password_hash="not-used",
        full_name="Plan Test",
        status=UserStatus.ACTIVE,
    )
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.ACTIVE,
        billing_plan_id=first_plan_id,
    )

    before = _state(user, entitlement)
    entitlement.billing_plan_id = second_plan_id
    after = _state(user, entitlement)

    assert before["billing_plan_id"] == str(first_plan_id)
    assert after["billing_plan_id"] == str(second_plan_id)
    assert before != after


def test_admin_update_can_explicitly_clear_billing_plan():
    payload = AdminUserUpdate(
        billing_plan_id=None,
        reason="Clear custom plan",
    )

    assert "billing_plan_id" in payload.model_fields_set
    assert payload.billing_plan_id is None
