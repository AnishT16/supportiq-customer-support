"""
Global Configuration & Business Policy Thresholds for SupportIQ AI Engine.
"""

from enum import Enum


class ActionType(str, Enum):
    REFUND = "refund"
    CANCEL_ORDER = "cancel_order"
    REORDER_ITEM = "reorder_item"
    EXPEDITE_SHIPPING = "expedite_shipping"
    PROACTIVE_NOTIFICATION = "proactive_notification"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PolicyStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    REQUIRES_REVIEW = "requires_review"


class Recommendation(str, Enum):
    EXECUTE = "execute"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    BLOCKED = "blocked"


class ImpactType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


# Policy Thresholds based on README Section 10
AUTO_REFUND_LIMIT = 1000.0            # Refunds <= $1,000 are eligible for auto-execution
MANAGER_APPROVAL_LIMIT = 5000.0      # $1,001 - $5,000 requires manager review
HIGH_VALUE_THRESHOLD = 5000.0        # > $5,000 requires human executive approval

# Customer Risk Thresholds
MAX_ALLOWED_PREVIOUS_COMPLAINTS = 3  # Triggers elevated risk
MAX_ALLOWED_PREVIOUS_REFUNDS = 2     # Multiple refund history triggers manual verification

# Restricted Statuses for direct cancellation
RESTRICTED_CANCELLATION_STATUSES = {"SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"}
