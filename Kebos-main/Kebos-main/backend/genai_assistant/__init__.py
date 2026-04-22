"""
GenAI Assistant Module

Context-aware GenAI assistant with RAG architecture for threat analysis.
Provides natural language interface for cybersecurity insights.
"""

from .api import router
from .models import AssistantQuery, AssistantResponse, ConversationContext
from .services import GenAIAssistantService
from .tasks import process_assistant_query, update_knowledge_base

__all__ = [
    "router",
    "AssistantQuery",
    "AssistantResponse", 
    "ConversationContext",
    "GenAIAssistantService",
    "process_assistant_query",
    "update_knowledge_base"
]
