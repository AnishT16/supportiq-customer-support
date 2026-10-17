"""
SupportIQ RAG Knowledge Base Package.
Provides local policy document retrieval, semantic chunking, and AI agent search tools.
"""

from pathlib import Path
import sys

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from ai_engine.rag.chunker import chunk_markdown
    from ai_engine.rag.cleaner import extract_title_and_clean, normalize_whitespace
    from ai_engine.rag.engine import KnowledgeBase, get_default_knowledge_base
    from ai_engine.rag.loader import DocumentLoader, DocumentNotFoundError
    from ai_engine.rag.retriever import RAGRetriever
    from ai_engine.rag.schemas import (
        DocumentChunk,
        DocumentMetadata,
        RAGQueryResult,
        RetrievalResult,
    )
    from ai_engine.rag.tool import (
        SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA,
        search_knowledge_base,
        search_knowledge_base_full,
    )
except ImportError:
    from .chunker import chunk_markdown
    from .cleaner import extract_title_and_clean, normalize_whitespace
    from .engine import KnowledgeBase, get_default_knowledge_base
    from .loader import DocumentLoader, DocumentNotFoundError
    from .retriever import RAGRetriever
    from .schemas import (
        DocumentChunk,
        DocumentMetadata,
        RAGQueryResult,
        RetrievalResult,
    )
    from .tool import (
        SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA,
        search_knowledge_base,
        search_knowledge_base_full,
    )

__all__ = [
    "KnowledgeBase",
    "get_default_knowledge_base",
    "RAGRetriever",
    "search_knowledge_base",
    "search_knowledge_base_full",
    "SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA",
    "DocumentChunk",
    "DocumentMetadata",
    "RetrievalResult",
    "RAGQueryResult",
    "DocumentLoader",
    "DocumentNotFoundError",
    "chunk_markdown",
    "extract_title_and_clean",
    "normalize_whitespace",
]
