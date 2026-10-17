"""
Data Schemas for Predictive Support Intervention Engine.
Directly fulfills the specification in README.md Section 7 & Section 15.
"""

from typing import Any, Dict, List, Union
from pydantic import BaseModel, Field

from ai_engine.config import RiskLevel


class PredictionInput(BaseModel):
    customer_id: Union[int, str]
    delivery_delay: float = Field(default=0.0, ge=0.0, description="Delivery delay in days (>= 0)")
    previous_complaints: int = Field(default=0, ge=0, description="Count of historical complaints")
    courier_reliability: float = Field(default=0.95, ge=0.0, le=1.0, description="Reliability score between 0.0 and 1.0")
    warehouse_backlog: str = Field(default="Low", description="Backlog status: Low, Medium, High")
    order_value: float = Field(default=100.0, ge=0.0, description="Order total in USD")
    payment_status: str = Field(default="PAID", description="Payment status: PAID, PENDING, FAILED")
    product_category: str = Field(default="General", description="Product category")
    cancellation_history: int = Field(default=0, ge=0, description="Count of past cancelled orders")


class PredictionResult(BaseModel):
    """
    Prediction Response Schema.
    Strictly conforms to Section 15 of README.md.
    """
    customer_id: Union[int, str]
    support_probability: float = Field(..., description="Probability of contacting support within the prediction window (0.0 to 1.0)")
    prediction_window: str = Field(default="next_48_hours", description="Time window for forecasted intervention")
    predicted_issue: str = Field(..., description="Most likely support issue category")
    risk_level: str = RiskLevel.LOW.value
    reasons: List[str] = Field(default_factory=list, description="Top contributing factors")
    recommended_intervention: str = "monitor_only"
    issue_probabilities: Dict[str, float] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary for Django DRF responses."""
        return self.model_dump()
