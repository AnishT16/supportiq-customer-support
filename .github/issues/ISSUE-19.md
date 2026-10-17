---
title: "[Frontend] Support Agent Workspace Dashboard (Queue, Escalations & Customer 360 View)"
labels: ["frontend", "support", "ui/ux", "dev-b", "milestone-8"]
assignee: "Dev B"
milestone: "Milestone 8: Role Dashboards & Analytics"
dependencies: ["ISSUE-04", "ISSUE-08", "ISSUE-16"]
---

## Summary & Objective
Implement the Support Agent Workspace interface designed for frontline customer service representatives. Enables agents to quickly triage open tickets, take over conversations escalated from AI, inspect customer purchase and complaint history (Customer 360), and execute approved remediation actions.

## Specifications & Requirements
- Views & Components:
  - `AgentWorkspacePage.jsx`: Multi-column agent desk layout:
    - Left Column: Active Queue Tabs (`All Open`, `AI Escalations`, `My Assigned`, `High Priority`).
    - Center Column: Active Ticket Thread with quick reply templates and internal agent notes.
    - Right Column: Customer 360 Dossier:
      - Lifetime order count and spend.
      - Past complaint count & refund count.
      - Account flag status (`Clean` vs `Flagged - Manual Review Required`).
      - AI Summary of customer's current issue.
  - Quick action toolbar: `Assign to Me`, `Simulate Refund`, `Simulate Cancellation`, `Resolve Ticket`.

## Mock State Contract
```javascript
const MOCK_CUSTOMER_360 = {
  customer_id: 9281,
  name: "Alexander Pierce",
  email: "alexander@example.com",
  is_flagged: false,
  previous_complaints: 2,
  previous_refunds_count: 1,
  total_orders: 8,
  lifetime_value: 4800.0,
  recent_order_id: 10291
};
```

## Acceptance Criteria
- [ ] Ticket queue sorts by priority (`CRITICAL` and `HIGH` at top).
- [ ] Agent can toggle between customer messages and private internal team notes.
- [ ] Customer 360 dossier renders live customer risk indicators directly beside the ticket.
- [ ] Action buttons hook seamlessly into the Action Simulation modal built in ISSUE-16.
