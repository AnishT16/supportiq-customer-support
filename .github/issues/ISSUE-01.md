---
title: "[Backend] Django Project Structure, Settings, and PostgreSQL Foundation"
labels: ["backend", "database", "dev-a", "milestone-0"]
assignee: "Dev A"
milestone: "Milestone 0: Project Foundation"
dependencies: []
---

## Summary & Objective
Set up the core Django backend project based on Section 14 of the specification. Configure standard application settings, PostgreSQL database connection, environment variable management via `python-dotenv`, and register core modular app stubs.

## Specifications & Requirements
- Target Django framework structure:
  - Root: `supportiq/`
  - Apps: `accounts/`, `customers/`, `products/`, `orders/`, `payments/`, `deliveries/`, `support/`, `knowledge_base/`, `predictions/`, `simulations/`, `policies/`, `approvals/`, `notifications/`, `analytics/`, `audit/`
- PostgreSQL configuration with environment variable fallbacks (host, port, user, password, db name).
- Django REST Framework (DRF) configuration with JSON renderer and parser.
- CORS configuration (`django-cors-headers`) to permit development origins (`http://localhost:5173` for Vite).
- Re-use existing `ai_engine` package as an installed/imported module.

## Implementation Steps
1. Create Django project config in `config/` with `settings.py`, `urls.py`, `wsgi.py`, and `asgi.py`.
2. Configure `.env` integration using `python-dotenv` for database credentials and secret key.
3. Configure `DATABASES` setting for PostgreSQL (with SQLite fallback for lightweight testing).
4. Configure `INSTALLED_APPS`, `MIDDLEWARE`, `REST_FRAMEWORK`, and `CORS_ALLOWED_ORIGINS`.
5. Create base health check endpoint `GET /api/health/` returning system status.
6. Write unit test for the health check and database connectivity.

## Contract / Response Schema
`GET /api/health/`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected"
}
```

## Acceptance Criteria
- [ ] Django starts cleanly via `python manage.py runserver`.
- [ ] `GET /api/health/` returns HTTP 200 with `{ "status": "healthy" }`.
- [ ] CORS is configured and accepts requests from Vite dev server.
- [ ] Database migrations execute without errors against PostgreSQL/SQLite.
