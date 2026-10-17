---
title: "[Frontend] Knowledge Base Policy Explorer & Live Search UI with Markdown Rendering"
labels: ["frontend", "ui/ux", "rag", "dev-b", "milestone-4"]
assignee: "Dev B"
milestone: "Milestone 4: RAG & Knowledge Base"
dependencies: ["ISSUE-02", "ISSUE-04"]
---

## Summary & Objective
Build a dedicated Knowledge Base and Help Center view where customers and support agents can search company policies, browse categorized FAQs, and view full markdown policy documents with rich syntax highlighting and citation deep-linking.

## Specifications & Requirements
- Views & Components:
  - `KnowledgeBaseExplorerPage.jsx`: Search bar with instant debounced search query execution.
  - `PolicyCardGrid.jsx`: Cards representing each policy document:
    - Customer Refund Policy
    - Order Cancellation Policy
    - Shipping & Delivery Policy
    - Product Warranty & Care+
    - Payment & Billing FAQ
  - `PolicyReaderDrawer.jsx`: Slide-over drawer displaying rendered Markdown policy document using `react-markdown`.
  - `SearchResultPassage.jsx`: Highlights matched section heading, similarity score pill, and snippet context.

## Mock Data Contract
```javascript
const MOCK_POLICY_CATALOG = [
  { source: "refund_policy.md", title: "SupportIQ Customer Refund Policy", category: "Refunds", icon: "DollarSign" },
  { source: "cancellation_policy.md", title: "SupportIQ Order Cancellation Policy", category: "Orders", icon: "XCircle" },
  { source: "shipping_policy.md", title: "SupportIQ Shipping & Delivery Policy", category: "Shipping", icon: "Truck" },
  { source: "warranty_policy.md", title: "SupportIQ Product Warranty Policy", category: "Warranty", icon: "ShieldCheck" },
  { source: "payment_faq.md", title: "SupportIQ Payment & Billing FAQ", category: "Billing", icon: "CreditCard" }
];
```

## Acceptance Criteria
- [ ] Policy catalog displays all categories with clean iconography and descriptions.
- [ ] Debounced search returns matched passages as the user types (300ms debounce).
- [ ] Clicking a policy card or search passage opens the Markdown drawer at the relevant section.
- [ ] Responsive on both desktop and mobile viewports.
