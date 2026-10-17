---
title: "[Backend] Backend Dockerization, docker-compose.yml (Postgres + Redis + Django) & DB Seed Script"
labels: ["backend", "devops", "docker", "dev-a", "milestone-10"]
assignee: "Dev A"
milestone: "Milestone 10: Dockerization & Deployment"
dependencies: ["ISSUE-01", "ISSUE-05", "ISSUE-11", "ISSUE-13", "ISSUE-15"]
---

## Summary & Objective
Implement reproducible local and production containerization for the backend services. Create `Dockerfile` for Django, `docker-compose.yml` orchestrating PostgreSQL (with `pgvector` support), Redis (for caching), and the Django application, plus an automated master seeding script.

## Specifications & Requirements
- `Dockerfile` (Backend):
  - Multi-stage Python 3.11/3.12 slim base image.
  - Install dependencies from `requirements-ai.txt` and project requirements.
  - Install `ai_engine` in editable mode (`pip install -e .`).
  - Configure Gunicorn WSGI server.
- `docker-compose.yml`:
  - Services:
    - `db`: `postgres:15` (or `pgvector/pgvector:pg15`) with persistent named volume.
    - `redis`: `redis:7-alpine` for caching and session state.
    - `backend`: Django service running migrations and Gunicorn.
- Unified Master Seeder:
  - `python manage.py seed_all` command that populates:
    - Demo users for all 4 roles (`customer`, `agent`, `manager`, `admin`).
    - Standard products, sample orders across all statuses (`ACTIVE`, `SHIPPED`, `DELIVERED`).
    - Tickets, knowledge base sync, and simulation test cases.

## Acceptance Criteria
- [ ] `docker compose up --build` spins up `db`, `redis`, and `backend` without errors.
- [ ] Automated healthcheck ensures backend waits until PostgreSQL is ready before applying migrations.
- [ ] `python manage.py seed_all` executes cleanly inside the container.
- [ ] All unit tests pass inside the container environment.
