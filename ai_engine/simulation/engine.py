"""
Core AI Action Simulation Engine.
Simulates proposed actions on synthetic in-memory state before database commitment.
Strictly adheres to Section 8 & Section 15 of README.md.
"""

import copy
from typing import Any, Dict, Optional, Union

from ai_engine.config import (
    ActionType,
    ImpactType,
    PolicyStatus,
    Recommendation,
    RiskLevel,
)
from ai_engine.simulation.policies import PolicyValidator
from ai_engine.simulation.risk_evaluator import RiskEvaluator
from ai_engine.simulation.schemas import (
    CustomerState,
    OrderState,
    ProposedAction,
    SimulationResult,
)


class SimulationEngine:
    """
    In-memory pre-execution simulation sandbox.
    Calculates deltas across financial, inventory, customer, and policy states.
    """

    @classmethod
    def simulate(
        cls,
        action: Union[str, ProposedAction, Dict[str, Any]],
        current_state: Union[OrderState, Dict[str, Any]],
        customer_state: Optional[Union[CustomerState, Dict[str, Any]]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> SimulationResult:
        """
        Main entry point for simulation.
        Accepts native dictionaries (e.g. from Django DRF request.data) or Pydantic models.

        Args:
            action: Action name (e.g. 'refund', 'cancel_order') or ProposedAction object/dict
            current_state: Current OrderState or dict representation of the order
            customer_state: Optional CustomerState or dict representation of the customer
            payload: Optional extra parameters (e.g. {'amount': 2499.0, 'reason': 'defective'})
        """
        # 1. Parse & validate inputs
        order = (
            current_state
            if isinstance(current_state, OrderState)
            else OrderState.model_validate(current_state)
        )

        customer = (
            customer_state
            if isinstance(customer_state, CustomerState)
            else (
                CustomerState.model_validate(customer_state)
                if customer_state
                else CustomerState(customer_id=order.customer_id)
            )
        )

        if isinstance(action, str):
            action_name = action
            action_amount = payload.get("amount") if payload else None
            action_params = payload or {}
        elif isinstance(action, dict):
            action_name = action.get("action_type") or action.get("action", ActionType.REFUND.value)
            action_amount = action.get("amount")
            action_params = action.get("parameters", {})
        else:
            action_name = action.action_type
            action_amount = action.amount
            action_params = action.parameters

        # 2. Clone state for synthetic sandbox
        simulated_order = copy.deepcopy(order)

        # 3. Simulate state mutations and compute impacts
        financial_impact = 0.0
        inventory_impact = 0
        customer_impact = ImpactType.NEUTRAL.value
        coupon_impact = None
        effective_amount = 0.0

        if action_name == ActionType.REFUND.value:
            effective_amount = (
                float(action_amount)
                if action_amount is not None
                else float(order.total_amount - order.refunded_amount)
            )
            financial_impact = -round(effective_amount, 2)
            inventory_impact = 0
            customer_impact = ImpactType.POSITIVE.value

            simulated_order.refunded_amount += effective_amount
            if simulated_order.refunded_amount >= simulated_order.total_amount:
                simulated_order.payment_status = "REFUNDED"

        elif action_name == ActionType.CANCEL_ORDER.value:
            effective_amount = float(order.total_amount - order.refunded_amount)
            # If payment was completed, refund is also factored into cancellation
            if order.payment_status == "PAID":
                financial_impact = -round(effective_amount, 2)
                simulated_order.payment_status = "REFUNDED"
                simulated_order.refunded_amount = order.total_amount
            else:
                financial_impact = 0.0

            # Restock items back into inventory
            total_items = sum(item.quantity for item in order.items) if order.items else 1
            inventory_impact = total_items
            customer_impact = ImpactType.POSITIVE.value
            simulated_order.status = "CANCELLED"

            if order.coupon_code or order.is_coupon_applied:
                coupon_impact = "Coupon becomes invalid"
                simulated_order.is_coupon_applied = False

        elif action_name == ActionType.REORDER_ITEM.value:
            total_items = sum(item.quantity for item in order.items) if order.items else 1
            inventory_impact = -total_items
            financial_impact = 0.0
            customer_impact = ImpactType.POSITIVE.value
            simulated_order.delivery_status = "PROCESSING_REPLACEMENT"

        else:
            customer_impact = ImpactType.NEUTRAL.value

        # 4. Evaluate deterministic business policy
        policy_eval = PolicyValidator.evaluate(
            action_type=action_name,
            order=order,
            customer=customer,
            amount=effective_amount,
        )

        # 5. Evaluate risk and approval necessity
        risk_level, human_approval_required, risk_factors = RiskEvaluator.evaluate(
            action_type=action_name,
            order=order,
            customer=customer,
            policy=policy_eval,
            amount=effective_amount,
        )

        # 6. Determine final actionable recommendation
        if not policy_eval.is_eligible:
            recommendation = Recommendation.BLOCKED.value
            policy_status = PolicyStatus.INELIGIBLE.value
        elif human_approval_required:
            recommendation = Recommendation.HUMAN_APPROVAL_REQUIRED.value
            policy_status = (
                PolicyStatus.REQUIRES_REVIEW.value
                if policy_eval.status == PolicyStatus.REQUIRES_REVIEW.value
                else PolicyStatus.ELIGIBLE.value
            )
        else:
            recommendation = Recommendation.EXECUTE.value
            policy_status = PolicyStatus.ELIGIBLE.value

        # Aggregate reasons and explanations
        reasons = list(dict.fromkeys(policy_eval.reasons + risk_factors))

        return SimulationResult(
            action=action_name,
            order_id=order.order_id,
            amount=effective_amount,
            policy_status=policy_status,
            risk_level=risk_level,
            customer_impact=customer_impact,
            financial_impact=financial_impact,
            inventory_impact=inventory_impact,
            coupon_impact=coupon_impact,
            human_approval_required=human_approval_required,
            recommendation=recommendation,
            reasons=reasons,
            policy_violations=policy_eval.violations,
            simulated_state=simulated_order.model_dump(),
        )
