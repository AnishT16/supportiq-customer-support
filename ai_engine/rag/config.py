"""
Configuration and Defaults for the SupportIQ RAG Knowledge Base.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_KNOWLEDGE_DOCS_DIR = BASE_DIR / "knowledge_docs"

# Chunking Parameters
DEFAULT_CHUNK_SIZE = 500       # Target characters per chunk
DEFAULT_CHUNK_OVERLAP = 75     # Overlap between consecutive chunks
MIN_CHUNK_LENGTH = 30          # Discard trivial or empty chunks

# Retrieval Defaults
DEFAULT_TOP_K = 3              # Number of top relevant passages to return
DEFAULT_SCORE_THRESHOLD = 0.05 # Minimum similarity score cutoff (0.0 to 1.0)
MAX_TOP_K = 10                 # Upper safety limit for retrieval window
