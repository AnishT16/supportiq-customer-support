# SupportIQ
**AI-Powered Predictive Customer Support & Action Simulation Platform**

A production-oriented AI project combining customer support automation, predictive machine learning, RAG, controlled AI actions, and pre-execution action simulation.

## 1. Project Overview
SupportIQ is an AI-powered customer support platform designed to move customer service from a reactive model to a predictive and decision-aware model. It combines an LLM-based support agent with retrieval-augmented generation, machine-learning prediction, controlled backend tools, policy validation, and an action simulation engine.

The project focuses on two differentiated capabilities: 
- **Predictive Support Intervention**, which estimates whether a customer is likely to raise a support request and what the likely issue may be.
- **AI Action Simulation**, which evaluates the expected impact of a proposed action before the action is executed.

The system is intended as a full-stack portfolio/final-year project demonstrating AI engineering, machine learning, backend development, database design, responsible AI, and automation.

## 2. Problem Statement
Most customer-support systems wait for a customer to report a problem. This creates repetitive work, slower resolution, unnecessary escalations, and limited visibility into emerging operational problems. AI chatbots improve response speed but can still make unsafe or poorly informed decisions when they are allowed to perform actions without sufficient validation.

SupportIQ addresses this by combining current-issue resolution with future-issue prediction and pre-execution simulation.

**Traditional:**
`Customer -> Complaint -> Ticket -> Agent -> Investigation -> Resolution`

**SupportIQ:**
`Business Data -> Prediction -> Customer/Problem -> AI Investigation -> Proposed Action -> Simulation -> Policy Check -> Auto Execute / Human Approval`

## 3. Objectives
- Automate routine customer-support conversations.
- Use RAG to ground responses in company policies and documentation.
- Predict customers likely to contact support and the likely reason.
- Enable proactive customer intervention before a complaint becomes a ticket.
- Simulate proposed AI actions before changing real business state.
- Apply policy and permission controls to AI actions.
- Route high-risk decisions to human support staff.
- Maintain explainable prediction results and complete AI audit logs.
- Provide dashboards for customers, support agents, and managers.

## 4. Core Innovation & USP
The project should not be positioned as simply another AI customer-support chatbot. Its differentiator is the combination of prediction, conversation, simulation, and controlled action.

**Current problem:**
`Customer -> AI Support Agent -> Resolution`

**Future problem:**
`Customer/Business Data -> Prediction -> Proactive Intervention`

**AI action:**
`Customer Request -> AI Decision -> Simulation -> Risk/Policy Check -> Execute or Human Approval`

**Project USP:** SupportIQ attempts to predict the next support problem and evaluate the consequences of an AI action before the action affects the real system.

## 5. Users & Roles
| Role | Main capabilities |
|---|---|
| Customer | Login, view orders, chat with AI, create/view tickets, receive proactive notifications. |
| Support Agent | View tickets, take over AI conversations, review escalations, approve selected actions. |
| Manager | View predictions, support analytics, simulation outcomes, AI performance and high-risk cases. |
| Administrator | Manage users, policies, knowledge documents, AI permissions and audit logs. |

## 6. Functional Features
### 6.1 AI Customer Support Agent
- Understand customer messages using an LLM.
- Detect intent and extract entities such as order ID, issue type and requested action.
- Retrieve customer, order, payment and delivery information through controlled tools.
- Search company knowledge through RAG.
- Create, update and escalate support tickets.
- Provide responses grounded in available business information.

### 6.2 Controlled AI Tools
```python
get_customer()
get_order()
get_delivery_status()
get_payment_status()
get_previous_tickets()
search_knowledge_base()
create_ticket()
update_ticket()
escalate_ticket()
calculate_refund()
request_refund()
send_notification()
```

## 7. Predictive Support Intervention Engine
Instead of waiting for a customer to create a ticket, SupportIQ analyzes customer, order, delivery and historical support data to estimate the probability of a future support request and predict its likely category.

**Example input:**
```yaml
Customer: 9281
Delivery delay: 3 days
Previous complaints: 2
Order value: $4,800
Courier reliability: Low
Warehouse backlog: High
```

