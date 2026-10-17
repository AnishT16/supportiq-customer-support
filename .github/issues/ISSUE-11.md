---
title: "[Backend] AI Agent Controller, LLM Tool Calling Engine & Action Audit Logger"
labels: ["backend", "ai-engine", "llm", "tools", "dev-a", "milestone-5"]
assignee: "Dev A"
milestone: "Milestone 5: AI Customer Support Agent"
dependencies: ["ISSUE-05", "ISSUE-07", "ISSUE-09"]
---

## Summary & Objective
Implement the LLM agent orchestrator in `ai_engine/` and expose the `POST /api/support/chat/` endpoint conforming to Section 6.1 and 6.2 of README.md. The agent understands customer messages, extracts entities, calls controlled tools, queries RAG, and produces grounded responses while recording an audit log of every tool execution.

## Specifications & Requirements
- Controlled Tools Implementation (Section 6.2):
  1. `get_customer(customer_id)`
  2. `get_order(order_id)`
  3. `get_delivery_status(order_id)`
  4. `get_payment_status(order_id)`
  5. `get_previous_tickets(customer_id)`
  6. `search_knowledge_base(query, top_k)`
  7. `create_ticket(customer_id, category, message)`
  8. `escalate_ticket(ticket_id, reason)`
  9. `calculate_refund(order_id)`
  10. `simulate_action(action, order_id, payload)` (links to Simulation Engine)
  11. `send_notification(customer_id, title, message)`
- Endpoint:
  - `POST /api/support/chat/`
- Tool Calling Architecture:
  - Compatible with Groq / OpenAI / Anthropic / Local mock LLM.
  - Multi-step tool execution loop: Model selects tool -> Backend executes controlled tool -> Output returned to model -> Final synthesized answer.
  - Record each tool invocation in `AuditLog` model (action name, inputs, timestamp, customer_id).

## Contract Schema
`POST /api/support/chat/`
Request:
```json
{
  "message": "Can I cancel my order 1001?",
  "order_id": 1001,
  "conversation_id": "conv_9281"
}
```
Response (HTTP 200):
```json
{
  "response": "I've checked Order #1001. It is currently in ACTIVE status and eligible for immediate cancellation. Would you like me to initiate the cancellation for you?",
  "intent": "ORDER_CANCELLATION",
  "tools_called": [
    { "name": "get_order", "arguments": { "order_id": 1001 } },
    { "name": "search_knowledge_base", "arguments": { "query": "cancellation cut-off window" } }
  ],
  "suggested_actions": ["Confirm Cancellation", "Talk to Human Agent"]
}
```

## Acceptance Criteria
- [ ] Agent recognizes customer intent (refund, cancellation, delivery tracking, policy inquiry).
- [ ] Controlled tools execute securely and validate customer ownership of the requested order.
- [ ] RAG retrieval seamlessly injects relevant policy context into the LLM prompt.
- [ ] Every tool invocation creates an audit trail entry.
- [ ] Mock LLM provider fallback ensures tests pass without active API keys.
