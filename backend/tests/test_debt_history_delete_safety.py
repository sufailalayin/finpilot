import inspect

from app.routers.liabilities import _liability_delete_blocker_count, delete_liability
from app.routers.receivables import _receivable_delete_blocker_count, delete_receivable


def test_receivable_delete_blocker_covers_repayments_and_movements():
    source = inspect.getsource(_receivable_delete_blocker_count)

    assert "ReceivableRepayment.user_id == user_id" in source
    assert "ReceivableRepayment.receivable_id == receivable_id" in source
    assert "ReceivableMovement.user_id == user_id" in source
    assert "ReceivableMovement.source_receivable_id == receivable_id" in source
    assert "ReceivableMovement.destination_receivable_id == receivable_id" in source


def test_receivable_delete_uses_history_blocker():
    source = inspect.getsource(delete_receivable)

    assert "await _receivable_delete_blocker_count(" in source
    assert "repayment or movement history" in source


def test_liability_delete_blocker_covers_payment_history():
    source = inspect.getsource(_liability_delete_blocker_count)

    assert "LiabilityPayment.user_id == user_id" in source
    assert "LiabilityPayment.liability_id == liability_id" in source


def test_liability_delete_uses_history_blocker():
    source = inspect.getsource(delete_liability)

    assert "await _liability_delete_blocker_count(" in source
    assert "payment history" in source
