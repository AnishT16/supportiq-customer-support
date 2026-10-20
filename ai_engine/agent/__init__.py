"""
SupportIQ AI Support Agent Package.
Exposes SupportIQAgent, AgentRequest, AgentResponse, IntentClassifier, and ControlledToolRegistry.
"""

from ai_engine.agent.controller import SupportIQAgent
from ai_engine.agent.intent import IntentClassifier
from ai_engine.agent.llm import LLMProvider
from ai_engine.agent.schemas import (
    AgentRequest,
    AgentResponse,
    IntentType,
    ToolInvocation,
)
from ai_engine.agent.tools import ControlledToolRegistry

__all__ = [
    "SupportIQAgent",
    "AgentRequest",
    "AgentResponse",
    "IntentType",
    "ToolInvocation",
    "ControlledToolRegistry",
    "IntentClassifier",
    "LLMProvider",
]
