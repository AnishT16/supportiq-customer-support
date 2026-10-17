---
title: "[Frontend] Simulation Impact Visualizer & Agent Approval Queue Dashboard"
labels: ["frontend", "simulation", "ui/ux", "dev-b", "milestone-7"]
assignee: "Dev B"
milestone: "Milestone 7: AI Action Simulation & Policy Engine"
dependencies: ["ISSUE-04", "ISSUE-06"]
---

## Summary & Objective
Build the UI interface for AI Action Simulation inspection and the Human Approval Queue. Support agents and managers can review proposed high-risk actions (e.g. $2,499 refunds), inspect visual before/after state diffs, examine policy compliance, and click to approve or reject with audit notes.

## Specifications & Requirements
- Views & Components:
  - `ApprovalQueuePage.jsx`: Filterable queue of pending actions grouped by risk (`MEDIUM`, `HIGH`) and action type (`REFUND`, `CANCEL`).
  - `SimulationImpactModal.jsx`: Visual audit card matching Section 8 of README.md:
    - Current State vs Simulated State (Diff comparison table).
    - Impact Badges:
      - Customer Impact: `Positive` (Green pill)
      - Financial Impact: `-$2,499.00` (Red pill)
      - Inventory Impact: `+1 item back to stock` (Blue pill)
    - Policy Status: `Eligible` / `Violation Detected`
    - Risk Tier Indicator: `LOW` (Auto), `MEDIUM` (Manager Review), `HIGH` (Executive Sign-Off)
  - `ApprovalActionButtons.jsx`:
    - `Approve & Execute Action` (Green primary button with confirmation prompt)
    - `Reject Action` (Red outline button prompting for reason text)

## Mock State Contract
```javascript
const MOCK_PENDING_APPROVAL = {
  simulation_id: "sim_7721",
  created_at: "2026-10-16T11:20:00Z",
  action: "refund",
  order_id: 10291,
  customer_name: "John Connor",
  amount: 2499.0,
  risk_level: "MEDIUM",
  recommendation: "REQUIRE_HUMAN_APPROVAL",
  financial_impact: -2499.0,
  inventory_impact: 1,
  policy_status: "ELIGIBLE"
};
```

## Acceptance Criteria
- [ ] Approval queue dynamically lists pending approvals with urgency indicators.
- [ ] Visual diff highlights exactly what state will change prior to execution.
- [ ] Clicking Approve executes the API call, removes item from queue, and shows a success toast.
- [ ] Rejecting prompts for a rejection reason and logs the decision.