**Example output:**
```yaml
Support Contact Probability: 91%
Predicted issue: 
  Delivery complaint: 74%
  Refund request: 18%
  Other: 8%
Recommended intervention: proactive notification
```

The system can then send an appropriate notification, provide a new delivery estimate, offer self-service options, or create a monitoring event.

### 7.1 Prediction Model
A practical first implementation can compare Logistic Regression, Random Forest and XGBoost. The target is whether a customer will raise a support request within a defined future window. A second classifier can predict the likely issue category.
- Target 1: support request within N hours/days — probability output.
- Target 2: likely support issue category — delivery, payment, refund, cancellation, account, product, etc.
- Feature examples: delivery delay, customer complaint history, courier reliability, warehouse backlog, order value, payment status, product category and cancellation history.

### 7.2 Explainability
```yaml
Support risk: 91%
Major contributing factors:
+3 day delivery delay
+2 previous complaints
+High warehouse backlog
+Low courier reliability
```

## 8. AI Action Simulation Engine
The AI does not immediately execute every action. It first creates a proposed action and evaluates its likely effects on customer state, finance, inventory, policies and other represented business state.

**Example:**
Customer: "Cancel my order and refund my money."

Proposed actions:
1. Cancel order
2. Refund $2,499
3. Update inventory
4. Notify customer

The simulation runs against a temporary state rather than the real database.

```yaml
Current state:
Order = ACTIVE
Payment = PAID
Inventory = 1

Simulated state:
Order = CANCELLED
Payment = REFUNDED
Inventory = 2
```

**Example simulation report:**
```yaml
ACTION SIMULATION
Customer impact: Positive
Financial impact: -$2,499
Inventory impact: +1 item
Coupon impact: Coupon becomes invalid
Policy: Eligible
Risk: LOW
Recommendation: AUTO EXECUTE
```

### 8.1 High-Risk Simulation
```yaml
Refund requested: $25,000
Policy: Human approval required
Risk: HIGH
Recommendation: DO NOT AUTO EXECUTE
```

### 8.2 Simulation Design
- Represent the requested operation as an action object.
- Create a temporary state or transaction-like copy of affected entities.
- Apply the action to the temporary state.
- Calculate customer, financial, inventory and policy impact.
- Assign a risk level.
- Return a recommendation without modifying production state.
- Only execute after policy validation and required approval.

## 9. AI Support Agent & RAG
The support agent uses an LLM for language understanding and tool selection. RAG is used to retrieve company-specific information from documents such as refund policies, cancellation policies, shipping rules, warranty guidelines and support procedures.

`Customer Question` -> `Query Processing` -> `Vector Search` -> `Relevant Knowledge` -> `LLM` -> `Grounded Response`

**Suggested knowledge documents:**
- Refund Policy
- Cancellation Policy
- Shipping Policy
- Warranty Policy
- Payment FAQ
- Delivery Guidelines
- Customer Support Guidelines

## 10. Policy, Guardrails & Human Approval
The LLM should not have unrestricted permission to modify the database. Every sensitive action should pass through a policy and permission layer.

`AI` -> `Proposed Action` -> `Simulation` -> `Risk Evaluation` -> `Policy Validation` -> `Auto Execute / Human Approval` -> `Audit Log`

- Low-risk actions can be automated.
- Medium-risk actions can require additional checks.
- High-value refunds and policy exceptions can require human approval.
- Customers cannot access another customer's data.
- Prompt injection cannot override backend policy rules.
- Every significant AI action should be recorded in an audit log.

**Example policy:**
- Refund <= $1,000 -> Automatically allowed
- $1,001–$5,000 -> Manager approval
- \> $5,000 -> Human approval required
- Shipped order -> cancellation restricted
- Multiple refund requests -> escalation
- Flagged account -> manual verification

## 11. System Architecture
```
CUSTOMER
  |
  v
React Frontend
  |
  v
Django REST API
  |
  v
PostgreSQL AI Agent ML Engine
```

**Detailed Modules:**
- RAG Tools Policy Prediction
- Simulation Engine
- Risk Evaluation
- Auto Action / Human Approval
- Audit Logs
- Analytics Dashboard

