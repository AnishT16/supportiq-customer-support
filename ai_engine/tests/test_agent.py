"""
Unit and Integration Tests for SupportIQ AI Support Agent.
Tests all requirements:
1. Intent classification & entity extraction
2. Successful RAG policy passage retrieval
3. Missing documents and empty query handling
4. Ambiguous customer requests
5. Unavailable LLM credentials & clear status reporting
6. Controlled tool registry & prohibition of real mutations
7. Pre-execution action simulation
8. Sensitive actions & mandatory human approval
9. Backend policy non-override enforcement
10. Predictive risk integration
"""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from ai_engine.agent.controller import SupportIQAgent
from ai_engine.agent.intent import IntentClassifier
from ai_engine.agent.llm import LLMProvider
from ai_engine.agent.schemas import AgentRequest, IntentType
from ai_engine.agent.tools import ControlledToolRegistry, PROHIBITED_MUTATION_OPERATIONS
from ai_engine.config import PolicyStatus, Recommendation, RiskLevel
from ai_engine.rag.engine import KnowledgeBase


# =============================================================================
# 1. Intent Recognition & Ambiguity Tests (Requirements 1, 2, 10)
# =============================================================================

def test_intent_classification_and_entity_extraction():
    """Verify intent detection and entity extraction on specific customer messages."""
    # Cancellation
    intent, conf = IntentClassifier.classify("Can I cancel my order #1001?")
    assert intent == IntentType.ORDER_CANCELLATION
    assert conf >= 0.90
    entities = IntentClassifier.extract_entities("Can I cancel my order #1001?")
    assert entities.get("order_id") == 1001

    # Refund
    intent, conf = IntentClassifier.classify("I want a refund of $2499 for defective item")
    assert intent == IntentType.REFUND_REQUEST
    entities = IntentClassifier.extract_entities("I want a refund of $2499 for defective item")
    assert entities.get("amount") == 2499.0
    assert "defective_product" in entities.get("reasons", [])

    # Delivery tracking
    intent, conf = IntentClassifier.classify("Where is my package? The courier tracking says delayed.")
    assert intent == IntentType.DELIVERY_TRACKING


def test_ambiguous_requests_clarification():
    """
    Requirement 10: Test ambiguous or vague customer requests.
    Should return AMBIGUOUS intent, request clarification, and offer suggested actions.
    """
    agent = SupportIQAgent()

    for vague_message in ["", "   ", "hello", "hi", "help", "???", "agent"]:
        response = agent.process_message(vague_message)
        assert response.intent == IntentType.AMBIGUOUS.value
        assert response.intent_confidence <= 0.30
        assert "SupportIQ AI Assistant" in response.response
        assert len(response.suggested_actions) > 0
        assert response.requires_human_approval is False
        assert response.simulation is None


# =============================================================================
# 2. RAG Retrieval & Missing Documents Tests (Requirements 3, 10)
# =============================================================================

def test_successful_rag_retrieval():
    """
    Requirement 10: Test successful policy passage retrieval using RAG.
    Querying about refund policy should retrieve refund_policy.md passages with high score.
    """
    agent = SupportIQAgent()
    response = agent.process_message("What is your refund policy window for returning items?")

    assert len(response.rag_passages) > 0
    top_passage = response.rag_passages[0]
    assert "refund" in top_passage["source"].lower() or "refund" in top_passage["document_title"].lower()
    assert top_passage["score"] > 0.05
    assert len(top_passage["text"]) > 20

    # Ensure tool was recorded
    tool_names = [t.name for t in response.tools_called]
    assert "search_knowledge_base" in tool_names


def test_missing_documents_graceful_handling(tmp_path):
    """
    Requirement 10: Test missing documents or query completely out of scope.
    The agent must handle missing documents gracefully without throwing an exception.
    """
    # Create an empty knowledge base with no documents
    empty_dir = tmp_path / "empty_docs"
    empty_dir.mkdir()
    empty_kb = KnowledgeBase(docs_dir=empty_dir)

    agent = SupportIQAgent(knowledge_base=empty_kb)
    response = agent.process_message("What is the policy for Martian space suits?")

    # Should not crash, returns empty passages or graceful notice
    assert isinstance(response.rag_passages, list)
    assert len(response.rag_passages) == 0
    assert "couldn't locate a specific policy" in response.response or len(response.response) > 0


