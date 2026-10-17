"""
Business Policy Validation Rules for AI Actions.
Enforces deterministic policies defined in README.md Section 10.
"""

from typing import Optional

from ai_engine.config import (
    ActionType,
    AUTO_REFUND_LIMIT,
    HIGH_VALUE_THRESHOLD,
    MANAGER_APPROVAL_LIMIT,
    MAX_ALLOWED_PREVIOUS_REFUNDS,
    PolicyStatus,
    RESTRICTED_CANCELLATION_STATUSES,
)
from ai_engine.simulation.schemas import (
    CustomerState,
    OrderState,
    PolicyEvaluation,
)


class PolicyValidator:
    """
    Deterministic rule engine that validates proposed actions
    against business policies and limits.
    """

    @classmethod
    def evaluate(
        cls,
        action_type: str,
        order: OrderState,
        customer: Optional[CustomerState] = None,
        amount: Optional[float] = None,
    ) -> PolicyEvaluation:
        """
        Dispatches policy validation to the specific handler based on action type.
        """
        customer = customer or CustomerState(customer_id=order.customer_id)

        if action_type == ActionType.REFUND.value:
            effective_amount = amount if amount is not None else order.total_amount
            return cls.validate_refund(order, customer, effective_amount)

        elif action_type == ActionType.CANCEL_ORDER.value:
            return cls.validate_cancellation(order, customer)

        elif action_type == ActionType.REORDER_ITEM.value:
            return cls.validate_reorder(order, customer)

        elif action_type in (ActionType.EXPEDITE_SHIPPING.value, ActionType.PROACTIVE_NOTIFICATION.value):
            return PolicyEvaluation(
                policy_name=f"Standard policy check for {action_type}",
                status=PolicyStatus.ELIGIBLE.value,
                is_eligible=True,
                requires_human_approval=False,
                reasons=[f"Action '{action_type}' is supported and passed standard baseline check."],
            )

        else:
            return PolicyEvaluation(
                policy_name=f"Unknown Action Policy",
                status=PolicyStatus.INELIGIBLE.value,
                is_eligible=False,
                requires_human_approval=True,
                violations=[f"Action type '{action_type}' is unrecognized or unsupported by the policy engine."],
            )

    @classmethod
    def validate_refund(
        cls,
        order: OrderState,
        customer: CustomerState,
        refund_amount: float,
    ) -> PolicyEvaluation:
        reasons = []
        violations = []
        requires_approval = False
        is_eligible = True

        # 1. Basic amount validation
        if refund_amount <= 0:
            is_eligible = False
            violations.append(f"Refund amount (${refund_amount:.2f}) must be greater than zero.")

        remaining_balance = order.total_amount - order.refunded_amount
        if refund_amount > remaining_balance + 0.001:
            is_eligible = False
            violations.append(
                f"Requested refund (${refund_amount:.2f}) exceeds available order balance (${remaining_balance:.2f})."
            )

        if order.payment_status == "REFUNDED" and remaining_balance <= 0:
            is_eligible = False
            violations.append("Order is already fully refunded.")

        # 2. Flagged customer checks
        if customer.is_flagged or customer.account_status == "FLAGGED":
            requires_approval = True
            reasons.append("Customer account is flagged: manual verification required.")

        # 3. Frequency / history check
        if customer.previous_refunds_count >= MAX_ALLOWED_PREVIOUS_REFUNDS:
            requires_approval = True
            reasons.append(
                f"High refund frequency ({customer.previous_refunds_count} prior refunds): escalation required."
            )

        # 4. Financial thresholds (Section 10)
        if refund_amount > HIGH_VALUE_THRESHOLD:
            requires_approval = True
            reasons.append(
                f"High-value refund (${refund_amount:.2f} > ${HIGH_VALUE_THRESHOLD:.2f}): executive human approval required."
            )
        elif refund_amount > AUTO_REFUND_LIMIT:
            requires_approval = True
            reasons.append(
                f"Refund amount (${refund_amount:.2f}) exceeds auto-approval threshold (${AUTO_REFUND_LIMIT:.2f}): manager approval required."
            )
        else:
            reasons.append(f"Refund amount (${refund_amount:.2f}) is within automated threshold (<= ${AUTO_REFUND_LIMIT:.2f}).")

        status = (
            PolicyStatus.INELIGIBLE.value
            if not is_eligible
            else (PolicyStatus.REQUIRES_REVIEW.value if requires_approval else PolicyStatus.ELIGIBLE.value)
        )

        return PolicyEvaluation(
            policy_name="Refund Policy Validation",
            status=status,
            is_eligible=is_eligible,
            requires_human_approval=requires_approval,
            reasons=reasons,
            violations=violations,
        )

    @classmethod
    def validate_cancellation(
        cls,
        order: OrderState,
        customer: CustomerState,
    ) -> PolicyEvaluation:
        reasons = []
        violations = []
        requires_approval = False
        is_eligible = True

        # Check order status
        current_status = order.status.upper()
        delivery_status = order.delivery_status.upper()

        if current_status == "CANCELLED":
            is_eligible = False
            violations.append("Order is already cancelled.")

        # Shipped order cancellation restriction (Section 10)
        if current_status in RESTRICTED_CANCELLATION_STATUSES or delivery_status in RESTRICTED_CANCELLATION_STATUSES:
            is_eligible = False
            violations.append(
                f"Order status is '{order.status}' (delivery: '{order.delivery_status}'). "
                "Cancellation is restricted once dispatched; customer must initiate return process."
            )

        # Flagged account check
        if customer.is_flagged:
            requires_approval = True
            reasons.append("Customer account flagged: manual verification required prior to cancellation.")

        if is_eligible and not requires_approval:
            reasons.append(f"Order status '{order.status}' is eligible for standard cancellation.")

        status = (
            PolicyStatus.INELIGIBLE.value
            if not is_eligible
            else (PolicyStatus.REQUIRES_REVIEW.value if requires_approval else PolicyStatus.ELIGIBLE.value)
        )

        return PolicyEvaluation(
            policy_name="Cancellation Policy Validation",
            status=status,
            is_eligible=is_eligible,
            requires_human_approval=requires_approval,
            reasons=reasons,
            violations=violations,
        )

    @classmethod
    def validate_reorder(
        cls,
        order: OrderState,
        customer: CustomerState,
    ) -> PolicyEvaluation:
        reasons = []
        violations = []
        requires_approval = False
        is_eligible = True

        if customer.is_flagged:
            requires_approval = True
            reasons.append("Flagged customer: reorder requires manual verification.")
        else:
            reasons.append("Reorder request passed standard validation.")

        status = (
            PolicyStatus.INELIGIBLE.value
            if not is_eligible
            else (PolicyStatus.REQUIRES_REVIEW.value if requires_approval else PolicyStatus.ELIGIBLE.value)
        )

        return PolicyEvaluation(
            policy_name="Reorder Policy Validation",
            status=status,
            is_eligible=is_eligible,
            requires_human_approval=requires_approval,
            reasons=reasons,
            violations=violations,
        )
