"""
LLM Provider Integration for SupportIQ AI Support Agent.
Manages grounded prompt synthesis and multi-provider LLM calling (Groq / OpenAI).
Strictly adheres to:
- No hardcoded API keys.
- Clear error/unavailable status when credentials are not configured.
- Grounded prompt injection from RAG and simulation sandbox.
- Backend policy non-override protection.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_TEMPLATE = """You are the SupportIQ AI Customer Support Assistant.
You assist customers with order tracking, returns, refunds, cancellations, warranties, and store policies.

MANDATORY RULES:
1. Grounded Accuracy: Base your response EXCLUSIVELY on the provided Company Policy Passages and Simulation State.
2. No Overrides: You CANNOT override company policy or auto-approve actions that require human review or are blocked.
3. Simulation Awareness: Never claim an action has been permanently charged, refunded, or deleted. All state operations are simulated and subject to policy limits.
4. Human Approval: If the simulation state indicates that human approval is required, explicitly inform the customer that their request has been routed to a support manager for review.
5. Tone: Polite, professional, clear, and reassuring.

=== CONTEXT: COMPANY POLICY PASSAGES (RAG) ===
{rag_context}

=== CONTEXT: SIMULATION OUTCOME ===
{simulation_context}

=== CONTEXT: CUSTOMER & ORDER DATA ===
{order_context}
"""


class LLMProvider:
    """
    Interface for LLM generation.
    Supports Groq, OpenAI, or local simulated mode.
    Reads credentials strictly from environment variables or explicit parameter.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # Determine provider and key without hardcoding
        self.api_key = (
            api_key
            or os.environ.get("GROQ_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("SUPPORTIQ_LLM_API_KEY")
        )

        if provider:
            self.provider = provider.lower()
        elif os.environ.get("GROQ_API_KEY"):
            self.provider = "groq"
        elif os.environ.get("OPENAI_API_KEY"):
            self.provider = "openai"
        else:
            self.provider = "none"

        # Models
        if model:
            self.model = model
        elif self.provider == "groq":
            self.model = "llama-3.3-70b-versatile"
        elif self.provider == "openai":
            self.model = "gpt-4o-mini"
        else:
            self.model = "none"

    def is_available(self) -> bool:
        """Returns True if LLM credentials and provider are active."""
        return bool(self.api_key and self.provider != "none")

    def generate_grounded_response(
        self,
        user_message: str,
        rag_passages: List[Dict[str, Any]],
        simulation_result: Optional[Dict[str, Any]] = None,
        order_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], str, Optional[str]]:
        """
        Generates a grounded response using the configured LLM provider.

        Args:
            user_message: Customer message.
            rag_passages: List of retrieved policy passages from RAG.
            simulation_result: Optional simulated action result.
            order_context: Customer/order operational state.

        Returns:
            Tuple of (response_text, llm_status, error_message)
            llm_status: 'available', 'unavailable', or 'error'
        """
        # Requirement 5: Return clear unavailable status when credentials are not configured
        if not self.is_available():
            return (
                None,
                "unavailable",
                "LLM provider is not configured. Set GROQ_API_KEY or OPENAI_API_KEY to enable LLM generation.",
            )

        prompt = self._build_prompt(
            user_message=user_message,
            rag_passages=rag_passages,
            simulation_result=simulation_result,
            order_context=order_context,
        )

        try:
            if self.provider == "groq":
                response_text = self._call_groq(prompt, user_message)
                return response_text, "available", None
            elif self.provider == "openai":
                response_text = self._call_openai(prompt, user_message)
                return response_text, "available", None
            else:
                return (
                    None,
                    "unavailable",
                    f"Unsupported LLM provider: {self.provider}",
                )
        except Exception as e:
            logger.error(f"LLM API execution error: {e}", exc_info=True)
            return (
                None,
                "error",
                f"LLM provider execution failed: {str(e)}",
            )

    def _build_prompt(
        self,
        user_message: str,
        rag_passages: List[Dict[str, Any]],
        simulation_result: Optional[Dict[str, Any]],
        order_context: Optional[Dict[str, Any]],
    ) -> str:
        """Constructs grounded system prompt with injected context."""
        # Format RAG passages
        if rag_passages:
            rag_lines = []
            for i, p in enumerate(rag_passages, 1):
                title = p.get("document_title", "Policy Document")
                sec = p.get("section", "General")
                text = p.get("text", "")
                rag_lines.append(f"Passage {i} [{title} - {sec}]:\n{text}")
            rag_str = "\n\n".join(rag_lines)
        else:
            rag_str = "No specific policy passages found for this query."

        # Format Simulation context
        if simulation_result:
            sim_lines = [
                f"Simulated Action: {simulation_result.get('action')}",
                f"Policy Status: {simulation_result.get('policy_status')}",
                f"Risk Level: {simulation_result.get('risk_level')}",
                f"Financial Impact: ${abs(simulation_result.get('financial_impact', 0.0)):.2f}",
                f"Human Approval Required: {simulation_result.get('human_approval_required')}",
                f"Recommendation: {simulation_result.get('recommendation')}",
            ]
            if simulation_result.get("reasons"):
                sim_lines.append(f"Reasons: {', '.join(simulation_result['reasons'])}")
            if simulation_result.get("policy_violations"):
                sim_lines.append(
                    f"Policy Violations: {', '.join(simulation_result['policy_violations'])}"
                )
            sim_str = "\n".join(sim_lines)
        else:
            sim_str = "No action simulated for this query."

        # Format Order context
        if order_context:
            ord_str = (
                f"Order ID: #{order_context.get('order_id', 'N/A')}, "
                f"Status: {order_context.get('status', 'N/A')}, "
                f"Total Amount: ${order_context.get('total_amount', 0.0):.2f}, "
                f"Delivery: {order_context.get('delivery_status', 'N/A')}"
            )
        else:
            ord_str = "No order context available."

        return SYSTEM_PROMPT_TEMPLATE.format(
            rag_context=rag_str,
            simulation_context=sim_str,
            order_context=ord_str,
        )

    def _call_groq(self, system_prompt: str, user_message: str) -> str:
        """Calls Groq API using groq client."""
        from groq import Groq

        client = Groq(api_key=self.api_key)
        completion = client.chat.completions.create(
            model=self.model or "llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return completion.choices[0].message.content.strip()

    def _call_openai(self, system_prompt: str, user_message: str) -> str:
        """Calls OpenAI API using standard client."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.model or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            return completion.choices[0].message.content.strip()
        except ImportError:
            raise RuntimeError("openai package is not installed.")

    @staticmethod
    def build_deterministic_grounded_response(
        intent: str,
        user_message: str,
        rag_passages: List[Dict[str, Any]],
        simulation_result: Optional[Dict[str, Any]] = None,
        requires_human_approval: bool = False,
        human_approval_reason: Optional[str] = None,
    ) -> str:
        """
        Constructs a high-accuracy, policy-grounded deterministic response when the
        LLM provider is unconfigured or in offline mode.
        Ensures strict compliance with business rules and transparent communication.
        """
        parts: List[str] = []

        # 1. State simulation outcome if an action was simulated
        if simulation_result:
            action = simulation_result.get("action", "").replace("_", " ")
            order_id = simulation_result.get("order_id", "your order")
            policy_status = simulation_result.get("policy_status")
            risk_level = simulation_result.get("risk_level")
            financial_impact = abs(simulation_result.get("financial_impact", 0.0))

            if policy_status == "ineligible" or simulation_result.get("recommendation") == "blocked":
                violations = simulation_result.get("policy_violations", [])
                reasons_str = "; ".join(violations) if violations else "Action violates policy."
                parts.append(
                    f"Your requested {action} for Order #{order_id} cannot be completed directly: {reasons_str}."
                )
            elif requires_human_approval:
                reason = human_approval_reason or "transaction amount exceeds automated threshold"
                parts.append(
                    f"A {action} of ${financial_impact:.2f} for Order #{order_id} has been simulated. "
                    f"Because this is classified as {risk_level} risk ({reason}), "
                    "it requires review and approval by a support manager before execution."
                )
            else:
                parts.append(
                    f"Order #{order_id} is eligible for immediate {action} "
                    f"(Impact: -${financial_impact:.2f}). All policy checks passed."
                )

        # 2. Add grounded policy context if available
        if rag_passages:
            primary_passage = rag_passages[0]
            title = primary_passage.get("document_title", "Company Policy")
            text_snippet = primary_passage.get("text", "").strip()
            # Truncate clean passage to first sentence or 200 chars
            clean_snippet = text_snippet.split(". ")[0] + "." if ". " in text_snippet else text_snippet[:180]
            parts.append(f"According to our {title}: \"{clean_snippet}\"")
        elif not simulation_result:
            parts.append(
                "I couldn't locate a specific policy matching your exact request in our knowledge base."
            )

        # 3. Closing guidance
        if requires_human_approval:
            parts.append("A support representative will inspect your request within 24 hours.")
        else:
            parts.append("Please let me know if you would like me to submit this or connect with an agent.")

        return " ".join(parts)