# =============================================================================
# 3. LLM Credentials & Offline Fallback Tests (Requirements 4, 5, 10)
# =============================================================================

def test_unavailable_llm_credentials():
    """
    Requirements 5 & 10: Return clear error or unavailable status when LLM is not configured.
    Must not crash, must return llm_status='unavailable', and produce safe grounded fallback.
    """
    # Explicitly unconfigured LLM provider
    unconfigured_llm = LLMProvider(provider="none", api_key=None)
    assert unconfigured_llm.is_available() is False

    agent = SupportIQAgent(llm_provider=unconfigured_llm)
    response = agent.process_message("What is the warranty coverage on electronic devices?")

    # Verify status
    assert response.llm_status == "unavailable"
    assert response.error is not None
    assert "not configured" in response.error.lower()

    # Grounded fallback must still synthesize the policy information
    assert len(response.response) > 30
    assert "Warranty Policy" in response.response or "warranty" in response.response.lower()


def test_available_llm_mock_generation():
    """
    Requirement 4: When LLM credentials are available, generate grounded response.
    """
    mock_llm = LLMProvider(provider="groq", api_key="test_mock_key")
    # Mock the internal Groq API caller
    with patch.object(mock_llm, "_call_groq", return_value="Order #1001 is eligible for immediate cancellation under our policy."):
        agent = SupportIQAgent(llm_provider=mock_llm)
        response = agent.process_message("Please cancel my order 1001")

        assert response.llm_status == "available"
        assert response.error is None
        assert "Order #1001 is eligible for immediate cancellation" in response.response


# =============================================================================
# 4. Controlled Tool Registry & Safety Guardrails (Requirements 6, 8)
# =============================================================================

def test_controlled_tool_registry_blocks_prohibited_mutations():
    """
    Requirements 6 & 8: Define controlled registry and NEVER execute real refunds/cancellations.
    Prohibited mutation operations must be blocked with an unauthorized error.
    """
    registry = ControlledToolRegistry()

    # Verify approved tools exist
    assert registry.has_tool("search_knowledge_base")
    assert registry.has_tool("simulate_action")
    assert registry.has_tool("predict_support_risk")

    # Verify prohibited operations are completely blocked from execution
    for prohibited in PROHIBITED_MUTATION_OPERATIONS:
        result = registry.execute_tool(prohibited, {"order_id": 1001})
        assert result["status"] == "unauthorized"
        assert "Prohibited Operation" in result["error"]
        assert result["human_approval_required"] is True

    # Attempting to register a prohibited mutation tool must raise ValueError
    with pytest.raises(ValueError):
        registry.register_tool(
            name="execute_real_refund",
            func=lambda: None,
            description="Prohibited",
            parameters={},
        )


# =============================================================================
# 5. Action Simulation & Human Approval Tests (Requirements 7, 8, 9)
# =============================================================================

def test_action_simulation_low_risk_auto_eligible():
    """
    Requirement 7: Allow the agent to request action simulation.
    Low-risk cancellation on an ACTIVE order should be auto-eligible and not require human approval.
    """
    agent = SupportIQAgent()
    request_data = {
        "message": "Can I cancel my active order #1001?",
        "order_id": 1001,
        "order_state": {
            "order_id": 1001,
            "customer_id": 901,
            "status": "ACTIVE",
            "total_amount": 150.0,
            "payment_status": "PAID",
            "delivery_status": "NOT_SHIPPED",
        },
    }

    response = agent.process_message(request_data)

    assert response.intent == IntentType.ORDER_CANCELLATION.value
    assert response.simulation is not None
    assert response.simulation["action"] == "cancel_order"
    assert response.simulation["policy_status"] == PolicyStatus.ELIGIBLE.value
    assert response.simulation["risk_level"] == RiskLevel.LOW.value
    assert response.simulation["recommendation"] == Recommendation.EXECUTE.value
    assert response.requires_human_approval is False


