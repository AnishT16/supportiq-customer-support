"""
Data Schemas and Contracts for SupportIQ AI Support Agent.
Defines input requests, tool invocations, intent classifications, and response models.
Strictly compatible with Section 6.1, 6.2 & Section 15 of README.md.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Customer query intent classifications."""
    REFUND_REQUEST = "REFUND_REQUEST"
    ORDER_CANCELLATION = "ORDER_CANCELLATION"
    DELIVERY_TRACKING = "DELIVERY_TRACKING"
    EXPEDITE_SHIPPING = "EXPEDITE_SHIPPING"
    WARRANTY_INQUIRY = "WARRANTY_INQUIRY"
    PAYMENT_INQUIRY = "PAYMENT_INQUIRY"
    POLICY_INQUIRY = "POLICY_INQUIRY"
    GENERAL_SUPPORT = "GENERAL_SUPPORT"
    AMBIGUOUS = "AMBIGUOUS"


class ToolInvocation(BaseModel):
    """Record of an individual tool call executed by or on behalf of the agent."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    status: str = "success"  # success, simulated, error, unauthorized

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class AgentRequest(BaseModel):
    """
    Standard request payload accepted by SupportIQAgent.
    Can be instantiated from a raw string or Django DRF request.data dictionary.
    """
    message: str
    customer_id: Optional[Union[int, str]] = None
    order_id: Optional[Union[int, str]] = None
    customer_state: Optional[Dict[str, Any]] = None
    order_state: Optional[Dict[str, Any]] = None
    operational_data: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    user_role: Optional[str] = "customer"
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

    def get_order_context(self) -> Dict[str, Any]:
        """
        Returns full order state if provided, or synthetic minimal order state
        based on order_id.
        """
        if self.order_state:
            return self.order_state
        return {
            "order_id": self.order_id or 1001,
            "customer_id": self.customer_id or 9001,
            "status": "ACTIVE",
            "total_amount": 100.0,
            "payment_status": "PAID",
            "delivery_status": "NOT_SHIPPED",
            "refunded_amount": 0.0,
        }

    def get_customer_context(self) -> Dict[str, Any]:
        """
        Returns customer state if provided, or synthetic default.
        """
        if self.customer_state:
            return self.customer_state
        return {
            "customer_id": self.customer_id or 9001,
            "previous_complaints": 0,
            "previous_refunds_count": 0,
            "is_flagged": False,
            "account_status": "ACTIVE",
        }


class AgentResponse(BaseModel):
    """
    Standard structured response output returned by SupportIQAgent.
    Designed for direct serialization into Django DRF JsonResponse.
    """
    response: str
    intent: str = IntentType.GENERAL_SUPPORT.value
    intent_confidence: float = 0.0
    entities: Dict[str, Any] = Field(default_factory=dict)
    tools_called: List[ToolInvocation] = Field(default_factory=list)
    rag_passages: List[Dict[str, Any]] = Field(default_factory=list)
    simulation: Optional[Dict[str, Any]] = None
    prediction: Optional[Dict[str, Any]] = None
    suggested_actions: List[str] = Field(default_factory=list)
    llm_status: str = "unavailable"  # available, unavailable, simulated, error
    error: Optional[str] = None
    requires_human_approval: bool = False
    human_approval_reason: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to JSON-serializable dictionary."""
        return self.model_dump()
