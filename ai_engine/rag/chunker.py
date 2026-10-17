"""
Document Chunking Utilities for RAG Knowledge Base.
Supports Markdown heading-aware chunking and sliding window subdivision.
"""

import re
from pathlib import Path
import sys
from typing import List, Optional

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ai_engine.rag.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    MIN_CHUNK_LENGTH,
)
from ai_engine.rag.schemas import DocumentChunk


def _split_into_windows(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Split long text into overlapping chunks along word or paragraph boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunk = text[start:].strip()
            if len(chunk) >= MIN_CHUNK_LENGTH:
                chunks.append(chunk)
            break

        # Try to find a sentence or newline break near end
        boundary = -1
        for sep in ["\n\n", "\n", ". ", " "]:
            candidate = text.rfind(sep, start, end)
            if candidate != -1 and candidate > start + (chunk_size // 3):
                boundary = candidate + len(sep)
                break

        if boundary == -1:
            boundary = end

        chunk = text[start:boundary].strip()
        if len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)

        # Advance start with overlap
        start = max(boundary - chunk_overlap, start + 1)

    return chunks


def chunk_markdown(
    content: str,
    source: str,
    document_title: str = "Policy Document",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    """
    Chunk markdown document respecting section headings (## Heading).
    Subdivides sections exceeding chunk_size into overlapping windows.
    """
    if not content or not content.strip():
        return []

    # Safe slug for chunk IDs
    doc_slug = re.sub(r"[^a-zA-Z0-9_]+", "_", source.split("/")[-1].split("\\")[-1].replace(".md", "")).lower()

    # Split on markdown headings (H2 or H3: ## or ###, allowing optional leading indentation)
    heading_pattern = re.compile(r"^[ \t]*(#{2,3}\s+.+)$", re.MULTILINE)
    parts = heading_pattern.split(content)

    sections: List[tuple[Optional[str], str]] = []

    # If document starts before first heading
    first_part = parts[0].strip()
    # Strip any top-level H1 header and synthetic demonstration disclaimers from the preamble
    first_part_cleaned = re.sub(r"^#[ \t]+[^\n]+", "", first_part).strip()
    first_part_cleaned = re.sub(
        r"(?i)^(?:>\s*)?(?:\*\*)?DEMONSTRATION CONTENT (?:ONLY|NOTICE)(?:\*\*)?:[^\n]+",
        "",
        first_part_cleaned,
        flags=re.MULTILINE,
    ).strip()
    if first_part_cleaned and len(first_part_cleaned) >= MIN_CHUNK_LENGTH:
        sections.append((None, first_part_cleaned))

    # Pair headings with their corresponding body
    for i in range(1, len(parts), 2):
        raw_heading = parts[i].strip()
        heading_text = re.sub(r"^[ \t]*#{2,3}\s*", "", raw_heading).strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((heading_text, body))

    chunks: List[DocumentChunk] = []
    chunk_idx = 0

    for heading, body in sections:
        if not body:
            continue

        # Prefix section heading to text for retrieval grounding context
        section_prefix = f"[{heading}]\n" if heading else ""
        full_section_text = f"{section_prefix}{body}".strip()

        if len(full_section_text) <= chunk_size:
            chunk_text = full_section_text
            if len(chunk_text) >= MIN_CHUNK_LENGTH:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{doc_slug}_{chunk_idx}",
                        document_title=document_title,
                        source=source,
                        section=heading,
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        metadata={"length": len(chunk_text), "has_heading": heading is not None},
                    )
                )
                chunk_idx += 1
        else:
            # Subdivide section with sliding windows
            sub_texts = _split_into_windows(body, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            for sub_text in sub_texts:
                combined_text = f"{section_prefix}{sub_text}".strip()
                if len(combined_text) >= MIN_CHUNK_LENGTH:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{doc_slug}_{chunk_idx}",
                            document_title=document_title,
                            source=source,
                            section=heading,
                            text=combined_text,
                            chunk_index=chunk_idx,
                            metadata={"length": len(combined_text), "sub_chunk": True},
                        )
                    )
                    chunk_idx += 1

    return chunks
