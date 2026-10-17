---
title: "[Frontend] Frontend Dockerfile, Nginx Reverse Proxy Config & Production Build Setup"
labels: ["frontend", "devops", "docker", "nginx", "dev-b", "milestone-10"]
assignee: "Dev B"
milestone: "Milestone 10: Dockerization & Deployment"
dependencies: ["ISSUE-02", "ISSUE-04", "ISSUE-06", "ISSUE-18"]
---

## Summary & Objective
Implement containerization for the React frontend application. Build a multi-stage `Dockerfile` with Node.js build stage and a lightweight Nginx alpine image serving static assets and proxying `/api/` requests to the backend container.

## Specifications & Requirements
- Multi-Stage `Dockerfile`:
  - Stage 1 (Build): `node:18-alpine` or `node:20-alpine`, run `npm install` and `npm run build`.
  - Stage 2 (Serve): `nginx:alpine`, copy built artifacts from `dist/` to `/usr/share/nginx/html`.
- `nginx.conf`:
  - SPA routing fallback: `try_files $uri $uri/ /index.html;` to ensure client-side routing functions on page refresh.
  - Proxy configuration: Proxy `/api/` traffic to `http://backend:8000/`.
  - Gzip compression enabled for JS, CSS, and SVG assets.
- Integrate `frontend` service into root `docker-compose.yml`.

## Acceptance Criteria
- [ ] `npm run build` generates optimized bundle without TypeScript/lint errors.
- [ ] Docker image builds and runs on port 80/3000.
- [ ] Page refreshes on deep routes (e.g. `/customer/orders/1001`) resolve properly without Nginx 404s.
- [ ] API calls from frontend container are proxied smoothly to backend container.
