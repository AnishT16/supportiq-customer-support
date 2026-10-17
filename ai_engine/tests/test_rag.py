"""
Unit Tests for SupportIQ RAG Knowledge Base.
Tests document loading, cleaning, chunking, vector indexing, similarity retrieval,
edge cases (empty queries, missing documents), and the AI Agent tool interface.
"""

from pathlib import Path
import sys

# Ensure project root is in sys.path
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from ai_engine.rag.chunker import chunk_markdown
from ai_engine.rag.cleaner import (
    extract_title_and_clean,
    normalize_whitespace,
    strip_markdown_decorations,
)
from ai_engine.rag.config import DEFAULT_KNOWLEDGE_DOCS_DIR
from ai_engine.rag.engine import KnowledgeBase, get_default_knowledge_base
from ai_engine.rag.loader import DocumentLoader, DocumentNotFoundError
from ai_engine.rag.retriever import RAGRetriever
from ai_engine.rag.schemas import DocumentChunk, RAGQueryResult, RetrievalResult
from ai_engine.rag.tool import (
    SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA,
    search_knowledge_base,
    search_knowledge_base_full,
)


# --- 1. Cleaner Tests ---

def test_normalize_whitespace():
    """Test whitespace and newline normalization."""
    raw = "Line 1   \r\n\r\n\r\n  Line 2   with   spaces  "
    cleaned = normalize_whitespace(raw)
    assert "Line 1" in cleaned
    assert "Line 2 with spaces" in cleaned
    assert "\r" not in cleaned


def test_strip_markdown_decorations():
    """Test stripping blockquotes, bolding, code backticks."""
    text = "> **Important**: Use `refund` immediately.\n> Extra line."
    stripped = strip_markdown_decorations(text)
    assert ">" not in stripped
    assert "**" not in stripped
    assert "`" not in stripped
    assert "Important: Use refund immediately." in stripped


def test_extract_title_and_clean():
    """Test title extraction from H1 markdown."""
    doc = "# SupportIQ Return Rules\n\n> Note: Demo\n\n## Section 1\nContent here."
    title, body = extract_title_and_clean(doc)
    assert title == "SupportIQ Return Rules"
    assert "Content here." in body


def test_cleaner_empty_input():
    """Test cleaner on empty or None input."""
    assert normalize_whitespace("") == ""
    assert strip_markdown_decorations("") == ""
    title, body = extract_title_and_clean("")
    assert title == "Untitled Policy"
    assert body == ""


# --- 2. Loader Tests ---

def test_load_default_documents():
    """Test that default knowledge docs directory loads all 5 sample policies."""
    docs = DocumentLoader.load_directory(DEFAULT_KNOWLEDGE_DOCS_DIR)
    assert len(docs) == 5

    filenames = {d[2] for d in docs}
    expected = {
        "refund_policy.md",
        "cancellation_policy.md",
        "shipping_policy.md",
        "warranty_policy.md",
        "payment_faq.md",
    }
    assert expected.issubset(filenames)


def test_load_missing_file_raises_error(tmp_path):
    """Test that loading a non-existent file raises DocumentNotFoundError."""
    non_existent = tmp_path / "does_not_exist.md"
    with pytest.raises(DocumentNotFoundError):
        DocumentLoader.load_file(non_existent)


def test_load_nonexistent_directory():
    """Test that loading a non-existent directory returns an empty list without error."""
    docs = DocumentLoader.load_directory("path/that/does/not/exist")
    assert docs == []


# --- 3. Chunker Tests ---

def test_chunk_markdown_sections():
    """Test that chunker splits markdown by sections and preserves heading metadata."""
    sample_md = """
    # Sample Policy
    
    ## 1. Overview
    This is the overview section text that provides background information.
    
    ## 2. Thresholds
    This is the thresholds section detailing $1,000 auto refunds and limits.
    """
    chunks = chunk_markdown(sample_md, source="sample.md", document_title="Sample Policy")
    assert len(chunks) == 2
    assert chunks[0].section == "1. Overview"
    assert "overview section text" in chunks[0].text
    assert chunks[1].section == "2. Thresholds"
    assert "$1,000" in chunks[1].text


def test_chunker_empty_input():
    """Test chunker handles empty content safely."""
    chunks = chunk_markdown("", source="empty.md")
    assert chunks == []
    chunks_whitespace = chunk_markdown("   \n\n  ", source="empty.md")
    assert chunks_whitespace == []


