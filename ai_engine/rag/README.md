# SupportIQ RAG Knowledge Base

A lightweight, production-grade local Retrieval-Augmented Generation (RAG) module for SupportIQ.
This module retrieves grounded company policy passages, return/cancellation rules, shipping guidelines, warranty terms, and payment FAQs to inform customer support responses.

> **DEMONSTRATION CONTENT NOTICE**: All policies included in `knowledge_docs/` are synthetic sample policies intended exclusively for SupportIQ testing and demonstration. They do not constitute actual legal policies or real customer data.

---

## 1. Architecture Overview

```
Customer Support Query ("Can I get a refund for a $2000 item?")
                  |
                  v
       +-----------------------+
       |   Cleaner & Normalizer|
       +-----------------------+
                  |
                  v
       +-----------------------+
       | TF-IDF N-Gram Vector  | (Sublinear TF, Unigrams + Bigrams, L2 Norm)
       +-----------------------+
                  |
                  v
       +-----------------------+
       | Cosine Sim Calculation| (Evaluated against Sparse Chunk Matrix)
       +-----------------------+
                  |
                  v
       +-----------------------+
       | Top-K Ranked Passages | (Returns Text, Source, Section, Similarity Score)
       +-----------------------+
                  |
                  v
       Future AI Support Agent / LLM Controller
```

### Key Design Principles:
1. **Local & Zero-Infrastructure**: Operates entirely in-memory using `scikit-learn` TF-IDF and Cosine Similarity. No external vector databases, Docker containers, heavy embedding downloads, or network calls required.
2. **Deterministic & Fast**: Query latencies are sub-millisecond (< 1ms).
3. **Pydantic Contract Enforcement**: Strong types and serialization via `DocumentChunk`, `RetrievalResult`, and `RAGQueryResult`.
4. **Standard Agent Tool Interface**: Exposes `search_knowledge_base()` and an OpenAI/Anthropic-compliant function-calling schema.

---

## 2. Included Demonstration Policy Documents

The `knowledge_docs/` directory includes five synthetic policy documents:
- `refund_policy.md`: Refund eligibility windows, tiered approval limits (Auto <= $1,000, Manager $1,001–$5,000, Executive > $5,000), previous refund limits, processing times.
- `cancellation_policy.md`: Immediate cancellation for `ACTIVE`/`PAID`/`PROCESSING` orders; restrictions on `SHIPPED`/`DELIVERED` orders; partial order cancellations.
- `shipping_policy.md`: Shipping tiers (Standard, Expedited, Overnight), carrier tracking updates, 3-day delay proactive notification rules, lost package handling.
- `warranty_policy.md`: 1-year limited manufacturer warranty coverage, exclusions (accidental damage/water), RMA claim procedure, SupportIQ Care+ plans.
- `payment_faq.md`: Accepted payment methods, billing charges, coupon refund adjustments, failed payment troubleshooting, chargeback dispute prevention.

---

## 3. How to Add New Policy Documents

Adding new policy documents to the knowledge base is straightforward:

### Method A: Adding via Markdown Files (Recommended)

1. Create a new `.md` file inside `ai_engine/rag/knowledge_docs/` (for example, `delivery_guidelines.md`).
2. Add a top-level heading (`# Title`) and a demonstration disclaimer banner:
   ```markdown
   # SupportIQ Delivery Guidelines

   > **DEMONSTRATION CONTENT ONLY**: Synthetic policy for demonstration.

   ## 1. Signature Requirements
   Orders exceeding $500 require a direct adult signature upon delivery.

   ## 2. Delivery Attempts
   Carriers will make three delivery attempts before returning the package to the depot.
   ```
3. Use `## ` headings to designate sections. The chunker automatically uses these headings for semantic chunk boundaries and tags them in retrieval results.
4. The document will be loaded and indexed automatically the next time `KnowledgeBase()` or `search_knowledge_base()` is invoked.

### Method B: Adding Dynamically in Code

You can also dynamically register documents in memory at runtime without creating files:

```python
from ai_engine.rag import KnowledgeBase

kb = KnowledgeBase()
kb.add_document(
    content="""
    # Return Logistics Guide
    ## 1. Drop-off Locations
    Customers can drop off returns at any authorized carrier drop-off kiosk.
    """,
    source="return_logistics.md",
    title="Return Logistics Guide",
)
```

---

## 4. AI Agent Interface & Controlled Tool Calling

Future AI support agents (and LLMs with tool-use capability) can search the knowledge base using the standardized interface:

### Python Function Call
```python
from ai_engine.rag import search_knowledge_base

results = search_knowledge_base(
    query="How long do I have to return an item?",
    top_k=3,
    min_score=0.05
)

for item in results:
    print(f"[{item['document_title']}] ({item['score']}) -> {item['text']}")
```

### Return Format
```json
[
  {
    "text": "[1. Overview & Eligibility Window]\nSupportIQ customers are eligible to request a refund for eligible products within 30 calendar days of the delivery date...",
    "source": "refund_policy.md",
    "document_title": "SupportIQ Customer Refund Policy",
    "section": "1. Overview & Eligibility Window",
    "score": 0.3842,
    "chunk_id": "refund_policy_0",
    "metadata": {
      "length": 252,
      "has_heading": true
    }
  }
]
```

### Tool Declaration Schema (OpenAI / Anthropic Function Calling)
The tool declaration schema is accessible via:
```python
from ai_engine.rag import SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA
```
This schema can be directly passed into an LLM's `tools` array for automated tool routing.

---

## 5. Dependencies

This module relies on the standard AI engine requirements already specified in `requirements-ai.txt`:
- `scikit-learn>=1.3.0` (for `TfidfVectorizer` and `cosine_similarity`)
- `numpy>=1.24.0` (for vector math and array sorting)
- `pydantic>=2.5.0` (for strict data validation and serialization)
- `pytest>=7.4.0` (for unit testing)

**No external vector database or API keys are required.**
