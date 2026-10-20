"""
SupportIQ AI/ML Engine Package
An isolated, importable AI/ML core providing:
- Action Simulation & Policy Evaluation
- Predictive Support Intervention
- RAG Knowledge Base
- Support Agent Controller & Tool Calling
"""

from pathlib import Path
import sys

_project_root = str(Path(__file__).resolve().parents[1])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

__version__ = "0.1.0"

try:
    from ai_engine.rag import KnowledgeBase, search_knowledge_base
    from ai_engine.agent import SupportIQAgent, AgentRequest, AgentResponse, ControlledToolRegistry
except ImportError:
    from .rag import KnowledgeBase, search_knowledge_base
    from .agent import SupportIQAgent, AgentRequest, AgentResponse, ControlledToolRegistry

__all__ = [
    "__version__",
    "KnowledgeBase",
    "search_knowledge_base",
    "SupportIQAgent",
    "AgentRequest",
    "AgentResponse",
    "ControlledToolRegistry",
]

