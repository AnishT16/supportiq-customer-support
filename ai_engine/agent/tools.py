"""
Controlled Tool Registry for SupportIQ AI Support Agent.
Enforces strict boundaries on agent capabilities:
- Approved read-only and simulation tools only.
- Real refunds, cancellations, or financial transactions are strictly blocked.
- High-risk and policy-sensitive actions mandate human approval.
Strictly compatible with Section 6.2 & Section 15 of README.md.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Union
import logging

from ai_engine.config import ActionType, Recommendation, RiskLevel
from ai_engine.predictor.inference import PredictionEngine
from ai_engine.rag.tool import search_knowledge_base
from ai_engine.simulation.engine import SimulationEngine
from ai_engine.simulation.schemas import SimulationResult

logger = logging.getLogger(__name__)


# Explicit blacklist of prohibited real-world state mutating operations
PROHIBITED_MUTATION_OPERATIONS: Set[str] = {
    "execute_refund",
    "execute_real_refund",
    "process_refund",
    "execute_cancellation",
    "cancel_order_in_db",
    "process_payment",
    "charge_credit_card",
    "delete_user",
    "delete_order",
    "drop_tables",
    "execute_sql",
}


class ControlledToolRegistry:
    """
    Registry of safe, verified operations exposed to the AI Support Agent.
    Guarantees that all state mutations remain safely sandboxed in simulation.
    """

    def __init__(self, knowledge_base: Optional[Any] = None):
        self.kb = knowledge_base
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register_tool(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        parameters: Dict[str, Any],
        requires_authorization: bool = False,
    ) -> None:
        """Register an approved tool function."""
        if name in PROHIBITED_MUTATION_OPERATIONS:
            raise ValueError(
                f"Security Violation: '{name}' is a prohibited mutation operation and cannot be registered."
            )
        self._tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "parameters": parameters,
            "requires_authorization": requires_authorization,
        }

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return OpenAI / LLM function calling schemas for all registered tools."""
        schemas = []
        for name, tool in self._tools.items():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
            )
        return schemas

    def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        user_role: str = "customer",
    ) -> Dict[str, Any]:
        """
        Safely execute a registered tool with authorization and safety guardrails.

        Args:
            name: Tool name.
            arguments: Dictionary of keyword arguments.
            user_role: Caller role ('customer', 'agent', 'manager', 'admin').

        Returns:
            Dictionary with execution status, result payload, and human approval flags.
        """
        # 1. Prohibited operations check (Requirement 8)
        if name in PROHIBITED_MUTATION_OPERATIONS or "execute_" in name or "delete_" in name:
            logger.warning(f"Blocked attempt to execute real mutation operation: {name}")
            return {
                "status": "unauthorized",
                "error": (
                    f"Prohibited Operation: '{name}' would perform real state mutation. "
                    "SupportIQ strictly restricts AI agents to 'simulate_action'. "
                    "Real execution requires authorized human workflows."
                ),
                "human_approval_required": True,
            }

        # 2. Existence check
        if name not in self._tools:
            return {
                "status": "error",
                "error": f"Tool '{name}' is not registered in the controlled tool registry.",
            }

        tool_meta = self._tools[name]

        # 3. Authorization check (Requirement 9)
        if tool_meta["requires_authorization"] and user_role not in ["agent", "manager", "admin"]:
            return {
                "status": "unauthorized",
                "error": f"Tool '{name}' requires staff authorization (role: {user_role}).",
                "human_approval_required": True,
            }

        # 4. Controlled Execution
        try:
            result = tool_meta["func"](**arguments)

            # Check if simulation result demands human approval
            requires_human_approval = False
            approval_reason = None

            if isinstance(result, SimulationResult):
                requires_human_approval = result.human_approval_required
                if result.recommendation == Recommendation.HUMAN_APPROVAL_REQUIRED.value:
                    requires_human_approval = True
                    approval_reason = f"Simulation requires human approval: {'; '.join(result.reasons)}"
                elif result.recommendation == Recommendation.BLOCKED.value:
                    approval_reason = f"Action blocked by policy: {'; '.join(result.policy_violations)}"
                result = result.to_dict()

            return {
                "status": "success",
                "result": result,
                "human_approval_required": requires_human_approval,
                "approval_reason": approval_reason,
            }

        except TypeError as te:
            logger.error(f"Invalid arguments for tool '{name}': {te}")
            return {"status": "error", "error": f"Invalid arguments for tool '{name}': {str(te)}"}
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    # --- Built-in Safe Tool Implementations ---

    def _register_default_tools(self) -> None:
        """Register the standard suite of controlled SupportIQ tools."""

        # 1. search_knowledge_base (RAG)
        self.register_tool(
            name="search_knowledge_base",
            func=self._tool_search_knowledge_base,
            description="Search company support policies, FAQs, return rules, and warranty terms via RAG.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Customer question or search term."},
                    "top_k": {"type": "integer", "default": 3, "description": "Number of passages."},
                    "min_score": {"type": "number", "default": 0.05, "description": "Similarity cutoff."},
                    "source_filter": {"type": "string", "description": "Optional policy file filter."},
                },
                "required": ["query"],
            },
            requires_authorization=False,
        )

        # 2. simulate_action (Action Simulation Engine)
        self.register_tool(
            name="simulate_action",
            func=self._tool_simulate_action,
            description=(
                "Simulate a proposed support action (refund, cancellation, expedited shipping) "
                "in a pre-execution sandbox without modifying real databases or charging accounts."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action name: 'refund', 'cancel_order', 'expedite_shipping', etc."},
                    "current_state": {"type": "object", "description": "Current order state dictionary."},
                    "customer_state": {"type": "object", "description": "Customer state dictionary."},
                    "payload": {"type": "object", "description": "Extra parameters such as amount, reason."},
                },
                "required": ["action", "current_state"],
            },
            requires_authorization=False,
        )

        # 3. predict_support_risk (Predictive Intervention ML)
        self.register_tool(
            name="predict_support_risk",
            func=self._tool_predict_support_risk,
            description="Predict customer support contact probability, likely issue category, and churn risk.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Operational event features dictionary."},
                },
                "required": ["data"],
            },
            requires_authorization=False,
        )

        # 4. escalate_to_human
        self.register_tool(
            name="escalate_to_human",
            func=self._tool_escalate_to_human,
            description="Escalate a support ticket or customer issue to human agent review.",
            parameters={
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for escalation."},
                    "priority": {"type": "string", "default": "medium", "description": "low, medium, high."},
                },
                "required": ["reason"],
            },
            requires_authorization=False,
        )

    def _tool_search_knowledge_base(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.05,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if self.kb is not None:
            response = self.kb.search(
                query=query,
                top_k=top_k,
                min_score=min_score,
                source_filter=source_filter,
            )
            return [r.to_dict() for r in response.results]
        return search_knowledge_base(
            query=query,
            top_k=top_k,
            min_score=min_score,
            source_filter=source_filter,
        )

    def _tool_simulate_action(
        self,
        action: str,
        current_state: Dict[str, Any],
        customer_state: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> SimulationResult:
        """
        Executes pre-execution simulation using SimulationEngine.
        Guaranteed to NEVER mutate production databases.
        """
        return SimulationEngine.simulate(
            action=action,
            current_state=current_state,
            customer_state=customer_state,
            payload=payload,
        )

    def _tool_predict_support_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs predictive ML model for contact and churn risk."""
        clean_data = dict(data)
        if "customer_id" not in clean_data:
            clean_data["customer_id"] = 9281
        if isinstance(clean_data.get("courier_reliability"), str):
            mapping = {"low": 0.40, "medium": 0.75, "high": 0.95}
            clean_data["courier_reliability"] = mapping.get(
                clean_data["courier_reliability"].lower(), 0.70
            )
        if isinstance(clean_data.get("warehouse_backlog"), str):
            clean_data["warehouse_backlog"] = clean_data["warehouse_backlog"].capitalize()
        result = PredictionEngine.predict(clean_data)
        return result.to_dict()

    def _tool_escalate_to_human(self, reason: str, priority: str = "medium") -> Dict[str, Any]:
        """Creates an escalation record for a human agent."""
        return {
            "status": "escalated",
            "reason": reason,
            "priority": priority,
            "human_approval_required": True,
        }
