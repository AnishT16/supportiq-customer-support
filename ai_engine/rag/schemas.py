"""
Data Schemas and Contracts for the SupportIQ RAG Knowledge Base.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata describing a policy or knowledge document."""
    source: str
    title: str
    total_characters: int = 0
    total_chunks: int = 0
    is_demonstration: bool = True
    extra: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """Represents an individual text chunk from a knowledge document."""
    chunk_id: str
    document_title: str
    source: str
    section: Optional[str] = None
    text: str
    chunk_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class RetrievalResult(BaseModel):
    """
    Result schema for an individual retrieved passage.
    Returns passage text, document source, section, and similarity score.
    """
    text: str
    source: str
    document_title: str
    section: Optional[str] = None
    score: float = 0.0
    chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return self.model_dump()


class RAGQueryResult(BaseModel):
    """Container for complete query results from the Knowledge Base."""
    query: str
    total_matches: int = 0
    results: List[RetrievalResult] = Field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return self.model_dump()
