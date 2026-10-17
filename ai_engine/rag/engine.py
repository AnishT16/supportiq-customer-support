"""
High-Level KnowledgeBase Engine for SupportIQ RAG.
Coordinates document loading, cleaning, chunking, and similarity retrieval.
"""

from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Union
import logging

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ai_engine.rag.chunker import chunk_markdown
from ai_engine.rag.cleaner import extract_title_and_clean
from ai_engine.rag.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_KNOWLEDGE_DOCS_DIR,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_TOP_K,
)
from ai_engine.rag.loader import DocumentLoader, DocumentNotFoundError
from ai_engine.rag.retriever import RAGRetriever
from ai_engine.rag.schemas import DocumentChunk, RAGQueryResult, RetrievalResult

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Core Knowledge Base engine for managing policy documents and executing RAG queries.
    """

    def __init__(
        self,
        docs_dir: Optional[Union[str, Path]] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        min_score: float = DEFAULT_SCORE_THRESHOLD,
        auto_load: bool = True,
    ):
        self.docs_dir = Path(docs_dir) if docs_dir else DEFAULT_KNOWLEDGE_DOCS_DIR
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retriever = RAGRetriever(min_score=min_score)
        self._all_chunks: List[DocumentChunk] = []
        self._indexed_sources: Dict[str, str] = {}  # source -> title

        if auto_load and self.docs_dir.exists():
            self.load_and_index()

    @property
    def total_chunks(self) -> int:
        return len(self._all_chunks)

    @property
    def total_documents(self) -> int:
        return len(self._indexed_sources)

    def load_and_index(self, docs_dir: Optional[Union[str, Path]] = None) -> int:
        """
        Load all markdown policy documents from a directory, chunk, and index them.

        Args:
            docs_dir: Optional path to override knowledge docs directory.

        Returns:
            Total number of indexed chunks.
        """
        target_dir = Path(docs_dir) if docs_dir else self.docs_dir
        raw_docs = DocumentLoader.load_directory(target_dir)

        chunks_to_index: List[DocumentChunk] = []
        self._indexed_sources.clear()

        for content, title, source in raw_docs:
            self._indexed_sources[source] = title
            doc_chunks = chunk_markdown(
                content=content,
                source=source,
                document_title=title,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            chunks_to_index.extend(doc_chunks)

        self._all_chunks = chunks_to_index
        self.retriever.index_chunks(self._all_chunks)
        logger.info(
            f"Indexed {len(self._all_chunks)} chunks from {len(self._indexed_sources)} documents in {target_dir}"
        )
        return len(self._all_chunks)

    def add_document(
        self,
        content: str,
        source: str,
        title: Optional[str] = None,
        rebuild_index: bool = True,
    ) -> int:
        """
        Add a document dynamically to the knowledge base from raw text or markdown.

        Args:
            content: Raw or markdown string.
            source: Source identifier / filename.
            title: Optional title (extracted automatically if not supplied).
            rebuild_index: Whether to immediately update vector index.

        Returns:
            Number of chunks generated for this document.
        """
        if not content or not content.strip():
            return 0

        extracted_title, cleaned_body = extract_title_and_clean(content)
        final_title = title if title else extracted_title

        self._indexed_sources[source] = final_title
        new_chunks = chunk_markdown(
            content=cleaned_body,
            source=source,
            document_title=final_title,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        self._all_chunks.extend(new_chunks)

        if rebuild_index:
            self.retriever.index_chunks(self._all_chunks)

        return len(new_chunks)

    def search(
        self,
        query: Optional[str],
        top_k: int = DEFAULT_TOP_K,
        min_score: Optional[float] = None,
        source_filter: Optional[str] = None,
    ) -> RAGQueryResult:
        """
        Search knowledge base for passages answering the query.

        Args:
            query: Natural language question or search phrase.
            top_k: Maximum number of relevant passages.
            min_score: Optional score threshold cutoff.
            source_filter: Optional filter by source filename.

        Returns:
            RAGQueryResult schema containing matched passages and latency.
        """
        start_time = time.perf_counter()

        if not query or not query.strip():
            return RAGQueryResult(query="", total_matches=0, results=[], latency_ms=0.0)

        results = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            min_score=min_score,
            source_filter=source_filter,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        return RAGQueryResult(
            query=query.strip(),
            total_matches=len(results),
            results=results,
            latency_ms=elapsed_ms,
        )

    def get_document_catalog(self) -> List[Dict[str, Any]]:
        """Return a catalog of loaded knowledge documents."""
        return [
            {"source": source, "title": title}
            for source, title in sorted(self._indexed_sources.items())
        ]


# Singleton default cache
_default_kb_instance: Optional[KnowledgeBase] = None


def get_default_knowledge_base() -> KnowledgeBase:
    """Return a lazily initialized default KnowledgeBase instance."""
    global _default_kb_instance
    if _default_kb_instance is None:
        _default_kb_instance = KnowledgeBase()
    return _default_kb_instance


if __name__ == "__main__":
    print("Testing SupportIQ KnowledgeBase Engine...")
    kb = get_default_knowledge_base()
    print(f"Loaded {kb.total_documents} documents and {kb.total_chunks} chunks.")
    for doc in kb.get_document_catalog():
        print(f"  - {doc['source']}: {doc['title']}")
    
    query = "What is the return window for a refund?"
    print(f"\nExecuting search: '{query}'")
    response = kb.search(query=query, top_k=2)
    print(f"Matched {response.total_matches} passages in {response.latency_ms}ms:")
    for r in response.results:
        print(f"  - [{r.document_title} - {r.section}] (score: {r.score})")
        print(f"    {r.text[:100]}...\n")
    print("KnowledgeBase execution test passed!")
