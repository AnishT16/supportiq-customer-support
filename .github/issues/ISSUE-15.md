---
title: "[Backend] Action Simulation Service, Policy Verification & Human Approval REST APIs"
labels: ["backend", "simulation", "policies", "dev-a", "milestone-7"]
assignee: "Dev A"
milestone: "Milestone 7: AI Action Simulation & Policy Engine"
dependencies: ["ISSUE-05", "ISSUE-07"]
---

## Summary & Objective
Implement the backend action simulation and policy verification service based on Section 8, Section 10, and Section 15 of README.md. When an action (e.g. `refund`, `cancel_order`) is proposed, simulate it on an isolated temporary state copy, evaluate multi-tier policies, calculate impact deltas, and route high-risk requests to human approval.

## Specifications & Requirements
- App: `simulations/`, `policies/`, `approvals/`
- Integration:
  - Utilize `SimulationEngine` from `ai_engine.simulation`.
  - Temporary state sandboxing: copy target Order, Payment, Inventory, and Customer entities into temporary schemas without touching production DB.
- Policy Enforcement (Section 10 & Policy Markdown Docs):
  - Refund <= $1,000 -> `LOW` risk, Auto Execute.
  - Refund $1,001–$5,000 -> `MEDIUM` risk, Manager Approval required.
  - Refund > $5,000 -> `HIGH` risk, Executive / Fraud Review required.
  - Cancel on `ACTIVE`/`PAID`/`PROCESSING` -> `LOW` risk, Auto Execute.
  - Cancel on `SHIPPED`/`DELIVERED` -> Policy violation: `BLOCKED`.
  - Customer with > 2 previous refunds -> Requires human review.
- Endpoints:
  - `POST /api/simulations/run/` (Execute sandbox simulation and return impact delta)
  - `GET /api/simulations/` (List all simulated actions with risk levels)
  - `GET /api/simulations/{id}/` (Retrieve detailed simulation before/after report)
  - `POST /api/approvals/{id}/approve/` (Manager approves medium/high-risk action -> applies to real DB)
  - `POST /api/approvals/{id}/reject/` (Manager rejects proposed action with notes)

## Schema Contract (Matches Section 15 of README.md)
`POST /api/simulations/run/`
Request:
```json
{
  "action": "refund",
  "order_id": 10291,
  "payload": { "amount": 2499.0 }
}
```
Response (HTTP 200):
```json
{
  "simulation_id": "sim_7721",
  "action": "refund",
  "order_id": 10291,
  "policy_status": "ELIGIBLE",
  "risk_level": "MEDIUM",
  "recommendation": "REQUIRE_HUMAN_APPROVAL",
  "human_approval_required": true,
  "impact_delta": {
    "customer_impact": "POSITIVE",
    "financial_impact": -2499.0,
    "inventory_impact": 1,
    "coupon_impact": "COUPON_VOIDED"
  },
  "before_state": { "status": "ACTIVE", "payment_status": "PAID" },
  "simulated_state": { "status": "CANCELLED", "payment_status": "REFUNDED" },
  "policy_violations": []
}
```

## Acceptance Criteria
- [ ] Simulation operates in a strictly sandboxed environment without altering the production database.
- [ ] Thresholds precisely enforce <=$1,000 auto-execute, $1,001–$5,000 manager approval, >$5,000 executive approval.
- [ ] Shipped/Delivered order cancellation attempts are blocked with clear policy violation messages.
- [ ] Approving a pending simulation triggers real database state transition and records an audit log.
- [ ] Full unit test suite covers all risk levels, violations, and state transitions.