## 12. Database Design
**Primary entities:**
- User, Customer, Agent
- Product, Order, OrderItem
- Payment, Delivery
- Ticket, TicketMessage, Escalation
- KnowledgeDocument, KnowledgeChunk
- Prediction, PredictionReason
- Simulation, SimulationAction
- Policy, Approval
- AIAction, AuditLog, Notification

**Important relationships:**
- Customer -> Orders, Tickets, Predictions, Notifications
- Order -> Payment, Delivery, OrderItems
- Ticket -> Messages, AI Actions, Escalation
- AI Action -> Simulation

## 13. Technology Stack
| Layer | Technology |
|---|---|
| Frontend | React.js, Vite, Tailwind CSS, Axios, Recharts |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL, pgvector |
| AI | LLM API, embeddings, RAG, tool calling |
| Machine Learning | Scikit-learn, Pandas, NumPy, XGBoost |
| Authentication | JWT / secure session-based authentication |
| Testing | Django tests / Pytest, API tests, AI evaluation |
| Infrastructure | Docker, Git, GitHub |
| Deployment | AWS or another cloud platform |

## 14. Django Project Structure
```text
supportiq/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── accounts/
├── customers/
├── products/
├── orders/
├── payments/
├── deliveries/
├── support/
├── knowledge_base/
├── ai_engine/
├── predictions/
├── simulations/
├── policies/
├── approvals/
├── notifications/
├── analytics/
└── audit/
```

## 15. API Design
| Area | Endpoint | Auth | Description |
|---|---|---|---|
| Authentication | `POST /api/auth/register/` | Public | Register customer account |
| Authentication | `POST /api/auth/login/` | Public | JWT login (returns access, refresh, user) |
| Authentication | `POST /api/auth/refresh/` | Public | Refresh expired JWT access token |
| Authentication | `GET /api/auth/me/` | Bearer Token | Retrieve authenticated user profile |
| Authentication | `PUT / PATCH /api/auth/me/` | Bearer Token | Update permitted profile fields |
| Customers | `GET /api/customers/` | Bearer Token | List customers (own for Customer, all for Agent/Manager/Admin) |
| Customers | `POST /api/customers/` | Bearer Token | Create customer profile |
| Customers | `GET /api/customers/{id}/` | Bearer Token | Retrieve customer profile details |
| Customers | `PUT / PATCH /api/customers/{id}/` | Bearer Token | Update customer profile details |
| Customers | `DELETE /api/customers/{id}/` | Bearer Token | Delete customer (Manager/Admin only) |
| Tickets | `GET /api/tickets/` | Bearer Token | List tickets (filtered by role & query params) |
| Tickets | `POST /api/tickets/` | Bearer Token | Create ticket (own for Customer, any for Staff) |
| Tickets | `GET /api/tickets/{id}/` | Bearer Token | Retrieve ticket details |
| Tickets | `PUT / PATCH /api/tickets/{id}/` | Bearer Token | Update ticket fields according to role permissions |
| Tickets | `DELETE /api/tickets/{id}/` | Bearer Token | Delete ticket (Manager/Admin only) |
| Ticket Workflows | `POST /api/tickets/{id}/assign/` | Bearer Token | Assign ticket to eligible agent (Manager/Admin only) |
| Ticket Workflows | `POST /api/tickets/{id}/status/` | Bearer Token | Update ticket status (Agent/Manager/Admin) |
| Ticket Workflows | `POST /api/tickets/{id}/resolve/` | Bearer Token | Mark ticket as RESOLVED with timestamp |
| Ticket Workflows | `POST /api/tickets/{id}/close/` | Bearer Token | Mark ticket as CLOSED |
| Ticket Workflows | `POST /api/tickets/{id}/reopen/` | Bearer Token | Reopen ticket to OPEN and clear resolved_at |
| Interactive Docs | `GET /api/docs/` | Public | OpenAPI 3 Swagger UI documentation |
| Orders | `GET /api/orders/` \| `GET /api/orders/{id}/` | Bearer Token | Future Phase |
| Support AI Chat | `POST /api/support/chat/` | Bearer Token | Future Phase |
| Prediction | `GET /api/predictions/` \| `POST /api/predictions/run/` | Bearer Token | Future Phase |
| Simulation | `POST /api/simulations/` \| `GET /api/simulations/{id}/` | Bearer Token | Future Phase |
| Approval | `POST /api/simulations/{id}/approve/` \| `reject/` | Bearer Token | Future Phase |

