---
title: "[QA] End-to-End Integration, Smoke Tests & API/UI Walkthrough Validation"
labels: ["qa", "testing", "integration", "dev-a", "dev-b", "milestone-10"]
assignee: "Dev A & Dev B"
milestone: "Milestone 10: Dockerization & Deployment"
dependencies: ["ISSUE-22", "ISSUE-23"]
---

## Summary & Objective
Joint validation task for Dev A and Dev B to verify the end-to-end integration between React Frontend, Django REST API, PostgreSQL, and the AI Engine. Execute the core platform user flows from Section 1, Section 8, and Section 18 of README.md to ensure all integration points work seamlessly.

## Key Scenarios to Validate
1. **Flow 1: Reactive AI Support & Policy Inquiries (Section 9)**:
   - Customer logs in, asks AI Support about return rules.
   - AI calls `search_knowledge_base`, returns citations from `refund_policy.md`, and quotes the 30-day window.
2. **Flow 2: Safe Low-Risk Action Simulation (Section 8)**:
   - Customer requests cancellation of an `ACTIVE` $750 order.
   - AI runs simulation -> Returns `LOW` risk, Policy: `Eligible`, `AUTO EXECUTE`.
   - Order transitions to `CANCELLED`, inventory increases by 1, audit log recorded.
3. **Flow 3: High-Risk Action & Manager Approval Routing (Section 8.1)**:
   - Customer requests refund on a $2,499 order.
   - AI runs simulation -> Returns `MEDIUM` risk, Recommendation: `REQUIRE_HUMAN_APPROVAL`.
   - Action appears in Agent/Manager Approval Queue (`ISSUE-16`).
   - Manager reviews state diff, clicks Approve -> Real DB is updated, customer notified.
4. **Flow 4: Proactive Predictive Intervention (Section 7)**:
   - Order experiences 3-day carrier delay.
   - Predictive engine scores risk at 91% -> Dispatches proactive notification.
   - Customer views alert banner on dashboard, accepts one-click shipping refund remedy.
5. **Flow 5: Policy Guardrail Defense (Section 10)**:
   - Customer asks AI to cancel an order already marked `SHIPPED`.
   - Policy engine blocks action with `Restricted Status` violation -> AI guides user to wait for delivery and initiate RMA.

## Acceptance Criteria
- [ ] Complete 5-flow integration walkthrough executes successfully with zero unhandled exceptions.
- [ ] End-to-end latency for AI chat responses remains responsive (< 2s).
- [ ] Manager KPI dashboard accurately reflects tickets, resolutions, and simulations from the demo walkthrough.
- [ ] Final documentation updated with local run steps (`docker compose up`).
