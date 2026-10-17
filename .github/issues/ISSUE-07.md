---
title: "[Backend] Support Ticket Lifecycle, Messages & Escalation REST APIs"
labels: ["backend", "api", "support", "dev-a", "milestone-3"]
assignee: "Dev A"
milestone: "Milestone 3: Support Ticketing System"
dependencies: ["ISSUE-03", "ISSUE-05"]
---

## Summary & Objective
Implement the traditional and AI-assisted ticketing backend described in Section 6.1 and Section 12 of README.md. Model tickets, multi-turn messages, status lifecycles (`OPEN`, `PENDING_CUSTOMER`, `ESCALATED`, `RESOLVED`, `CLOSED`), and agent assignment.

## Specifications & Requirements
- Models:
  - `Ticket`: `customer`, `assigned_agent` (nullable), `order` (optional link), `subject`, `category` (`DELIVERY`, `REFUND`, `CANCELLATION`, `PAYMENT`, `PRODUCT`, `OTHER`), `priority` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `status`, `resolved_by_ai` (boolean), `created_at`, `updated_at`.
  - `TicketMessage`: `ticket`, `sender` (`CUSTOMER`, `AGENT`, `AI_AGENT`), `message_text`, `timestamp`.
  - `Escalation`: `ticket`, `reason`, `escalated_by`, `escalated_to`, `resolved_at`.
- Endpoints:
  - `GET /api/tickets/` (Customer views own; Agents/Managers filter by status/priority)
  - `POST /api/tickets/` (Customer creates new support ticket)
  - `GET /api/tickets/{id}/` (Ticket detail with full conversation history)
  - `POST /api/tickets/{id}/messages/` (Send reply to ticket)
  - `POST /api/tickets/{id}/escalate/` (Escalate ticket from AI to human agent queue)
  - `POST /api/tickets/{id}/status/` (Update status to RESOLVED/CLOSED)

## Sample Schema Contract
`POST /api/tickets/`
Request:
```json
{
  "order_id": 1001,
  "category": "DELIVERY",
  "priority": "HIGH",
  "subject": "Package delayed past estimated date",
  "message": "My order was supposed to arrive 3 days ago. Where is it?"
}
```
Response (HTTP 201):
```json
{
  "ticket_id": 401,
  "status": "OPEN",
  "priority": "HIGH",
  "category": "DELIVERY",
  "resolved_by_ai": false,
  "created_at": "2026-10-16T10:00:00Z"
}
```

## Acceptance Criteria
- [ ] Customers can create tickets and append messages to their tickets.
- [ ] Support agents can view, take ownership of, reply to, and resolve tickets.
- [ ] Escalation endpoint flags ticket priority and moves it to human attention queue.
- [ ] Complete unit test coverage for ticket creation, messaging permissions, and state transitions.
