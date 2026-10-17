---
title: "[Frontend] Proactive Customer Notification Banner & Intervention Modal"
labels: ["frontend", "ui/ux", "predictions", "dev-b", "milestone-6"]
assignee: "Dev B"
milestone: "Milestone 6: Predictive Intervention Engine"
dependencies: ["ISSUE-04", "ISSUE-06"]
---

## Summary & Objective
Implement the customer-facing proactive intervention UI components described in Section 7 of README.md. When SupportIQ predicts an emerging issue (such as a 3-day carrier delay), display high-priority proactive notification cards offering one-click resolutions before the customer needs to file a ticket.

## Specifications & Requirements
- Views & Components:
  - `ProactiveAlertBanner.jsx`: Prominent amber banner appearing at top of Customer Dashboard when an active proactive alert exists (e.g. `⚠️ We noticed your shipment TRK9281928 has experienced unexpected carrier transit delays`).
  - `ProactiveActionModal.jsx`: Modal presenting the user with explainable context and immediate self-service remedies:
    - New estimated delivery date.
    - Option 1: "Request Complimentary Shipping Fee Refund" (triggers simulation & auto-refund).
    - Option 2: "Request Free Priority Re-Order Dispatch".
    - Option 3: "Chat with AI Support Agent".
  - `NotificationDropdown.jsx`: Bell icon badge showing unread count in TopBar.

## Mock State Contract
```javascript
const MOCK_PROACTIVE_ALERT = {
  notification_id: 88,
  title: "Delivery Delay Alert for Order #10291",
  message: "Your shipment has been delayed by 3 business days due to severe weather at the courier distribution hub.",
  predicted_issue: "delivery_delay",
  recommended_action: "COMPLIMENTARY_SHIPPING_REFUND",
  options: [
    { label: "Refund Shipping Fee ($15.00)", action: "refund_shipping" },
    { label: "Talk with Support", action: "open_chat" }
  ]
};
```

## Acceptance Criteria
- [ ] Notification badge accurately displays unread proactive interventions.
- [ ] Clicking a notification opens the action modal with clear explainability reasons.
- [ ] Self-service action buttons trigger the appropriate resolution flow without forcing the user to create a complaint ticket.
- [ ] Marking a notification as read updates state locally and via API.
