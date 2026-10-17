"""
Controlled AI Agent Tool Interface for SupportIQ RAG.
Provides the standard `search_knowledge_base` tool function and LLM tool calling schema.
Compatible with Section 6.2 & Section 9 of README.md.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ai_engine.rag.config import DEFAULT_SCORE_THRESHOLD, DEFAULT_TOP_K
from ai_engine.rag.engine import get_default_knowledge_base


def search_knowledge_base(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_SCORE_THRESHOLD,
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Controlled tool function for AI Support Agents to search company policies and FAQs.

    Args:
        query: Customer question or policy query to search for.
        top_k: Maximum number of relevant passages to retrieve (default: 3).
        min_score: Minimum similarity score threshold (default: 0.05).
        source_filter: Optional filter by policy file name (e.g. 'refund_policy.md').

    Returns:
        List of dictionaries with passage text, document source, document title,
        section, and similarity score.
    """
    kb = get_default_knowledge_base()
    response = kb.search(
        query=query,
        top_k=top_k,
        min_score=min_score,
        source_filter=source_filter,
    )
    return [r.to_dict() for r in response.results]


def search_knowledge_base_full(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_SCORE_THRESHOLD,
    source_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extended search interface returning full execution metadata and latency.
    """
    kb = get_default_knowledge_base()
    response = kb.search(
        query=query,
        top_k=top_k,
        min_score=min_score,
        source_filter=source_filter,
    )
    return response.to_dict()


# Standard Function Calling Schema for OpenAI / Anthropic / LangChain / Native Agents
SEARCH_KNOWLEDGE_BASE_TOOL_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": (
            "Retrieve grounded company policy passages, return/cancellation rules, "
            "shipping guidelines, warranty details, and payment FAQs for customer support queries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Customer question or policy search query (e.g., 'What is the refund window for electronics?').",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of policy passages to retrieve (1 to 10). Defaults to 3.",
                    "default": 3,
                },
                "min_score": {
                    "type": "number",
                    "description": "Minimum similarity score threshold between 0.0 and 1.0.",
                    "default": 0.05,
                },
                "source_filter": {
                    "type": "string",
                    "description": "Optional specific policy filename filter (e.g. 'refund_policy.md', 'warranty_policy.md').",
                },
            },
            "required": ["query"],
        },
    },
}


if __name__ == "__main__":
    print("Testing search_knowledge_base AI tool...")
    test_query = "What happens if a package is delayed by 3 days?"
    print(f"Tool input query: '{test_query}'")
    tool_results = search_knowledge_base(query=test_query, top_k=2)
    print(f"Tool returned {len(tool_results)} passages:")
    for res in tool_results:
        print(f"  - [{res['document_title']}] (score: {res['score']})")
        print(f"    {res['text'][:90]}...\n")
    print("search_knowledge_base tool test passed!")
