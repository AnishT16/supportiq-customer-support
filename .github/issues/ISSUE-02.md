---
title: "[Frontend] React 18 + Vite + Tailwind CSS Project Scaffold, Routing & Design System"
labels: ["frontend", "ui/ux", "dev-b", "milestone-0"]
assignee: "Dev B"
milestone: "Milestone 0: Project Foundation"
dependencies: []
---

## Summary & Objective
Initialize the frontend application using React 18, Vite, and Tailwind CSS. Implement the global design system, color palette, responsive application layout shell (Navbar, Sidebar, Page Container), and client-side routing structure using `react-router-dom`.

## Specifications & Requirements
- Tech Stack: React 18, Vite, Tailwind CSS, Lucide React (icons), Axios.
- Design Aesthetic: Modern, high-trust enterprise dashboard aesthetic with dark/light mode foundations, subtle border radiuses, and crisp typography (Inter/Outfit).
- Layout Shell:
  - Top Navigation Bar (User profile dropdown, Notifications bell, Role indicator).
  - Collapsible Sidebar with links grouped by role:
    - Customer: Orders, Tickets, AI Support, Notifications.
    - Agent: Ticket Queue, Approvals Queue, Customer Directory.
    - Manager: Performance Analytics, Prediction Monitor, Simulation Logs.
  - Responsive main content viewport with notification toast container.

## Implementation Steps
1. Scaffold frontend in `frontend/` using Vite (`npm create vite@latest frontend -- --template react`).
2. Install and configure Tailwind CSS (`tailwind.config.js`, `postcss.config.js`).
3. Set up Axios base client (`src/api/client.js`) with request/response interceptors for JWT injection and baseURL handling.
4. Set up `react-router-dom` with placeholder page routes:
   - `/login`, `/register`
   - `/customer/orders`, `/customer/tickets`, `/customer/chat`
   - `/agent/queue`, `/agent/approvals`
   - `/manager/analytics`, `/manager/predictions`, `/manager/simulations`
5. Implement responsive Shell component with Navbar and Sidebar.
6. Verify layout responsiveness across desktop and mobile screen sizes.

## Acceptance Criteria
- [ ] Vite dev server runs cleanly via `npm run dev` on port 5173.
- [ ] Tailwind styles and utility classes render properly.
- [ ] Sidebar navigation toggles active links and renders role-specific link sections.
- [ ] Axios client is pre-configured with `VITE_API_BASE_URL` fallback to `http://localhost:8000`.
