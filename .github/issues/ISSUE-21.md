---
title: "[Frontend] System Audit Log Explorer & Security Activity UI"
labels: ["frontend", "security", "audit", "ui/ux", "dev-b", "milestone-9"]
assignee: "Dev B"
milestone: "Milestone 9: Security & Audit Logging"
dependencies: ["ISSUE-04", "ISSUE-18"]
---

## Summary & Objective
Build an administrator and manager-facing Audit Log Explorer UI. Enables oversight of all AI automated decisions, human approval overrides, tool calls, and security events with rich filtering, JSON payload inspection, and export options.

## Specifications & Requirements
- Views & Components:
  - `AuditLogPage.jsx`: Filterable data table of system security and AI events.
  - Filter Controls:
    - Event Type (`AI_TOOL_EXECUTION`, `SIMULATION_EVALUATION`, `MANAGER_APPROVAL`, `PROACTIVE_INTERVENTION`)
    - Date range picker
    - Actor (AI Agent, Human Agent, Customer)
  - `AuditDetailDrawer.jsx`: Inspect before/after state diff, request IP, full tool argument JSON, and policy rule evaluations.
  - Role Guard: Only accessible to users with `MANAGER` or `ADMINISTRATOR` roles.

## Mock State Contract
```javascript
const MOCK_AUDIT_LOGS = [
  {
    id: 1043,
    event_type: "MANAGER_APPROVAL",
    actor: "Manager (alex@supportiq.com)",
    resource: "Simulation #sim_7721",
    action: "REFUND_APPROVED",
    details: "Approved $2,499 refund for Order #10291 following delivery damage confirmation.",
    timestamp: "2026-10-16 11:48:12"
  },
  {
    id: 1042,
    event_type: "AI_SIMULATION",
    actor: "AI Agent",
    resource: "Order #10291",
    action: "SIMULATE_REFUND",
    details: "Risk: MEDIUM, Recommendation: REQUIRE_HUMAN_APPROVAL",
    timestamp: "2026-10-16 11:45:00"
  }
];
```

## Acceptance Criteria
- [ ] Displays live log stream with distinct status badges and timestamps.
- [ ] Slide-out drawer renders formatted JSON payloads of audit metadata.
- [ ] Real-time search by order ID, customer ID, or simulation ID.
- [ ] Protected by RoleGuard against unauthorized customer role access.
