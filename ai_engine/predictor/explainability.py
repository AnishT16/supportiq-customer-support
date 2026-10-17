"""
Explainability Engine for Predictive Support Intervention.
Maps feature inputs and model weights into human-understandable reason codes.
Matches README Section 7.2 and Section 15 specifications.
"""

from typing import Dict, List, Union


class ExplainabilityEngine:
    """
    Analyzes input signals and ranks the most influential factors
    driving the predicted support contact risk.
    """

    @classmethod
    def get_top_reasons(
        cls,
        features: Dict[str, Union[int, float, str]],
        max_reasons: int = 3,
        include_prefix: bool = False,
    ) -> List[str]:
        """
        Extracts the top human-readable reason codes ordered by importance.
        """
        reasons_with_weight = []

        delay = float(features.get("delivery_delay", 0.0))
        if delay >= 1.0:
            delay_str = f"{int(delay)}" if delay.is_integer() else f"{delay:.1f}"
            weight = delay * 1.5
            text = f"{delay_str} day delivery delay"
            reasons_with_weight.append((weight, f"+{text}" if include_prefix else text))

        complaints = int(features.get("previous_complaints", 0))
        if complaints > 0:
            weight = complaints * 1.8
            text = f"{complaints} previous complaints" if complaints > 1 else "previous complaints"
            reasons_with_weight.append((weight, f"+{text}" if include_prefix else text))

        backlog = str(features.get("warehouse_backlog", "Low"))
        if backlog == "High":
            weight = 2.0
            text = "warehouse backlog"
            reasons_with_weight.append((weight, "+High warehouse backlog" if include_prefix else text))
        elif backlog == "Medium":
            weight = 0.8
            text = "warehouse backlog"
            reasons_with_weight.append((weight, "+Medium warehouse backlog" if include_prefix else text))

        courier = float(features.get("courier_reliability", 1.0))
        if courier < 0.80:
            weight = (1.0 - courier) * 3.0
            text = "low courier reliability"
            reasons_with_weight.append((weight, "+Low courier reliability" if include_prefix else text))

        payment_status = str(features.get("payment_status", "PAID")).upper()
        if payment_status == "FAILED":
            weight = 3.5
            text = "failed payment status"
            reasons_with_weight.append((weight, "+Failed payment status" if include_prefix else text))
        elif payment_status == "PENDING":
            weight = 1.5
            text = "pending payment status"
            reasons_with_weight.append((weight, "+Pending payment status" if include_prefix else text))

        order_val = float(features.get("order_value", 0.0))
        if order_val > 2000:
            weight = 0.9
            text = f"high-value order (${order_val:.0f})"
            reasons_with_weight.append((weight, f"+{text}" if include_prefix else text))

        cancels = int(features.get("cancellation_history", 0))
        if cancels > 1:
            weight = 0.7 * cancels
            text = "repeated order cancellations"
            reasons_with_weight.append((weight, f"+{text}" if include_prefix else text))

        # Sort descending by weight
        reasons_with_weight.sort(key=lambda x: x[0], reverse=True)

        selected = [item[1] for item in reasons_with_weight[:max_reasons]]
        if not selected:
            selected = ["routine account activity"]

        return selected