**Ticket Choices:**
- **Category:** `DELIVERY`, `PAYMENT`, `REFUND`, `CANCELLATION`, `ACCOUNT`, `PRODUCT`, `OTHER`
- **Priority:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- **Status:** `OPEN`, `IN_PROGRESS`, `WAITING_FOR_CUSTOMER`, `RESOLVED`, `CLOSED`

**Ticket Query Parameters:**
- `?status=<status>` (e.g. `?status=OPEN`)
- `?priority=<priority>` (e.g. `?priority=HIGH`)
- `?category=<category>` (e.g. `?category=DELIVERY`)
- `?assigned_to=<id|unassigned>` (e.g. `?assigned_to=unassigned`)
- `?customer=<id>` (Staff only)
- `?search=<keyword>` (searches ticket number, subject, description)
- `?ordering=<field>` (e.g. `-created_at`, `priority`, `status`)
- `?page=<number>&page_size=<size>` (default size 10)

**Example Ticket Request (`POST /api/tickets/`):**
```json
{
  "subject": "Delayed shipment for order #9821",
  "description": "Package has been stuck in transit for 4 days past the estimated delivery date.",
  "category": "DELIVERY",
  "priority": "HIGH"
}
```

**Example Ticket Response (`200 OK` / `201 Created`):**
```json
{
  "id": 1,
  "ticket_number": "TIK-20261016-B4E8F2",
  "customer_name": "Alice Customer",
  "customer_email": "alice@example.com",
  "subject": "Delayed shipment for order #9821",
  "description": "Package has been stuck in transit for 4 days past the estimated delivery date.",
  "category": "DELIVERY",
  "priority": "HIGH",
  "status": "OPEN",
  "assigned_to_name": null,
  "assigned_to_username": null,
  "created_at": "2026-10-16T16:08:15.123456Z",
  "updated_at": "2026-10-16T16:08:15.123456Z",
  "resolved_at": null
}
```


**Example Customer Profile Request (`POST /api/customers/`):**
```json
{
  "name": "Jane Customer",
  "email": "jane@example.com",
  "phone": "+1987654321",
  "address": "456 Elm Street, Suite 100"
}
```

**Example Customer Profile Response (`200 OK` / `201 Created`):**
```json
{
  "id": 1,
  "username": "jane_cust",
  "user_role": "CUSTOMER",
  "name": "Jane Customer",
  "email": "jane@example.com",
  "phone": "+1987654321",
  "address": "456 Elm Street, Suite 100",
  "created_at": "2026-10-15T10:24:50.123456Z",
  "updated_at": "2026-10-15T10:24:50.123456Z"
}
```


**Example Prediction Response:**
```json
{
  "customer_id": 9281,
  "support_probability": 0.91,
  "predicted_issue": "delivery_delay",
  "risk_level": "HIGH",
  "reasons": [
    "3 day delivery delay",
    "previous complaints",
    "warehouse backlog"
  ],
  "recommended_intervention": "proactive_notification"
}
```

**Example Simulation Response:**
```json
{
  "action": "refund",
  "order_id": 10291,
  "amount": 2499,
  "policy_status": "eligible",
  "risk_level": "LOW",
  "customer_impact": "positive",
  "financial_impact": -2499,
  "inventory_impact": 1,
  "human_approval_required": false,
  "recommendation": "execute"
}
```

## 16. Dashboard Design
- **Customer Dashboard:** My Orders, My Tickets, AI Support, Notifications, Account
- **Agent Dashboard:** Open Tickets, AI Escalations, Pending Approvals, High-Risk Customers
- **Manager Dashboard:** 
  - Total Tickets: 12,482
  - AI Resolved: 8,721
  - Human Escalated: 2,341
  - Predicted Incidents: 1,204
  - Successful Predictions: 914
  - AI Resolution Rate: 69.8%