def test_chunker_subdivides_large_sections():
    """Test that a section exceeding chunk_size is split into sub-chunks."""
    large_body = "word " * 300  # ~1500 chars
    large_md = f"## Long Section\n{large_body}"
    chunks = chunk_markdown(large_md, source="long.md", chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.section == "Long Section"


# --- 4. KnowledgeBase & Retrieval Accuracy Tests ---

@pytest.fixture(scope="module")
def kb():
    """Fixture initializing the KnowledgeBase with default sample policies."""
    return KnowledgeBase()


def test_knowledge_base_initialization(kb):
    """Verify that KnowledgeBase loads documents and builds index."""
    assert kb.total_documents == 5
    assert kb.total_chunks > 10
    catalog = kb.get_document_catalog()
    assert len(catalog) == 5


def test_retrieve_refund_policy(kb):
    """Querying refund rules should return refund_policy.md as top match with high score."""
    result = kb.search("What is the refund window and maximum automatic refund limit?")
    assert result.total_matches > 0
    top = result.results[0]
    assert top.source == "refund_policy.md"
    assert top.score > 0.1
    assert "refund" in top.text.lower()


def test_retrieve_cancellation_policy(kb):
    """Querying cancellation rules should return cancellation_policy.md."""
    result = kb.search("Can I cancel an order that is already shipped or out for delivery?")
    assert result.total_matches > 0
    top = result.results[0]
    assert top.source == "cancellation_policy.md"
    assert top.score > 0.1
    assert "cancellation" in top.text.lower() or "shipped" in top.text.lower()


def test_retrieve_shipping_delays(kb):
    """Querying shipping delay procedures should retrieve shipping_policy.md."""
    result = kb.search("What happens when courier tracking is delayed by 3 business days?")
    assert result.total_matches > 0
    top = result.results[0]
    assert top.source == "shipping_policy.md"
    assert top.score > 0.1
    assert "delay" in top.text.lower() or "shipping" in top.text.lower()


def test_retrieve_warranty_coverage(kb):
    """Querying warranty rules should retrieve warranty_policy.md."""
    result = kb.search("How do I file an RMA claim for warranty repair or replacement?")
    assert result.total_matches > 0
    top = result.results[0]
    assert top.source == "warranty_policy.md"
    assert top.score > 0.1
    assert "rma" in top.text.lower() or "warranty" in top.text.lower()


def test_retrieve_payment_faq(kb):
    """Querying payment methods should retrieve payment_faq.md."""
    result = kb.search("What payment methods are accepted, like Apple Pay or PayPal?")
    assert result.total_matches > 0
    top = result.results[0]
    assert top.source == "payment_faq.md"
    assert top.score > 0.1


# --- 5. Edge Cases & Robustness Tests ---

def test_empty_query_handling(kb):
    """Empty, blank, or None queries should return empty results gracefully without errors."""
    for empty_val in ["", "   ", "\t\n", None]:
        res = kb.search(empty_val)
        assert res.total_matches == 0
        assert res.results == []


def test_empty_knowledge_base():
    """A KnowledgeBase with no documents handles queries gracefully."""
    empty_kb = KnowledgeBase(docs_dir=None, auto_load=False)
    assert empty_kb.total_chunks == 0
    res = empty_kb.search("Any query here")
    assert res.total_matches == 0
    assert res.results == []


def test_source_filtering(kb):
    """Filtering by source returns only passages from that specific document."""
    res = kb.search(
        query="cancellation or refund procedure",
        source_filter="cancellation_policy.md",
    )
    assert res.total_matches > 0
    for match in res.results:
        assert match.source == "cancellation_policy.md"


def test_dynamic_document_addition():
    """Adding a document dynamically updates the index and makes it searchable."""
    custom_kb = KnowledgeBase(auto_load=False)
    custom_doc = """
    # VIP Loyalty Guidelines
    
    ## 1. VIP Tier Perks
    Diamond tier customers receive dedicated concierge support and free returns.
    """
    added_chunks = custom_kb.add_document(custom_doc, source="vip_policy.md", title="VIP Loyalty")
    assert added_chunks > 0

    res = custom_kb.search("What perks do Diamond tier customers receive?")
    assert res.total_matches > 0
    assert res.results[0].source == "vip_policy.md"
    assert "Diamond tier" in res.results[0].text


# --- 6. AI Agent Tool Interface Tests ---

def test_search_knowledge_base_tool():
    """Test the controlled search_knowledge_base tool function returns expected dictionaries."""
    results = search_knowledge_base(query="What is the refund time frame?", top_k=2)
    assert isinstance(results, list)
    assert len(results) <= 2
    if results:
        first = results[0]
        assert "text" in first
        assert "source" in first
        assert "document_title" in first
        assert "section" in first
        assert "score" in first
        assert isinstance(first["score"], float)


def test_search_knowledge_base_full_tool():
    """Test the extended tool interface returning latency and total_matches."""
    res = search_knowledge_base_full(query="shipping methods", top_k=3)
    assert isinstance(res, dict)
    assert "query" in res
    assert "total_matches" in res
    assert "results" in res
    assert "latency_ms" in res
    assert res["latency_ms"] >= 0.0


def test_tool_schema_compliance():
    """Validate OpenAI / Anthropic tool schema definitions."""
    assert SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA["type"] == "function"
    fn = SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA["function"]
    assert fn["name"] == "search_knowledge_base"
    assert "query" in fn["parameters"]["properties"]
    assert "query" in fn["parameters"]["required"]


def test_extract_title_with_leading_newlines():
    """Ensure title extraction works when file has leading blank lines or no H1."""
    doc_leading_nl = "\n\n\n# SupportIQ Shipping Guide\n\nSome text."
    title, body = extract_title_and_clean(doc_leading_nl)
    assert title == "SupportIQ Shipping Guide"
    assert "Some text." in body

    doc_no_h1 = "No heading here\nJust text."
    title_default, body2 = extract_title_and_clean(doc_no_h1, default_title="Fallback Title")
    assert title_default == "Fallback Title"
    assert "No heading here" in body2


def test_demo_disclaimers_filtered_from_chunks(kb):
    """Ensure synthetic demonstration notice banners are not indexed as content chunks."""
    for chunk in kb._all_chunks:
        assert chunk.section is not None, f"Chunk {chunk.chunk_id} has no section (unfiltered preamble)"
        assert "DEMONSTRATION CONTENT ONLY" not in chunk.text


def test_natural_customer_queries(kb):
    """Test realistic conversational queries match the intended policies."""
    # Return query matching refund policy overview
    res_return = kb.search("How long do I have to return an item?")
    assert res_return.total_matches > 0
    assert res_return.results[0].source == "refund_policy.md"
    assert res_return.results[0].section == "1. Overview & Eligibility Window"

    # Cancellation before dispatch
    res_cancel = kb.search("I ordered an hour ago and want to cancel before it ships")
    assert res_cancel.total_matches > 0
    assert res_cancel.results[0].source == "cancellation_policy.md"
    assert res_cancel.results[0].section == "1. Cancellation Cut-Off Window"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

