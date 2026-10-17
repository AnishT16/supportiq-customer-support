# SupportIQ — Master Project Task Breakdown & Issue Tracker

> **Project Objective**: End-to-end full-stack implementation of SupportIQ (AI-Powered Predictive Customer Support & Action Simulation Platform) based on `README.md` and the policy specifications in `ai_engine/rag/knowledge_docs/`.

---

## 1. Division of Responsibilities

The full project is divided into **24 atomic, low-dependency tasks** distributed between two core collaborators:

| Developer | Primary Focus | Core Deliverables | Task Count |
|---|---|---|:---:|
| **Dev A** | **Backend & AI Architecture** | Django REST Framework, PostgreSQL schema, JWT RBAC, AI Engine integration, Predictive ML inference, Action Simulation engine, Security & Dockerization | **12 Tasks** |
| **Dev B** | **Frontend UI & Full-Stack Integration** | React 18 + Vite, Tailwind CSS design system, Customer Portal, Agent Workspace, Manager Analytics, AI Support Chat widget, Approval queues, Nginx build | **11 Tasks** |
| **Dev A & Dev B** | **Joint QA & Validation** | End-to-end user journey smoke tests, integration validation across all 5 core demonstration flows | **1 Task** |

---

## 2. Low-Dependency Parallel Execution Strategy

To ensure **minimum dependency** between Dev A and Dev B, each frontend task is paired with an explicit **Mock Contract & Data Schema** defined in its issue. 

- **Independent Frontend Velocity**: Dev B can build and test complete UI components, dashboards, and modal workflows using mock data immediately without waiting for database migrations or model training to finish.
- **Contract-First APIs**: Dev A builds endpoints directly matching the pre-agreed JSON schemas, allowing plug-and-play integration as soon as endpoints go live.

```
WEEK 1: Foundation & Core Entities
  [Dev A] ISSUE-01 (Django Setup)      --> ISSUE-03 (JWT Auth)       --> ISSUE-05 (Orders/DB Models)
  [Dev B] ISSUE-02 (Vite + Tailwind)   --> ISSUE-04 (Auth UI/Guards) --> ISSUE-06 (Customer Portal UI)

WEEK 2: Ticketing, RAG & AI Agent
  [Dev A] ISSUE-07 (Ticket REST API)   --> ISSUE-09 (RAG Service)    --> ISSUE-11 (AI Agent Controller)
  [Dev B] ISSUE-08 (Ticket Views UI)   --> ISSUE-10 (Policy UI)      --> ISSUE-12 (AI Chat Drawer)

WEEK 3: Predictive Intervention & Action Simulation
  [Dev A] ISSUE-13 (Predictive API)    --> ISSUE-15 (Simulation API) --> ISSUE-17 (Analytics APIs)
  [Dev B] ISSUE-14 (Proactive Banner)  --> ISSUE-16 (Approval Queue) --> ISSUE-18/19 (Dashboards)

WEEK 4: Hardening, Docker & Delivery
  [Dev A] ISSUE-20 (Security/Audit)    --> ISSUE-22 (Backend Docker)
  [Dev B] ISSUE-21 (Audit Log UI)      --> ISSUE-23 (Frontend Docker)
  [Joint] ISSUE-24 (End-to-End System Walkthrough & Integration Tests)
```

---

## 3. Master Issue Matrix