- **Prediction dashboard:** Probability and predicted issue by customer.
- **Simulation dashboard:** Total Simulations, Auto Approved, Human Approval, Blocked.

## 17. Security
- Secure authentication and password hashing.
- Role-based authorization.
- API permission checks.
- Input validation and rate limiting.
- CSRF/CORS configuration appropriate to deployment.
- Environment variables for secrets and API keys.
- Audit logging for AI decisions and sensitive actions.
- Backend policy enforcement independent of LLM output.
- Protection against prompt injection and unauthorized tool use.

## 18. Testing & Evaluation
- **Unit tests:** Refund calculations, Policy rules, Risk calculations, Prediction functions, Simulation functions
- **API tests:** Authentication, Authorization, Order APIs, Ticket APIs, Prediction APIs, Simulation APIs
- **AI tests:** Intent classification accuracy, RAG retrieval quality, Prediction accuracy, Action decision accuracy, Escalation accuracy, Prompt injection resistance
- **Recommended metrics:** Precision / Recall / F1, Calibration, RAG retrieval accuracy, AI resolution rate, Escalation accuracy, Simulation correctness.

## 19. Development Roadmap
| Phase | Deliverables |
|---|---|
| 1. Foundation | Django, PostgreSQL, authentication, users, customers, products, orders |
| 2. Support | Tickets, messages, assignment, agent dashboard |
| 3. AI Agent | LLM, intent detection, tool calling, order/ticket lookup |
| 4. RAG | Document upload, chunking, embeddings, pgvector, retrieval |
| 5. Prediction | Dataset, feature engineering, ML model, prediction API, proactive notifications |
| 6. Simulation | Temporary state, impact analysis, risk scoring, policy validation, approvals |
| 7. Dashboard | Customer, agent, manager, prediction and simulation dashboards |
| 8. Security & Testing | Permissions, guardrails, audit logs, unit/API/AI testing |
| 9. Deployment | Docker, production database, frontend/backend deployment, CI/CD |

## 20. Deployment
`GitHub` -> `Docker` -> `Cloud Platform (React Frontend, Django API, PostgreSQL, AI/ML Services)`
For a student portfolio, deployment can start with a simple cloud architecture and later be expanded to AWS services. API keys and database credentials must be stored as environment variables.

## 21. Expected Results
- Routine customer questions can be handled automatically.
- Customers at high risk of raising a support request can be identified proactively.
- The system can predict the likely category of an upcoming support issue.
- AI actions can be simulated before real execution.
- High-risk actions can be routed to human staff.
- Managers can monitor predictions, actions, escalations and AI performance.

## 22. Limitations & Future Scope
**Limitations:**
- Prediction quality depends on the quantity and quality of historical data.
- LLMs can still misunderstand ambiguous requests.
- Simulation is limited to business state and side effects explicitly represented by the system.
- RAG quality depends on the completeness and freshness of the knowledge base.
- A student-scale implementation will not represent every complexity of a production enterprise.

**Future Scope:**
- Multilingual support for English, Hindi and Marathi.
- Voice-based customer support.
- Real-time event processing using streaming infrastructure.
- More advanced sequential/time-series prediction.
- CRM, courier, payment, email and messaging integrations.
- More sophisticated policy and risk models.
- Continuous AI evaluation and monitoring.

## 23. Conclusion
SupportIQ is designed as more than an AI chatbot. It combines an AI support agent with two core intelligence capabilities: predictive support intervention and pre-execution action simulation. The first asks, “What support problem is likely to happen next?” The second asks, “What could happen if the AI takes this action?”

Together with RAG, controlled tools, policy validation, human approval, audit logging, machine learning, and full-stack engineering, these capabilities provide a strong foundation for a practical AI project suitable for a final-year academic project and a fresher software/AI portfolio.

**Project positioning:**
“SupportIQ predicts the next customer-support problem and simulates the consequences of AI actions before they affect the real system.”
