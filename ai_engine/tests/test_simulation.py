"""
Unit Tests for Action Simulation Engine.
Verifies policy evaluation, risk matrix, impact deltas, and state sandboxing.
"""

import copy
from pathlib import Path
import sys

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from ai_engine.config import PolicyStatus, Recommendation, RiskLevel
from ai_engine.simulation.engine import SimulationEngine
from ai_engine.simulation.schemas import CustomerState, OrderItem, OrderState


def test_simulation_low_risk_refund_auto_execute():
    """
    Refund <= $1,000 with a clean customer profile should be LOW risk,
    eligible, and recommended for immediate auto-execution.
    """
    order = {
        "order_id": 1001,
        "customer_id": 901,
        "status": "ACTIVE",
        "total_amount": 750.0,
        "payment_status": "PAID",
        "delivery_status": "NOT_SHIPPED",
    }
    customer = {
        "customer_id": 901,
        "previous_complaints": 0,
        "previous_refunds_count": 0,
        "is_flagged": False,
    }

    result = SimulationEngine.simulate(
        action="refund",
        current_state=order,
        customer_state=customer,
        payload={"amount": 750.0},
    )

    assert result.action == "refund"
    assert result.order_id == 1001
    assert result.amount == 750.0
    assert result.policy_status == PolicyStatus.ELIGIBLE.value
    assert result.risk_level == RiskLevel.LOW.value
    assert result.financial_impact == -750.0
    assert result.customer_impact == "positive"
    assert result.human_approval_required is False
    assert result.recommendation == Recommendation.EXECUTE.value
    assert result.simulated_state["payment_status"] == "REFUNDED"


def test_simulation_medium_risk_manager_approval():
    """
    Refund between $1,001 and $5,000 (README example: $2,499)
    should require manager approval and be classified as MEDIUM risk.
    """
    order = OrderState(
        order_id=10291,
        customer_id=9281,
        status="ACTIVE",
        total_amount=2499.0,
        payment_status="PAID",
        items=[OrderItem(product_id="P-101", quantity=1, unit_price=2499.0)],
    )

    result = SimulationEngine.simulate(
        action="refund",
        current_state=order,
        payload={"amount": 2499.0},
    )

    assert result.action == "refund"
    assert result.order_id == 10291
    assert result.amount == 2499.0
    assert result.financial_impact == -2499.0
    assert result.risk_level == RiskLevel.MEDIUM.value
    assert result.human_approval_required is True
    assert result.recommendation == Recommendation.HUMAN_APPROVAL_REQUIRED.value


def test_simulation_high_value_refund_executive_approval():
    """
    Refund > $5,000 (README section 8.1: $25,000)
    must trigger HIGH risk and mandatory human approval.
    """
    order = {
        "order_id": 10999,
        "customer_id": 9999,
        "status": "ACTIVE",
        "total_amount": 25000.0,
        "payment_status": "PAID",
    }

    result = SimulationEngine.simulate(
        action="refund",
        current_state=order,
        payload={"amount": 25000.0},
    )

    assert result.risk_level == RiskLevel.HIGH.value
    assert result.human_approval_required is True
    assert result.recommendation == Recommendation.HUMAN_APPROVAL_REQUIRED.value


def test_simulation_cancel_active_order_with_coupon():
    """
    Cancelling an active order before dispatch should restock inventory,
    invalidate coupon, and be recommended for auto-execution.
    """
    order = {
        "order_id": 2045,
        "customer_id": 812,
        "status": "PROCESSING",
        "total_amount": 350.0,
        "payment_status": "PAID",
        "delivery_status": "NOT_SHIPPED",
        "coupon_code": "SAVE20",
        "is_coupon_applied": True,
        "items": [
            {"product_id": 1, "name": "Headphones", "quantity": 1, "unit_price": 200.0},
            {"product_id": 2, "name": "Case", "quantity": 1, "unit_price": 150.0},
        ],
    }

    result = SimulationEngine.simulate(
        action="cancel_order",
        current_state=order,
    )

    assert result.action == "cancel_order"
    assert result.financial_impact == -350.0
    assert result.inventory_impact == 2
    assert result.coupon_impact == "Coupon becomes invalid"
    assert result.policy_status == PolicyStatus.ELIGIBLE.value
    assert result.recommendation == Recommendation.EXECUTE.value
    assert result.simulated_state["status"] == "CANCELLED"
    assert result.simulated_state["is_coupon_applied"] is False


