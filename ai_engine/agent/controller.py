"""
SupportIQ AI Support Agent Controller & Orchestrator.
Main entry point for customer support message handling, intent classification,
RAG context retrieval, pre-execution action simulation, and grounded LLM synthesis.

Strictly adheres to:
- Section 6.1 & 6.2 of README.md
- Controlled tool invocation with safety bounds
- Zero direct database / payment mutations
- Backend policy non-override protection
- Clear error / unavailable status when LLM credentials are not configured
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import logging

from ai_engine.agent.intent import IntentClassifier
from ai_engine.agent.llm import LLMProvider
from ai_engine.agent.schemas import (
    AgentRequest,
    AgentResponse,
    IntentType,
    ToolInvocation,
)
from ai_engine.agent.tools import ControlledToolRegistry
from ai_engine.config import ActionType, Recommendation, RiskLevel
from ai_engine.rag.engine import KnowledgeBase, get_default_knowledge_base

logger = logging.getLogger(__name__)


# Intent to RAG search query mapping
INTENT_RAG_QUERIES: Dict[IntentType, str] = {
    IntentType.ORDER_CANCELLATION: "cancellation policy cutoff window active shipped",
    IntentType.REFUND_REQUEST: "refund policy return window tiers auto refund limit",
    IntentType.DELIVERY_TRACKING: "shipping policy delivery delay 3 days lost package courier",
    IntentType.EXPEDITE_SHIPPING: "expedited shipping tiers overnight delivery options",
    IntentType.WARRANTY_INQUIRY: "warranty policy limited coverage replacement claim RMA",
    IntentType.PAYMENT_INQUIRY: "payment methods failed payment billing duplicate charges",
    IntentType.POLICY_INQUIRY: "support policies return refund shipping terms",
}

# Intent to Simulation Action mapping
INTENT_SIMULATION_ACTIONS: Dict[IntentType, str] = {
    IntentType.ORDER_CANCELLATION: ActionType.CANCEL_ORDER.value,
    IntentType.REFUND_REQUEST: ActionType.REFUND.value,
    IntentType.EXPEDITE_SHIPPING: ActionType.EXPEDITE_SHIPPING.value,
}


INTENT_SOURCE_FILTERS: Dict[IntentType, str] = {
    IntentType.ORDER_CANCELLATION: "cancellation_policy.md",
    IntentType.REFUND_REQUEST: "refund_policy.md",
    IntentType.DELIVERY_TRACKING: "shipping_policy.md",
    IntentType.EXPEDITE_SHIPPING: "shipping_policy.md",
    IntentType.WARRANTY_INQUIRY: "warranty_policy.md",
    IntentType.PAYMENT_INQUIRY: "payment_faq.md",
}


class SupportIQAgent:
    """
    Production-grade AI Support Agent Controller.

    Django Developer Interface:
        ```python
        from ai_engine.agent import SupportIQAgent

        agent = SupportIQAgent()
        result = agent.process_message({
            "message": "Can I cancel order #1001?",
            "order_id": 1001,
            "customer_id": 9281,
        })
        return JsonResponse(result.to_dict())
        ```
    """

    def __init__(
        self,
        tool_registry: Optional[ControlledToolRegistry] = None,
        llm_provider: Optional[LLMProvider] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
    ):
        self.kb = knowledge_base or get_default_knowledge_base()
        self.tools = tool_registry or ControlledToolRegistry(knowledge_base=self.kb)
        self.llm = llm_provider or LLMProvider()

    def process_message(
        self,
        request: Union[str, Dict[str, Any], AgentRequest],
    ) -> AgentResponse:
        """
        Process an incoming customer message through the full agent pipeline.

        Pipeline Stages:
        1. Input validation & normalization to AgentRequest
        2. Intent recognition & entity extraction (e.g. order ID, amount, defect)
        3. Ambiguity handling (clarification prompt if request is ambiguous)
        4. RAG policy passage retrieval
        5. Action simulation (if user requests an actionable state change)
        6. Predictive risk evaluation (if operational data present)
        7. Grounded LLM response generation (with strict unconfigured fallback)
        8. Backend policy non-override enforcement
        9. Audit logging and response assembly

        Args:
            request: Raw text string, request dictionary, or AgentRequest instance.

        Returns:
            AgentResponse instance with full metadata, tools called, and suggested actions.
        """
        audit_trail: List[Dict[str, Any]] = []
        tools_called: List[ToolInvocation] = []

        # ---------------------------------------------------------------------
        # 1. Normalize Request
        # ---------------------------------------------------------------------
        req: AgentRequest
        if isinstance(request, str):
            req = AgentRequest(message=request)
        elif isinstance(request, dict):
            req = AgentRequest.model_validate(request)
        elif isinstance(request, AgentRequest):
            req = request
        else:
            req = AgentRequest(message=str(request))

        # ---------------------------------------------------------------------
        # 2. Intent Classification & Entity Extraction
        # ---------------------------------------------------------------------
        intent_type, confidence = IntentClassifier.classify(req.message)
        extracted_entities = IntentClassifier.extract_entities(req.message)

        # Merge extracted entities with request fields
        if "order_id" in extracted_entities and not req.order_id:
            req.order_id = extracted_entities["order_id"]

        # ---------------------------------------------------------------------
        # 3. Handle Ambiguous Requests (Requirement 10)
        # ---------------------------------------------------------------------
        if intent_type == IntentType.AMBIGUOUS:
            return AgentResponse(
                response=(
                    "Hello! I am your SupportIQ AI Assistant. I can help you check order delivery "
                    "status, explore return and refund policies, cancel pending orders, or request a warranty claim. "
                    "Could you please share your order number or describe the issue you are experiencing?"
                ),
                intent=IntentType.AMBIGUOUS.value,
                intent_confidence=confidence,
                entities=extracted_entities,
                tools_called=[],
                rag_passages=[],
                suggested_actions=[
                    "Track an Order",
                    "Request a Refund",
                    "Cancel an Order",
                    "Check Warranty Policy",
                    "Speak with a Human Agent",
                ],
                llm_status="unavailable" if not self.llm.is_available() else "available",
                requires_human_approval=False,
                audit_trail=[
                    {
                        "stage": "intent_classification",
                        "status": "ambiguous_request_handled",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            )

        # ---------------------------------------------------------------------
        # 4. RAG Policy Passage Retrieval (Requirement 3 & 10)
        # ---------------------------------------------------------------------
        rag_passages: List[Dict[str, Any]] = []
        search_query = req.message
        if intent_type in INTENT_RAG_QUERIES:
            search_query = f"{req.message} {INTENT_RAG_QUERIES[intent_type]}"

        source_filter = INTENT_SOURCE_FILTERS.get(intent_type)
        tool_exec = self.tools.execute_tool(
            name="search_knowledge_base",
            arguments={"query": search_query, "top_k": 3, "min_score": 0.04, "source_filter": source_filter},
            user_role=req.user_role or "customer",
        )
        if not (tool_exec.get("status") == "success" and tool_exec.get("result")):
            tool_exec = self.tools.execute_tool(
                name="search_knowledge_base",
                arguments={"query": search_query, "top_k": 3, "min_score": 0.04},
                user_role=req.user_role or "customer",
            )

        tools_called.append(
            ToolInvocation(
                name="search_knowledge_base",
                arguments={"query": search_query},
                result=tool_exec.get("result"),
                status=tool_exec.get("status", "success"),
            )
        )
        audit_trail.append(
            {
                "tool": "search_knowledge_base",
                "status": tool_exec.get("status"),
                "results_count": len(tool_exec.get("result") or []),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        if tool_exec.get("status") == "success" and tool_exec.get("result"):
            rag_passages = tool_exec["result"]

        # ---------------------------------------------------------------------
        # 5. Action Simulation Sandbox (Requirements 6, 7, 8, 9)
        # ---------------------------------------------------------------------
        simulation_result: Optional[Dict[str, Any]] = None
        requires_human_approval = False
        human_approval_reason = None

        if intent_type in INTENT_SIMULATION_ACTIONS:
            action_name = INTENT_SIMULATION_ACTIONS[intent_type]
            order_context = req.get_order_context()
            customer_context = req.get_customer_context()

            # Pass extracted dollar amount or custom payload
            payload: Dict[str, Any] = {}
            if "amount" in extracted_entities:
                payload["amount"] = extracted_entities["amount"]
            elif order_context.get("total_amount"):
                payload["amount"] = order_context["total_amount"]
            if "reasons" in extracted_entities:
                payload["reason"] = ", ".join(extracted_entities["reasons"])

            sim_exec = self.tools.execute_tool(
                name="simulate_action",
                arguments={
                    "action": action_name,
                    "current_state": order_context,
                    "customer_state": customer_context,
                    "payload": payload,
                },
                user_role=req.user_role or "customer",
            )

            tools_called.append(
                ToolInvocation(
                    name="simulate_action",
                    arguments={"action": action_name, "order_id": order_context.get("order_id")},
                    result=sim_exec.get("result"),
                    status=sim_exec.get("status", "simulated"),
                )
            )
            audit_trail.append(
                {
                    "tool": "simulate_action",
                    "action": action_name,
                    "status": sim_exec.get("status"),
                    "requires_approval": sim_exec.get("human_approval_required", False),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            if sim_exec.get("status") == "success":
                simulation_result = sim_exec.get("result")
                requires_human_approval = sim_exec.get("human_approval_required", False)
                human_approval_reason = sim_exec.get("approval_reason")

        # ---------------------------------------------------------------------
        # 6. Predictive ML Support Intervention (if operational data provided)
        # ---------------------------------------------------------------------
        prediction_result: Optional[Dict[str, Any]] = None
        if req.operational_data:
            pred_exec = self.tools.execute_tool(
                name="predict_support_risk",
                arguments={"data": req.operational_data},
                user_role=req.user_role or "customer",
            )
            tools_called.append(
                ToolInvocation(
                    name="predict_support_risk",
                    arguments={"data": req.operational_data},
                    result=pred_exec.get("result"),
                    status=pred_exec.get("status", "success"),
                )
            )
            if pred_exec.get("status") == "success":
                prediction_result = pred_exec.get("result")

        # ---------------------------------------------------------------------
        # 7. Grounded LLM Synthesis / Fallback (Requirements 4 & 5)
        # ---------------------------------------------------------------------
        llm_text, llm_status, llm_error = self.llm.generate_grounded_response(
            user_message=req.message,
            rag_passages=rag_passages,
            simulation_result=simulation_result,
            order_context=req.get_order_context(),
        )

        final_response_text: str
        if llm_status == "available" and llm_text:
            final_response_text = llm_text
        else:
            # Deterministic, grounded fallback
            final_response_text = LLMProvider.build_deterministic_grounded_response(
                intent=intent_type.value,
                user_message=req.message,
                rag_passages=rag_passages,
                simulation_result=simulation_result,
                requires_human_approval=requires_human_approval,
                human_approval_reason=human_approval_reason,
            )

        # ---------------------------------------------------------------------
        # 8. Backend Policy Non-Override Protection (Requirement 9 & Constraint)
        # ---------------------------------------------------------------------
        # Ensure LLM does NOT override backend policy rules or approval gates
        if simulation_result:
            is_blocked = (
                simulation_result.get("recommendation") == Recommendation.BLOCKED.value
                or simulation_result.get("policy_status") == "ineligible"
            )
            if is_blocked:
                requires_human_approval = False
                policy_note = (
                    f" [System Policy Note: Action '{simulation_result.get('action')}' is ineligible "
                    f"under company policy: {'; '.join(simulation_result.get('policy_violations', []))}]"
                )
                if policy_note not in final_response_text:
                    final_response_text += policy_note
            elif requires_human_approval:
                # If LLM failed to mention manager review, append safety gate
                approval_notice = (
                    " [Notice: Due to policy thresholds, this action requires approval "
                    "from a support manager before execution.]"
                )
                if "approval" not in final_response_text.lower() and "manager" not in final_response_text.lower():
                    final_response_text += approval_notice

        # ---------------------------------------------------------------------
        # 9. Determine Suggested Actions
        # ---------------------------------------------------------------------
        suggested_actions = self._build_suggested_actions(
            intent=intent_type,
            simulation=simulation_result,
            requires_human_approval=requires_human_approval,
        )

        return AgentResponse(
            response=final_response_text,
            intent=intent_type.value,
            intent_confidence=confidence,
            entities=extracted_entities,
            tools_called=tools_called,
            rag_passages=rag_passages,
            simulation=simulation_result,
            prediction=prediction_result,
            suggested_actions=suggested_actions,
            llm_status=llm_status,
            error=llm_error,
            requires_human_approval=requires_human_approval,
            human_approval_reason=human_approval_reason,
            audit_trail=audit_trail,
        )

    def _build_suggested_actions(
        self,
        intent: IntentType,
        simulation: Optional[Dict[str, Any]],
        requires_human_approval: bool,
    ) -> List[str]:
        """Provides relevant one-click contextual action suggestions for the UI."""
        if requires_human_approval:
            return ["Request Manager Review", "Talk to Support Agent", "View Ticket Status"]

        if simulation and simulation.get("recommendation") == Recommendation.BLOCKED.value:
            return ["Review Return Policy", "Contact Support Agent", "File Policy Appeal"]

        if intent == IntentType.ORDER_CANCELLATION:
            return ["Confirm Cancellation", "Modify Order Items", "Keep Order"]
        elif intent == IntentType.REFUND_REQUEST:
            return ["Submit Refund Request", "Exchange Item Instead", "Talk to Human Agent"]
        elif intent == IntentType.DELIVERY_TRACKING:
            return ["View Live Tracking", "Report Delayed Delivery", "Notify Carrier"]
        elif intent == IntentType.WARRANTY_INQUIRY:
            return ["File RMA Warranty Claim", "View Care+ Benefits", "Locate Repair Center"]
        else:
            return ["Track an Order", "Return/Refund Item", "Check Policies", "Talk to Support Agent"]
