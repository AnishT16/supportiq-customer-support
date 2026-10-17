---
title: "[Backend] Predictive ML Inference API, Risk Classification & Proactive Alert Dispatcher"
labels: ["backend", "machine-learning", "predictions", "dev-a", "milestone-6"]
assignee: "Dev A"
milestone: "Milestone 6: Predictive Intervention Engine"
dependencies: ["ISSUE-05", "ISSUE-07"]
---

## Summary & Objective
Integrate the trained predictive machine learning pipeline (`ai_engine.predictor`) into the Django application (`predictions/` and `notifications/` apps). Score live customer/order events to compute support contact probability, predict likely issue categories, generate explainable feature attributions, and automatically create proactive notifications.

## Specifications & Requirements
- App: `predictions/`, `notifications/`
- Integration:
  - Utilize `PredictionEngine` and `ExplainabilityEngine` from `ai_engine.predictor`.
  - Feature extraction mapping:
    - `delivery_delay`: days beyond estimated delivery date from `Delivery` model.
    - `previous_complaints`: count of past tickets from `Customer` profile.
    - `courier_reliability`: historical on-time score of assigned carrier (0.0 to 1.0).
    - `warehouse_backlog`: operational metric (0 to 10 scale).
    - `order_value`: total price from `Order`.
    - `payment_status`: paid/failed.
- Endpoints:
  - `POST /api/predictions/score/` (Score a specific customer/order on demand)
  - `GET /api/predictions/` (Manager view of all active predicted support risks)
  - `GET /api/notifications/` (Customer notifications list)
  - `POST /api/notifications/{id}/read/` (Mark notification as read)
- Automation Trigger:
  - When an order delay exceeds 3 days, automatically trigger prediction scoring. If `support_probability >= 0.70`, dispatch a `Notification` record recommending proactive resolution.

## Schema Contract
`POST /api/predictions/score/`
Request:
```json
{
  "customer_id": 9281,
  "order_id": 1002
}
```
Response (HTTP 200 - Matches Section 15 of README.md):
```json
{
  "customer_id": 9281,
  "support_probability": 0.91,
  "predicted_issue": "delivery_delay",
  "risk_level": "HIGH",
  "reasons": [
    "3 day delivery delay",
    "previous complaints: 2",
    "low courier reliability: 0.65"
  ],
  "recommended_intervention": "proactive_notification",
  "notification_created": true
}
```

## Acceptance Criteria
- [ ] Predictive engine scores customer profiles in under 20ms using serialized ML model.
- [ ] Returns explainable contributing factors (e.g. `+3 day delivery delay`).
- [ ] High-risk scores automatically populate customer's proactive notification inbox.
- [ ] Comprehensive unit tests cover scoring pipeline, feature extraction, and notification dispatch.
