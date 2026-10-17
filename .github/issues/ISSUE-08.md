---
title: "[Frontend] Support Ticketing UI (Customer Ticket List, Message Thread & Create Ticket Modal)"
labels: ["frontend", "ui/ux", "support", "dev-b", "milestone-3"]
assignee: "Dev B"
milestone: "Milestone 3: Support Ticketing System"
dependencies: ["ISSUE-04", "ISSUE-06"]
---

## Summary & Objective
Build the customer-facing support ticketing interface where customers can browse their previous tickets, review conversation logs with timestamps, submit follow-up replies, and file new support tickets with category tagging and order attachments.

## Specifications & Requirements
- Views & Components:
  - `CustomerTicketsPage.jsx`: Filterable ticket table/cards (filter by `OPEN`, `RESOLVED`, `ALL`).
  - `TicketConversationView.jsx`: Chat-style message thread with distinct visual styling for Customer messages, Human Agent replies, and AI Automated notifications.
  - `CreateTicketModal.jsx`: Form with order selector dropdown, category picker, priority, and rich text/markdown message input.
  - Quick action to request escalation to a human agent when chatting with AI.

## Mock State Contract
```javascript
const MOCK_TICKET_THREAD = {
  ticket_id: 401,
  subject: "Package delayed past estimated date",
  status: "OPEN",
  category: "DELIVERY",
  messages: [
    { id: 1, sender: "CUSTOMER", text: "My order was supposed to arrive 3 days ago.", time: "10:00 AM" },
    { id: 2, sender: "AI_AGENT", text: "I've checked with carrier FedEx (TRK9281928). Your package is in transit with weather delays.", time: "10:01 AM" },
    { id: 3, sender: "AGENT", text: "Hello Jane, I'm reviewing the carrier logs and will expedite a replacement if needed.", time: "10:15 AM" }
  ]
};
```

## Acceptance Criteria
- [ ] Ticket list displays accurate status badges and relative timestamps (e.g. "2 hours ago").
- [ ] Message thread displays chronologically with clear distinction between Customer, Agent, and AI.
- [ ] Customer can append new replies with auto-scroll to bottom of conversation thread.
- [ ] Form validation prevents submission of empty subjects or messages.