def test_action_simulation_sensitive_refund_requires_human_approval():
    """
    Requirement 9: Sensitive actions (refund > $1,000) require backend human approval.
    """
    agent = SupportIQAgent()
    request_data = {
        "message": "I need a refund of $2499 for order #10291",
        "order_id": 10291,
        "order_state": {
            "order_id": 10291,
            "customer_id": 9281,
            "status": "ACTIVE",
            "total_amount": 2499.0,
            "payment_status": "PAID",
        },
    }

    response = agent.process_message(request_data)

    assert response.intent == IntentType.REFUND_REQUEST.value
    assert response.simulation is not None
    assert response.simulation["amount"] == 2499.0
    assert response.simulation["risk_level"] == RiskLevel.MEDIUM.value
    assert response.requires_human_approval is True
    assert "approval" in response.response.lower() or "manager" in response.response.lower()


def test_backend_policy_non_override_protection():
    """
    Requirement 9 & Constraint: LLM cannot override backend policy rules.
    If LLM claims an action is auto-executed, controller enforces human approval.
    """
    mock_llm = LLMProvider(provider="groq", api_key="test_mock_key")
    # Simulate an LLM hallucinating that a $25,000 refund was already auto-credited
    hallucinated_answer = "Great news! I have approved and transferred the $25,000 refund directly to your bank account!"

    with patch.object(mock_llm, "_call_groq", return_value=hallucinated_answer):
        agent = SupportIQAgent(llm_provider=mock_llm)
        request_data = {
            "message": "Refund $25000 for my order #9999",
            "order_id": 9999,
            "order_state": {
                "order_id": 9999,
                "customer_id": 9999,
                "status": "ACTIVE",
                "total_amount": 25000.0,
                "payment_status": "PAID",
            },
        }

        response = agent.process_message(request_data)

        # Backend policy MUST enforce human approval
        assert response.requires_human_approval is True
        assert response.simulation["risk_level"] == RiskLevel.HIGH.value
        # Safety gate notice must be appended to the LLM response
        assert "requires approval" in response.response.lower() or "manager" in response.response.lower()


def test_shipped_order_cancellation_blocked():
    """Cancelling a SHIPPED order violates policy and must be flagged as ineligible."""
    agent = SupportIQAgent()
    request_data = {
        "message": "Cancel order #5555 immediately",
        "order_id": 5555,
        "order_state": {
            "order_id": 5555,
            "customer_id": 888,
            "status": "SHIPPED",
            "total_amount": 200.0,
            "payment_status": "PAID",
            "delivery_status": "IN_TRANSIT",
        },
    }

    response = agent.process_message(request_data)

    assert response.simulation is not None
    assert response.simulation["policy_status"] == PolicyStatus.INELIGIBLE.value
    assert response.simulation["recommendation"] == Recommendation.BLOCKED.value
    assert "cannot be completed" in response.response or "ineligible" in response.response


# =============================================================================
# 6. Predictive Risk Integration Test
# =============================================================================

def test_predictive_risk_integration():
    """Verify integration of Predictive Support Intervention Engine."""
    agent = SupportIQAgent()
    request_data = {
        "message": "Where is my package? It is 3 days late.",
        "operational_data": {
            "delivery_delay": 3,
            "previous_complaints": 2,
            "courier_reliability": "low",
            "warehouse_backlog": "high",
            "order_value": 4800.0,
            "payment_status": "PAID",
            "product_category": "electronics",
            "cancellation_history": 0,
        },
    }

    response = agent.process_message(request_data)

    assert response.prediction is not None
    assert response.prediction["support_probability"] >= 0.70
    assert len(response.prediction.get("reasons") or response.prediction.get("top_reasons", [])) > 0
