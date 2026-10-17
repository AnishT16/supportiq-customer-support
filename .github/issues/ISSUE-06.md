---
title: "[Frontend] Customer Portal UI (Order History, Order Details, Live Delivery Tracker & Customer Profile)"
labels: ["frontend", "ui/ux", "dev-b", "milestone-2"]
assignee: "Dev B"
milestone: "Milestone 2: Core E-Commerce Entities"
dependencies: ["ISSUE-02", "ISSUE-04"]
---

## Summary & Objective
Build the Customer Portal interface where logged-in customers can view their recent purchases, drill down into order breakdowns, inspect live delivery tracking status (Ground/Expedited/Overnight), and launch support actions.

## Specifications & Requirements
- Pages & Views:
  - `CustomerOrdersPage.jsx`: Filterable order list with status badges (`PAID`, `SHIPPED`, `DELIVERED`, `CANCELLED`).
  - `OrderDetailModal.jsx`: Breakdown of line items, unit pricing, payment details, and shipping carrier info.
  - `DeliveryTracker.jsx`: Visual step-progress bar (`Accepted` -> `In Transit` -> `Out for Delivery` -> `Delivered`) highlighting any shipping delay alert (e.g. `+3 days delay` warning).
  - Quick action buttons on eligible orders:
    - `Cancel Order` (active if status is `ACTIVE` / `PAID` / `PROCESSING`)
    - `Request Refund` (active within 30-day window)
    - `Need Help with this Order` (initiates context-aware AI chat with order ID prefilled)

## Component Contract & Mock State
```javascript
const MOCK_ORDER = {
  order_id: 10291,
  created_at: "2026-10-12T14:30:00Z",
  status: "PAID",
  total_amount: 2499.0,
  delivery: {
    carrier: "UPS",
    tracking_number: "1Z9999999999999999",
    status: "IN_TRANSIT",
    delay_days: 3,
    estimated_delivery: "2026-10-17"
  }
};
```

## Acceptance Criteria
- [ ] Orders list loads asynchronously with clean loading skeletons and empty state illustrations.
- [ ] Order detail modal accurately displays line items, totals, and payment status.
- [ ] Delivery tracker visually indicates current status milestone and flags delays > 0 days in amber/red.
- [ ] Action buttons (`Cancel Order`, `Request Refund`) adhere to status rules (e.g., disable direct cancel if `SHIPPED`).
