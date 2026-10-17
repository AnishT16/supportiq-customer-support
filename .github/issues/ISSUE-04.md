---
title: "[Frontend] Auth UI & State Management (Login, Register, Protected Routes & Navigation Guards)"
labels: ["frontend", "auth", "ui/ux", "dev-b", "milestone-1"]
assignee: "Dev B"
milestone: "Milestone 1: Authentication & RBAC"
dependencies: ["ISSUE-02"]
---

## Summary & Objective
Build the client-side authentication screens (Login, Customer Registration) and global Auth Context provider. Implement client-side role-based routing guards to enforce security and redirect users according to their persona (`CUSTOMER`, `SUPPORT_AGENT`, `MANAGER`).

## Specifications & Requirements
- State Management: React Context or Zustand store (`useAuthStore`) managing `user`, `token`, `isAuthenticated`, `role`, and `login()`, `logout()`.
- Token Persistence: Secure localStorage / sessionStorage storage with automatic header injection into Axios.
- Route Guards:
  - `<ProtectedRoute>`: Redirect unauthenticated requests to `/login`.
  - `<RoleGuard allowedRoles={['MANAGER']}>`: Restrict access based on current user role.
- UI Components:
  - `LoginPage.jsx`: Clean email/password form with validation, error banners, and loading state.
  - `RegisterPage.jsx`: Customer sign-up form with input validation (email, password match, name).
  - Quick-switch demo persona buttons (`Demo Customer`, `Demo Agent`, `Demo Manager`) for rapid evaluation.

## Mock Contract for Frontend Testing (Before Backend is Connected)
```javascript
// Mock user profiles for dev switcher
const DEMO_USERS = {
  customer: { id: 101, email: "customer@demo.com", role: "CUSTOMER", name: "Sarah Connor" },
  agent: { id: 201, email: "agent@demo.com", role: "SUPPORT_AGENT", name: "Agent Smith" },
  manager: { id: 301, email: "manager@demo.com", role: "MANAGER", name: "Chief Operations" },
};
```

## Acceptance Criteria
- [ ] User can log in with valid credentials, storing JWT in local storage.
- [ ] User is redirected to role-appropriate home view after login:
  - `CUSTOMER` -> `/customer/orders`
  - `SUPPORT_AGENT` -> `/agent/queue`
  - `MANAGER` -> `/manager/analytics`
- [ ] Unauthorized URL access displays a 403 Forbidden alert or redirects gracefully.
- [ ] Logout button clears auth state and redirects to `/login`.