def test_simulation_cancel_shipped_order_blocked():
    """
    Cancelling an already shipped order violates business policy
    and must be BLOCKED with clear violations.
    """
    order = {
        "order_id": 3081,
        "customer_id": 711,
        "status": "SHIPPED",
        "total_amount": 500.0,
        "delivery_status": "IN_TRANSIT",
    }

    result = SimulationEngine.simulate(
        action="cancel_order",
        current_state=order,
    )

    assert result.policy_status == PolicyStatus.INELIGIBLE.value
    assert result.recommendation == Recommendation.BLOCKED.value
    assert len(result.policy_violations) > 0
    assert any("Cancellation is restricted once dispatched" in v for v in result.policy_violations)


def test_simulation_refund_exceeding_total_balance_blocked():
    """
    Refund exceeding the order balance is invalid and must be blocked.
    """
    order = {
        "order_id": 4012,
        "customer_id": 650,
        "status": "ACTIVE",
        "total_amount": 200.0,
        "refunded_amount": 50.0,
    }

    result = SimulationEngine.simulate(
        action="refund",
        current_state=order,
        payload={"amount": 250.0},
    )

    assert result.policy_status == PolicyStatus.INELIGIBLE.value
    assert result.recommendation == Recommendation.BLOCKED.value
    assert any("exceeds available order balance" in v for v in result.policy_violations)


def test_simulation_flagged_customer():
    """
    Actions on flagged customer accounts require manual review and carry elevated risk.
    """
    order = {
        "order_id": 5011,
        "customer_id": 999,
        "status": "ACTIVE",
        "total_amount": 100.0,
        "payment_status": "PAID",
    }
    customer = {
        "customer_id": 999,
        "is_flagged": True,
    }

    result = SimulationEngine.simulate(
        action="refund",
        current_state=order,
        customer_state=customer,
        payload={"amount": 100.0},
    )

    assert result.risk_level == RiskLevel.HIGH.value
    assert result.human_approval_required is True
    assert result.recommendation == Recommendation.HUMAN_APPROVAL_REQUIRED.value


def test_simulation_state_immutability():
    """
    Ensures the original order dictionary is never modified by the simulation.
    """
    original_order = {
        "order_id": 6012,
        "customer_id": 341,
        "status": "ACTIVE",
        "total_amount": 500.0,
        "payment_status": "PAID",
        "refunded_amount": 0.0,
    }
    order_snapshot = copy.deepcopy(original_order)

    _ = SimulationEngine.simulate(
        action="refund",
        current_state=original_order,
        payload={"amount": 500.0},
    )

    assert original_order == order_snapshot
    assert original_order["status"] == "ACTIVE"
    assert original_order["payment_status"] == "PAID"
    assert original_order["refunded_amount"] == 0.0


def test_simulation_to_dict_matches_readme_spec():
    """
    Ensures result.to_dict() matches the exact contract documented in Section 15 of README.md.
    """
    order = {
        "order_id": 10291,
        "customer_id": 9281,
        "status": "ACTIVE",
        "total_amount": 2499.0,
        "payment_status": "PAID",
        "items": [{"product_id": 101, "quantity": 1, "unit_price": 2499.0}],
    }

    result = SimulationEngine.simulate(
        action="refund",
        current_state=order,
        payload={"amount": 2499.0},
    )

    response_dict = result.to_dict()

    required_keys = [
        "action",
        "order_id",
        "amount",
        "policy_status",
        "risk_level",
        "customer_impact",
        "financial_impact",
        "inventory_impact",
        "human_approval_required",
        "recommendation",
    ]
    for key in required_keys:
        assert key in response_dict, f"Missing key '{key}' in response dictionary"

    assert response_dict["action"] == "refund"
    assert response_dict["order_id"] == 10291
    assert response_dict["amount"] == 2499.0
    assert response_dict["financial_impact"] == -2499.0


def test_simulation_unknown_action_rejected():
    """
    Simulating an unknown or unsupported action must be blocked
    by policy with clear violation explanation.
    """
    order = {
        "order_id": 9001,
        "customer_id": 100,
        "status": "ACTIVE",
        "total_amount": 100.0,
    }

    result = SimulationEngine.simulate(
        action="unsupported_custom_action",
        current_state=order,
    )

    assert result.policy_status == PolicyStatus.INELIGIBLE.value
    assert result.recommendation == Recommendation.BLOCKED.value
    assert any("unrecognized or unsupported" in v for v in result.policy_violations)


def test_simulation_negative_or_zero_refund_rejected():
    """
    Refunds <= $0 must be blocked by policy.
    """
    order = {
        "order_id": 9002,
        "customer_id": 101,
        "status": "ACTIVE",
        "total_amount": 100.0,
    }

    result = SimulationEngine.simulate(
        action="refund",
        current_state=order,
        payload={"amount": -50.0},
    )

    assert result.policy_status == PolicyStatus.INELIGIBLE.value
    assert result.recommendation == Recommendation.BLOCKED.value
    assert any("greater than zero" in v for v in result.policy_violations)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

