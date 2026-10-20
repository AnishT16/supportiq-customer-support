# SupportIQ AI Support Agent Controller

A production-ready, safe AI customer support agent orchestrator designed for integration with Django REST Framework and Celery asynchronous tasks.

The agent unifies:
- **Intent Recognition & Entity Extraction** (`IntentClassifier`)
- **RAG Policy Retrieval** (`KnowledgeBase` & `search_knowledge_base`)
- **AI Action Simulation** (`SimulationEngine` - zero real database/payment mutations)
- **Predictive Support ML** (`PredictionEngine` for churn and issue prediction)
- **Grounded LLM Synthesis** (Groq / OpenAI with safe unconfigured fallback)
- **Controlled Tool Registry** (Strict safety constraints and approval enforcement)

---

## 1. Quick Start for Django Developers

### Basic Usage in a DRF API View

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ai_engine.agent import SupportIQAgent, AgentRequest

class SupportChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        customer_id = getattr(user, "customer_id", user.id)

        # 1. Initialize agent (uses default RAG knowledge base & tool registry)
        agent = SupportIQAgent()

        # 2. Build agent request
        agent_req = AgentRequest(
            message=request.data.get("message", ""),
            customer_id=customer_id,
            order_id=request.data.get("order_id"),
            user_role=getattr(user, "role", "customer"),
            order_state=request.data.get("order_state"), # Optional real DB state
            operational_data=request.data.get("operational_data"),
            conversation_id=request.data.get("conversation_id"),
        )

        # 3. Process message
        agent_resp = agent.process_message(agent_req)

        # 4. Return serialized dictionary
        return Response(agent_resp.to_dict(), status=status.HTTP_200_OK)
```

---

## 2. API Contract Schema

### Request: `POST /api/support/chat/`
```json
{
  "message": "Can I cancel my order 1001?",
  "order_id": 1001,
  "conversation_id": "conv_9281"
}
```

### Response (HTTP 200):
```json
{
  "response": "Order #1001 is eligible for immediate cancellation (Impact: -$100.00). All policy checks passed. According to our Cancellation Policy: \"Orders in ACTIVE, PAID, or PROCESSING status may be cancelled immediately for a full refund before courier dispatch.\"",
  "intent": "ORDER_CANCELLATION",
  "intent_confidence": 0.95,
  "entities": {
    "order_id": 1001
  },
  "tools_called": [
    {
      "name": "search_knowledge_base",
      "arguments": { "query": "Can I cancel my order 1001? cancellation policy cutoff window active shipped" },
      "status": "success"
    },
    {
      "name": "simulate_action",
      "arguments": { "action": "cancel_order", "order_id": 1001 },
      "status": "success"
    }
  ],
  "rag_passages": [
    {
      "document_title": "Cancellation Policy",
      "source": "cancellation_policy.md",
      "section": "1. Cancellation Window",
      "score": 0.82
    }
  ],
  "simulation": {
    "action": "cancel_order",
    "order_id": 1001,
    "policy_status": "eligible",
    "risk_level": "LOW",
    "financial_impact": -100.0,
    "human_approval_required": false,
    "recommendation": "execute"
  },
  "suggested_actions": ["Confirm Cancellation", "Modify Order Items", "Keep Order"],
  "llm_status": "unavailable",
  "error": "LLM provider is not configured. Set GROQ_API_KEY or OPENAI_API_KEY to enable LLM generation.",
  "requires_human_approval": false,
  "human_approval_reason": null,
  "audit_trail": [
    { "tool": "search_knowledge_base", "status": "success", "results_count": 3 },
    { "tool": "simulate_action", "action": "cancel_order", "status": "success", "requires_approval": false }
  ]
}
```

---

## 3. Core Safety Rules & Guardrails

1. **Zero Real Mutations**: The agent is restricted to `simulate_action`. It cannot perform direct refunds, card charges, or database deletions.
2. **Backend Policy Non-Override**: If an action exceeds policy limits (e.g. refund > $1,000, or cancelling a shipped order), the backend policy validator flags `requires_human_approval = True`. The LLM cannot override or bypass this flag.
3. **Graceful Offline Fallback**: If `GROQ_API_KEY` or `OPENAI_API_KEY` is not configured, the agent sets `llm_status = "unavailable"` and outputs a deterministic, policy-grounded response.
