"""
Data Schemas and Contracts for the Action Simulation Engine.
Strictly compatible with Section 8 & Section 15 of README.md.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from ai_engine.config import (
    ActionType,
    ImpactType,
    PolicyStatus,
    Recommendation,
    RiskLevel,
)


class OrderItem(BaseModel):
    product_id: Union[int, str]
    name: str = "Product Item"
    quantity: int = 1
    unit_price: float = 0.0


class OrderState(BaseModel):
    order_id: Union[int, str]
    customer_id: Union[int, str]
    status: str = "ACTIVE"  # ACTIVE, PAID, PROCESSING, SHIPPED, DELIVERED, CANCELLED
    total_amount: float = 0.0
    items: List[OrderItem] = Field(default_factory=list)
    payment_status: str = "PAID"  # PAID, PENDING, REFUNDED, FAILED
    delivery_status: str = "NOT_SHIPPED"  # NOT_SHIPPED, IN_TRANSIT, DELIVERED, RETURNED
    coupon_code: Optional[str] = None
    is_coupon_applied: bool = False
    refunded_amount: float = 0.0


class CustomerState(BaseModel):
    customer_id: Union[int, str]
    name: str = ""
    previous_complaints: int = 0
    previous_refunds_count: int = 0
    is_flagged: bool = False
    account_status: str = "ACTIVE"  # ACTIVE, SUSPENDED, FLAGGED


class ProposedAction(BaseModel):
    action_type: str = ActionType.REFUND.value
    order_id: Union[int, str]
    amount: Optional[float] = None
    reason: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluation(BaseModel):
    policy_name: str
    status: str = PolicyStatus.ELIGIBLE.value
    is_eligible: bool = True
    requires_human_approval: bool = False
    reasons: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """
    Simulation Result Schema.
    Directly fulfills the specification in README.md Section 15.
    """
    action: str
    order_id: Union[int, str]
    amount: float = 0.0
    policy_status: str = PolicyStatus.ELIGIBLE.value
    risk_level: str = RiskLevel.LOW.value
    customer_impact: str = ImpactType.POSITIVE.value
    financial_impact: float = 0.0
    inventory_impact: int = 0
    coupon_impact: Optional[str] = None
    human_approval_required: bool = False
    recommendation: str = Recommendation.EXECUTE.value
    reasons: List[str] = Field(default_factory=list)
    policy_violations: List[str] = Field(default_factory=list)
    simulated_state: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary for Django DRF responses."""
        return self.model_dump()
