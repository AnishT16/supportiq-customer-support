"""
Risk Evaluator for SupportIQ AI Action Simulation.
Computes multi-dimensional risk scores (LOW, MEDIUM, HIGH) and human approval requirements.
"""

from typing import List, Tuple

from ai_engine.config import (
    ActionType,
    AUTO_REFUND_LIMIT,
    HIGH_VALUE_THRESHOLD,
    MAX_ALLOWED_PREVIOUS_COMPLAINTS,
    MAX_ALLOWED_PREVIOUS_REFUNDS,
    RiskLevel,
)
from ai_engine.simulation.schemas import (
    CustomerState,
    OrderState,
    PolicyEvaluation,
)


class RiskEvaluator:
    """
    Evaluates financial, operational, and customer risk dimensions
    to generate an aggregate risk rating and approval flag.
    """

    @classmethod
    def evaluate(
        cls,
        action_type: str,
        order: OrderState,
        customer: CustomerState,
        policy: PolicyEvaluation,
        amount: float = 0.0,
    ) -> Tuple[str, bool, List[str]]:
        """
        Returns:
            Tuple of (risk_level: str, human_approval_required: bool, risk_factors: List[str])
        """
        risk_factors: List[str] = []
        human_approval_required = policy.requires_human_approval

        # If policy already failed, high operational risk
        if not policy.is_eligible:
            risk_factors.extend(policy.violations)
            return RiskLevel.HIGH.value, True, risk_factors

        # 1. Financial Risk Dimension
        if action_type == ActionType.REFUND.value:
            if amount > HIGH_VALUE_THRESHOLD:
                base_risk = RiskLevel.HIGH.value
                human_approval_required = True
                risk_factors.append(f"High-value financial exposure (${amount:.2f} > ${HIGH_VALUE_THRESHOLD:.2f})")
            elif amount > AUTO_REFUND_LIMIT:
                base_risk = RiskLevel.MEDIUM.value
                human_approval_required = True
                risk_factors.append(f"Medium-value refund (${amount:.2f} > ${AUTO_REFUND_LIMIT:.2f})")
            else:
                base_risk = RiskLevel.LOW.value
                risk_factors.append(f"Low financial exposure (${amount:.2f} <= ${AUTO_REFUND_LIMIT:.2f})")
        else:
            base_risk = RiskLevel.LOW.value

        # 2. Customer Risk Dimension
        if customer.is_flagged or customer.account_status == "FLAGGED":
            base_risk = RiskLevel.HIGH.value
            human_approval_required = True
            risk_factors.append("Customer account is flagged for elevated risk / fraud monitoring")

        if customer.previous_refunds_count >= MAX_ALLOWED_PREVIOUS_REFUNDS:
            if base_risk == RiskLevel.LOW.value:
                base_risk = RiskLevel.MEDIUM.value
            human_approval_required = True
            risk_factors.append(
                f"Elevated customer refund history ({customer.previous_refunds_count} prior refunds)"
            )

        if customer.previous_complaints > MAX_ALLOWED_PREVIOUS_COMPLAINTS:
            if base_risk == RiskLevel.LOW.value:
                base_risk = RiskLevel.MEDIUM.value
            risk_factors.append(
                f"High historical complaint frequency ({customer.previous_complaints} prior complaints)"
            )

        # 3. Policy overrides
        if policy.requires_human_approval:
            human_approval_required = True
            if base_risk == RiskLevel.LOW.value:
                base_risk = RiskLevel.MEDIUM.value
            risk_factors.extend(policy.reasons)

        return base_risk, human_approval_required, risk_factors
