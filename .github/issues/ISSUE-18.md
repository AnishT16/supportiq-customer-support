---
title: "[Frontend] Manager Analytics Dashboard (KPI Cards, Recharts Trends & Resolution Rates)"
labels: ["frontend", "analytics", "recharts", "ui/ux", "dev-b", "milestone-8"]
assignee: "Dev B"
milestone: "Milestone 8: Role Dashboards & Analytics"
dependencies: ["ISSUE-02", "ISSUE-04"]
---

## Summary & Objective
Build the Manager Analytics Dashboard conforming to Section 16 of README.md. Implement executive KPI metric cards, interactive chart visualizations using `recharts`, prediction accuracy monitors, and simulation breakdown charts.

## Specifications & Requirements
- Views & Components:
  - `ManagerDashboardPage.jsx`: Top-level dashboard layout.
  - `KPISummaryGrid.jsx`: 6 primary metric cards:
    - Total Tickets (12,482)
    - AI Resolved Tickets (8,721)
    - Human Escalated Tickets (2,341)
    - AI Resolution Rate (69.8%)
    - Predicted Incidents (1,204)
    - Successful Proactive Interventions (914)
  - `TicketVolumeChart.jsx`: Recharts area/line chart displaying 30-day trend of total tickets vs AI resolutions.
  - `SimulationOutcomesDonut.jsx`: Donut chart showing breakdown of simulated actions:
    - Auto Approved (64%)
    - Human Approval Required (28%)
    - Blocked by Policy (8%)
  - `PredictionRiskTable.jsx`: Ranked list of customers with highest predicted support contact probabilities.

## Mock Data Contract
```javascript
const MOCK_MANAGER_KPIS = {
  total_tickets: 12482,
  ai_resolved: 8721,
  human_escalated: 2341,
  predicted_incidents: 1204,
  successful_predictions: 914,
  ai_resolution_rate: 69.8
};
```

## Acceptance Criteria
- [ ] Displays all 6 KPI cards with sparklines and percentage delta comparisons.
- [ ] Recharts graphs render smoothly with tooltips, legend, and responsive sizing.
- [ ] Simulation donut chart displays accurate color codes (Green for Auto, Amber for Human, Red for Blocked).
- [ ] High-risk customer table allows managers to drill into individual customer risk factors.
