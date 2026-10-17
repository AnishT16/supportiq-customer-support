---
title: "[Backend] Custom User Model, JWT Authentication, and RBAC Permissions"
labels: ["backend", "auth", "security", "dev-a", "milestone-1"]
assignee: "Dev A"
milestone: "Milestone 1: Authentication & RBAC"
dependencies: ["ISSUE-01"]
---

## Summary & Objective
Implement the custom User model and role-based authentication system supporting the 4 platform personas: `CUSTOMER`, `SUPPORT_AGENT`, `MANAGER`, and `ADMINISTRATOR`. Implement secure JWT token issuance and verification endpoints using `djangorestframework-simplejwt`.

## Specifications & Requirements
- User Persona Roles:
  - `CUSTOMER`: Access to own orders, tickets, proactive notifications, and AI support chat.
  - `SUPPORT_AGENT`: Access to ticket queue, AI escalations, and approval queues.
  - `MANAGER`: Full analytics, prediction overview, simulation audit, and team metrics.
  - `ADMINISTRATOR`: Full permissions across policies, knowledge base, and audit logs.
- Authentication Endpoints:
  - `POST /api/auth/register/` (Register customer accounts)
  - `POST /api/auth/login/` (Authenticate credentials, return access + refresh tokens and user profile)
  - `POST /api/auth/refresh/` (Refresh JWT access token)
  - `GET /api/auth/me/` (Retrieve authenticated user identity and role)
- Permissions:
  - Custom DRF permission classes: `IsCustomer`, `IsSupportAgent`, `IsManager`, `IsAdminUser`.

## Input & Output Contracts
`POST /api/auth/login/`
Request:
```json
{
  "email": "customer@example.com",
  "password": "SecurePassword123!"
}
```
Response (HTTP 200):
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "customer@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "CUSTOMER"
  }
}
```

## Acceptance Criteria
- [ ] Custom `User` model extends `AbstractBaseUser` / `PermissionsMixin`.
- [ ] Users can register with valid password hashing (Argon2 / PBKDF2).
- [ ] JWT access and refresh tokens returned on successful login.
- [ ] `GET /api/auth/me/` accurately returns current user profile when bearer token is provided.
- [ ] Permission classes reject unauthorized role access with HTTP 403 Forbidden.
- [ ] Automated tests cover login, registration, token refresh, and role enforcement.