| Issue ID | GitHub URL | Title | Assignee | Milestone | Dependencies | Local Spec |
|---|---|---|---|---|---|---|
| **ISSUE-01** | [#3](https://github.com/AnishT16/supportiq-customer-support/issues/3) | Django Project Structure, Settings, and PostgreSQL Foundation | **Dev A** | M0: Foundation | None | [.github/issues/ISSUE-01.md](file:///.github/issues/ISSUE-01.md) |
| **ISSUE-02** | [#4](https://github.com/AnishT16/supportiq-customer-support/issues/4) | React 18 + Vite + Tailwind CSS Project Scaffold & Design System | **Dev B** | M0: Foundation | None | [.github/issues/ISSUE-02.md](file:///.github/issues/ISSUE-02.md) |
| **ISSUE-03** | [#5](https://github.com/AnishT16/supportiq-customer-support/issues/5) | Custom User Model, JWT Authentication, and RBAC Permissions | **Dev A** | M1: Auth & RBAC | ISSUE-01 | [.github/issues/ISSUE-03.md](file:///.github/issues/ISSUE-03.md) |
| **ISSUE-04** | [#6](https://github.com/AnishT16/supportiq-customer-support/issues/6) | Auth UI & State Management (Login, Register & Route Guards) | **Dev B** | M1: Auth & RBAC | ISSUE-02 | [.github/issues/ISSUE-04.md](file:///.github/issues/ISSUE-04.md) |
| **ISSUE-05** | [#7](https://github.com/AnishT16/supportiq-customer-support/issues/7) | Customer, Product, Order, Payment & Delivery Models & APIs | **Dev A** | M2: E-Commerce | ISSUE-01, ISSUE-03 | [.github/issues/ISSUE-05.md](file:///.github/issues/ISSUE-05.md) |
| **ISSUE-06** | [#8](https://github.com/AnishT16/supportiq-customer-support/issues/8) | Customer Portal UI (Order List, Details & Live Delivery Tracker) | **Dev B** | M2: E-Commerce | ISSUE-02, ISSUE-04 | [.github/issues/ISSUE-06.md](file:///.github/issues/ISSUE-06.md) |
| **ISSUE-07** | [#9](https://github.com/AnishT16/supportiq-customer-support/issues/9) | Support Ticket Lifecycle, Messages & Escalation REST APIs | **Dev A** | M3: Ticketing | ISSUE-03, ISSUE-05 | [.github/issues/ISSUE-07.md](file:///.github/issues/ISSUE-07.md) |
| **ISSUE-08** | [#10](https://github.com/AnishT16/supportiq-customer-support/issues/10) | Support Ticketing UI (Customer Ticket List & Message Thread) | **Dev B** | M3: Ticketing | ISSUE-04, ISSUE-06 | [.github/issues/ISSUE-08.md](file:///.github/issues/ISSUE-08.md) |
| **ISSUE-09** | [#11](https://github.com/AnishT16/supportiq-customer-support/issues/11) | Integrate RAG Engine with Django Services & Knowledge Base API | **Dev A** | M4: RAG Engine | ISSUE-01, ISSUE-03 | [.github/issues/ISSUE-09.md](file:///.github/issues/ISSUE-09.md) |
| **ISSUE-10** | [#12](https://github.com/AnishT16/supportiq-customer-support/issues/12) | Knowledge Base Policy Explorer & Live Search UI | **Dev B** | M4: RAG Engine | ISSUE-02, ISSUE-04 | [.github/issues/ISSUE-10.md](file:///.github/issues/ISSUE-10.md) |
| **ISSUE-11** | [#13](https://github.com/AnishT16/supportiq-customer-support/issues/13) | AI Agent Controller, LLM Tool Calling Engine & Audit Logger | **Dev A** | M5: AI Agent | ISSUE-05, ISSUE-07, ISSUE-09 | [.github/issues/ISSUE-11.md](file:///.github/issues/ISSUE-11.md) |
| **ISSUE-12** | [#14](https://github.com/AnishT16/supportiq-customer-support/issues/14) | Interactive AI Chat Drawer & Real-Time Tool Calling Visualizer | **Dev B** | M5: AI Agent | ISSUE-02, ISSUE-04, ISSUE-06 | [.github/issues/ISSUE-12.md](file:///.github/issues/ISSUE-12.md) |
| **ISSUE-13** | [#15](https://github.com/AnishT16/supportiq-customer-support/issues/15) | Predictive ML Inference API, Risk Classification & Alerts | **Dev A** | M6: Prediction | ISSUE-05, ISSUE-07 | [.github/issues/ISSUE-13.md](file:///.github/issues/ISSUE-13.md) |
| **ISSUE-14** | [#16](https://github.com/AnishT16/supportiq-customer-support/issues/16) | Proactive Customer Notification Banner & Intervention Modal | **Dev B** | M6: Prediction | ISSUE-04, ISSUE-06 | [.github/issues/ISSUE-14.md](file:///.github/issues/ISSUE-14.md) |
| **ISSUE-15** | [#17](https://github.com/AnishT16/supportiq-customer-support/issues/17) | Action Simulation Service, Policy Verification & Approval APIs | **Dev A** | M7: Simulation | ISSUE-05, ISSUE-07 | [.github/issues/ISSUE-15.md](file:///.github/issues/ISSUE-15.md) |
| **ISSUE-16** | [#18](https://github.com/AnishT16/supportiq-customer-support/issues/18) | Simulation Impact Visualizer & Agent Approval Queue Dashboard | **Dev B** | M7: Simulation | ISSUE-04, ISSUE-06 | [.github/issues/ISSUE-16.md](file:///.github/issues/ISSUE-16.md) |
| **ISSUE-17** | [#19](https://github.com/AnishT16/supportiq-customer-support/issues/19) | Analytics & Aggregation APIs for Support, Predictions & Simulations | **Dev A** | M8: Analytics | ISSUE-05, ISSUE-07, ISSUE-13, ISSUE-15 | [.github/issues/ISSUE-17.md](file:///.github/issues/ISSUE-17.md) |
| **ISSUE-18** | [#20](https://github.com/AnishT16/supportiq-customer-support/issues/20) | Manager Analytics Dashboard (KPI Cards & Recharts Trends) | **Dev B** | M8: Analytics | ISSUE-02, ISSUE-04 | [.github/issues/ISSUE-18.md](file:///.github/issues/ISSUE-18.md) |
| **ISSUE-19** | [#21](https://github.com/AnishT16/supportiq-customer-support/issues/21) | Support Agent Workspace Dashboard (Queue, Escalations & 360 View) | **Dev B** | M8: Analytics | ISSUE-04, ISSUE-08, ISSUE-16 | [.github/issues/ISSUE-19.md](file:///.github/issues/ISSUE-19.md) |
| **ISSUE-20** | [#22](https://github.com/AnishT16/supportiq-customer-support/issues/22) | API Security Hardening, Prompt Injection Guardrails & Audit Logs | **Dev A** | M9: Security | ISSUE-03, ISSUE-11, ISSUE-15 | [.github/issues/ISSUE-20.md](file:///.github/issues/ISSUE-20.md) |
| **ISSUE-21** | [#23](https://github.com/AnishT16/supportiq-customer-support/issues/23) | System Audit Log Explorer & Security Activity UI | **Dev B** | M9: Security | ISSUE-04, ISSUE-18 | [.github/issues/ISSUE-21.md](file:///.github/issues/ISSUE-21.md) |
| **ISSUE-22** | [#24](https://github.com/AnishT16/supportiq-customer-support/issues/24) | Backend Dockerization, docker-compose.yml & DB Seed Script | **Dev A** | M10: Deployment | ISSUE-01, ISSUE-05, ISSUE-11, ISSUE-13, ISSUE-15 | [.github/issues/ISSUE-22.md](file:///.github/issues/ISSUE-22.md) |
| **ISSUE-23** | [#25](https://github.com/AnishT16/supportiq-customer-support/issues/25) | Frontend Dockerfile, Nginx Reverse Proxy Config & Build Pipeline | **Dev B** | M10: Deployment | ISSUE-02, ISSUE-04, ISSUE-06, ISSUE-18 | [.github/issues/ISSUE-23.md](file:///.github/issues/ISSUE-23.md) |
| **ISSUE-24** | [#26](https://github.com/AnishT16/supportiq-customer-support/issues/26) | End-to-End Integration, Smoke Tests & Walkthrough Validation | **Dev A & B** | M10: Deployment | ISSUE-22, ISSUE-23 | [.github/issues/ISSUE-24.md](file:///.github/issues/ISSUE-24.md) |


---

## 4. How to Publish These Issues to GitHub

When you or your team are ready to publish these issues to the GitHub repository:

1. Authenticate with GitHub CLI in your terminal:
   ```powershell
   gh auth login
   ```
2. Run the automated synchronization script:
   - **PowerShell (Windows)**:
     ```powershell
     .\scripts\push_issues_to_github.ps1
     ```
   - **Bash (Linux / macOS)**:
     ```bash
     chmod +x ./scripts/push_issues_to_github.sh
     ./scripts/push_issues_to_github.sh
     ```
3. The script will read all markdown files in `.github/issues/`, extract their titles, labels, assignees, and specifications, and create live GitHub issues on `AnishT16/supportiq-customer-support`.
