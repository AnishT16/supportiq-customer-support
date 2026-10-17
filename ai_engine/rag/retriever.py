"""
Similarity-Based Retrieval Engine for SupportIQ RAG.
Provides local, zero-infrastructure TF-IDF vector indexing and cosine similarity retrieval.
"""

from typing import Any, Dict, List, Optional
import time
from pathlib import Path
import sys

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ai_engine.rag.config import (
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_TOP_K,
    MAX_TOP_K,
)
from ai_engine.rag.schemas import DocumentChunk, RetrievalResult


class RAGRetriever:
    """
    Local vector retrieval engine using TF-IDF and Cosine Similarity.
    Requires no external model downloads, API keys, or database services.
    """

    def __init__(self, ngram_range: tuple = (1, 2), min_score: float = DEFAULT_SCORE_THRESHOLD):
        self.ngram_range = ngram_range
        self.min_score = min_score
        self.vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            stop_words="english",
            sublinear_tf=True,
            strip_accents="unicode",
            norm="l2",
        )
        self.chunks: List[DocumentChunk] = []
        self._tfidf_matrix = None
        self._is_indexed = False

    @property
    def is_indexed(self) -> bool:
        """Return True if index contains fitted chunks."""
        return self._is_indexed and len(self.chunks) > 0

    @property
    def total_chunks(self) -> int:
        """Return total number of indexed chunks."""
        return len(self.chunks)

    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Fit vectorizer and build similarity matrix over document chunks.
        Returns:
            Number of indexed chunks.
        """
        if not chunks:
            self.chunks = []
            self._tfidf_matrix = None
            self._is_indexed = False
            return 0

        self.chunks = list(chunks)
        corpus = [chunk.text for chunk in self.chunks]
        self._tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self._is_indexed = True
        return len(self.chunks)

    def retrieve(
        self,
        query: Optional[str],
        top_k: int = DEFAULT_TOP_K,
        min_score: Optional[float] = None,
        source_filter: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant passages for a given natural language query.

        Args:
            query: User search query or customer question.
            top_k: Maximum number of passages to return.
            min_score: Minimum similarity cutoff (overrides default).
            source_filter: Optional filter by document source filename.

        Returns:
            List of RetrievalResult objects sorted by similarity score descending.
        """
        # Validate query: handle empty, whitespace, or None gracefully
        if not query or not query.strip():
            return []

        # Return empty if knowledge base has no indexed chunks
        if not self.is_indexed or self._tfidf_matrix is None:
            return []

        clean_query = query.strip()
        score_cutoff = self.min_score if min_score is None else min_score
        k = max(1, min(top_k, MAX_TOP_K))

        # Vectorize query
        query_vector = self.vectorizer.transform([clean_query])

        # Compute cosine similarity
        similarities = cosine_similarity(query_vector, self._tfidf_matrix).flatten()

        # If all scores are zero (no vocabulary overlap)
        if np.all(similarities <= 0.0):
            return []

        # Rank indices by descending similarity
        ranked_indices = np.argsort(similarities)[::-1]

        results: List[RetrievalResult] = []
        for idx in ranked_indices:
            score = float(similarities[idx])
            if score < score_cutoff:
                break

            chunk = self.chunks[idx]

            # Optional source filtering
            if source_filter and chunk.source.lower() != source_filter.lower():
                continue

            results.append(
                RetrievalResult(
                    text=chunk.text,
                    source=chunk.source,
                    document_title=chunk.document_title,
                    section=chunk.section,
                    score=round(score, 4),
                    chunk_id=chunk.chunk_id,
                    metadata=chunk.metadata,
                )
            )

            if len(results) >= k:
                break

        return results


if __name__ == "__main__":
    print("Testing RAGRetriever...")
    retriever = RAGRetriever()
    test_chunks = [
        DocumentChunk(
            chunk_id="test_1",
            document_title="Return Policy",
            source="returns.md",
            section="Overview",
            text="Customers can request a refund within 30 days of receiving the item.",
        ),
        DocumentChunk(
            chunk_id="test_2",
            document_title="Shipping Policy",
            source="shipping.md",
            section="Expedited",
            text="Overnight shipping arrives next business day before 3 PM.",
        ),
    ]
    retriever.index_chunks(test_chunks)
    print(f"Indexed {retriever.total_chunks} chunks successfully.")
    res = retriever.retrieve("How many days for refund?", top_k=1)
    if res:
        print(f"Sample retrieval match: '{res[0].text}' (score: {res[0].score})")
    print("RAGRetriever execution test passed!")
