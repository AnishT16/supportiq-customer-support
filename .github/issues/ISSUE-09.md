---
title: "[Backend] Integrate RAG Engine with Django Services & Knowledge Base Search API"
labels: ["backend", "ai-engine", "rag", "dev-a", "milestone-4"]
assignee: "Dev A"
milestone: "Milestone 4: RAG & Knowledge Base"
dependencies: ["ISSUE-01", "ISSUE-03"]
---

## Summary & Objective
Integrate the existing `ai_engine.rag` module (`KnowledgeBase`, `RAGRetriever`, document loader) into the Django application lifecycle (`knowledge_base/` app). Expose search endpoints for both customer self-service exploration and internal agent tool calling.

## Specifications & Requirements
- App: `knowledge_base/`
- Service Wrapper: Lazy-load and cache singleton `KnowledgeBase` instance loading policies from `ai_engine/rag/knowledge_docs/` (`refund_policy.md`, `cancellation_policy.md`, `shipping_policy.md`, `payment_faq.md`, `warranty_policy.md`).
- Endpoints:
  - `GET /api/knowledge-base/documents/` (Catalog of loaded policy documents and metadata)
  - `POST /api/knowledge-base/search/` (Semantic/similarity query search returning matched passages, scores, and sources)
  - `GET /api/knowledge-base/documents/{source}/` (Retrieve clean markdown content of a specific policy)

## Input & Output Contracts
`POST /api/knowledge-base/search/`
Request:
```json
{
  "query": "Can I cancel an order that has already shipped?",
  "top_k": 3,
  "min_score": 0.05
}
```
Response (HTTP 200):
```json
{
  "query": "Can I cancel an order that has already shipped?",
  "total_matches": 1,
  "latency_ms": 1.25,
  "results": [
    {
      "source": "cancellation_policy.md",
      "document_title": "SupportIQ Order Cancellation Policy",
      "section": "2. Ineligible & Restricted Cancellation Statuses",
      "score": 0.324,
      "text": "If an order status is marked as SHIPPED, OUT_FOR_DELIVERY, or DELIVERED, direct cancellation is restricted..."
    }
  ]
}
```

## Acceptance Criteria
- [ ] Django service initializes `KnowledgeBase` smoothly on first call.
- [ ] Policy catalog endpoint returns all 5 demonstration policy documents.
- [ ] Search endpoint returns ranked results with sub-10ms response times.
- [ ] Test cases verify accurate retrieval across refund, cancellation, shipping, and warranty queries.
