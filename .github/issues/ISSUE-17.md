---
title: "[Backend] Analytics & Aggregation APIs for Support, Predictions & Simulations"
labels: ["backend", "analytics", "api", "dev-a", "milestone-8"]
assignee: "Dev A"
milestone: "Milestone 8: Role Dashboards & Analytics"
dependencies: ["ISSUE-05", "ISSUE-07", "ISSUE-13", "ISSUE-15"]
---

## Summary & Objective
Implement high-performance aggregation and metrics endpoints for the Manager and Agent dashboards as outlined in Section 16 of README.md. Calculate KPI metrics across ticket volumes, AI resolution rate, prediction accuracy, and simulation risk distributions.

## Specifications & Requirements
- App: `analytics/`
- Endpoints:
  - `GET /api/analytics/manager/kpis/`:
    - `total_tickets`
    - `ai_resolved_tickets`
    - `human_escalated_tickets`
    - `ai_resolution_rate` (percentage)
    - `predicted_incidents`
    - `successful_proactive_interventions`
  - `GET /api/analytics/manager/timeseries/`:
    - Daily ticket volume breakdown (AI resolved vs Human escalated over last 30 days).
  - `GET /api/analytics/simulations/summary/`:
    - Distribution of simulations by outcome (`AUTO_APPROVED`, `HUMAN_APPROVED`, `BLOCKED`).
  - `GET /api/analytics/predictions/risk-distribution/`:
    - Breakdown of customer risk levels (`LOW`, `MEDIUM`, `HIGH`) and category frequencies (`DELIVERY`, `REFUND`, etc.).
- Performance:
  - Utilize Django ORM aggregation (`Count`, `Avg`, `Q` filters) and cache KPI outputs with a 5-minute TTL to ensure fast dashboard load times (<50ms).

## Schema Contract (Matches Section 16 of README.md)
`GET /api/analytics/manager/kpis/`
Response (HTTP 200):
```json
{
  "total_tickets": 12482,
  "ai_resolved": 8721,
  "human_escalated": 2341,
  "predicted_incidents": 1204,
  "successful_predictions": 914,
  "ai_resolution_rate": 69.8
}
```

## Acceptance Criteria
- [ ] Returns aggregated metrics matching the exact KPI fields defined in Section 16.
- [ ] Timeseries endpoint outputs daily buckets suitable for Recharts line and bar graphs.
- [ ] Endpoint is protected with `IsManager` permission class.
- [ ] Unit tests verify mathematical calculation of resolution rate and aggregation accuracy.
