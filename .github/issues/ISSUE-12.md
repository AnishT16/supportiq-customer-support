---
title: "[Frontend] Interactive AI Chat Drawer & Real-Time Tool Calling Visualizer"
labels: ["frontend", "ai-engine", "ui/ux", "dev-b", "milestone-5"]
assignee: "Dev B"
milestone: "Milestone 5: AI Customer Support Agent"
dependencies: ["ISSUE-02", "ISSUE-04", "ISSUE-06"]
---

## Summary & Objective
Build an interactive AI Support Chat interface (both as an omnipresent floating widget and a full-page view). The chat UI displays multi-turn conversations, typing states, suggested action chips, and a collapsible visualizer displaying which backend tools the AI called (e.g., `Checked Order #1001`, `Searched Refund Policy`).

## Specifications & Requirements
- Views & Components:
  - `AISupportChatWidget.jsx`: Floating chat bubble with badge that expands into a rich conversation drawer.
  - `ChatMessageItem.jsx`: Clean message bubble with markdown formatting support, citations to policy docs, and interactive confirmation buttons.
  - `ToolCallPills.jsx`: Collapsible activity banner showing internal tool invocations:
    - ⚡ `Called get_order(order_id: 1001)` -> Result: `Status: ACTIVE`
    - 🔍 `Searched Knowledge Base` -> Source: `cancellation_policy.md`
  - `QuickActionChips.jsx`: Interactive pills below responses (e.g. `Track Package`, `Cancel Order`, `Talk to Human`).
  - Auto-scroll to latest message and loading skeleton during AI thinking states.

## Mock State Contract
```javascript
const MOCK_CHAT_RESPONSE = {
  response: "I've checked Order #1001. It is currently in ACTIVE status and eligible for immediate cancellation.",
  intent: "ORDER_CANCELLATION",
  tools_called: [
    { name: "get_order", arguments: { order_id: 1001 } },
    { name: "search_knowledge_base", arguments: { query: "cancellation policy" } }
  ],
  suggested_actions: ["Confirm Cancellation", "Talk to Human Agent"]
};
```

## Acceptance Criteria
- [ ] Chat drawer opens smoothly from anywhere in the customer portal.
- [ ] User can type questions or click suggestion chips to send messages.
- [ ] Tool execution pills toggle open to reveal which internal tools and documents were used.
- [ ] Markdown links inside AI responses open the policy reader drawer directly.
