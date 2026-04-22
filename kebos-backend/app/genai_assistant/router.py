"""
LLM Router for Kebos AI.
Phase 2.2 - Routes LLM requests based on data classification and tenant type.
"""
import logging
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def complete(self, system: str, user: str) -> str:
        """Complete a prompt with the LLM"""
        pass


class LocalGemmaClient(LLMClient):
    """Local Gemma model - air-gapped, no external calls"""
    
    async def complete(self, system: str, user: str) -> str:
        """Complete using local Gemma model"""
        # TODO: Implement local Gemma inference
        logger.info("Using local Gemma for completion")
        return "Local Gemma completion - TODO"


class AirGappedGemmaClient(LLMClient):
    """Air-gapped Gemma for RESTRICTED data"""
    
    async def complete(self, system: str, user: str) -> str:
        """Complete using air-gapped Gemma"""
        # TODO: Implement air-gapped Gemma inference
        logger.info("Using air-gapped Gemma for completion")
        return "Air-gapped Gemma completion - TODO"


class GroqClient(LLMClient):
    """Groq API client for PUBLIC/INTERNAL data"""
    
    def __init__(self):
        self.api_key = None  # TODO: Load from config
    
    async def complete(self, system: str, user: str) -> str:
        """Complete using Groq API"""
        # TODO: Implement Groq API call
        logger.info("Using Groq API for completion")
        return "Groq completion - TODO"


class LLMRouter:
    """
    Routes LLM requests based on classification and tenant type.
    Government tenants ALWAYS use local Gemma.
    """
    
    def __init__(self):
        self.local_gemma = LocalGemmaClient()
        self.air_gapped_gemma = AirGappedGemmaClient()
        self.groq = GroqClient()
    
    def get_client(self, classification: str, tenant_type: str) -> LLMClient:
        """
        Get appropriate LLM client based on classification and tenant type.
        
        Args:
            classification: Data classification (CONFIDENTIAL, RESTRICTED, PUBLIC, INTERNAL)
            tenant_type: Tenant type (government, bfsi, enterprise)
        
        Returns:
            Appropriate LLM client
        
        Raises:
            ValueError: If unknown classification or tenant type
        """
        # Government tenants ALWAYS use local Gemma (no exceptions)
        if tenant_type == 'government':
            logger.info("Government tenant - using local Gemma")
            return self.local_gemma
        
        # RESTRICTED data uses air-gapped Gemma
        if classification == 'RESTRICTED':
            logger.info("RESTRICTED data - using air-gapped Gemma")
            return self.air_gapped_gemma
        
        # CONFIDENTIAL data uses local Gemma
        if classification == 'CONFIDENTIAL':
            logger.info("CONFIDENTIAL data - using local Gemma")
            return self.local_gemma
        
        # PUBLIC or INTERNAL data can use Groq
        if classification in ('PUBLIC', 'INTERNAL'):
            logger.info(f"{classification} data - using Groq")
            return self.groq
        
        raise ValueError(f"Unknown classification: {classification}")


# Singleton instance
_router_instance: LLMRouter = None


def get_llm_router() -> LLMRouter:
    """Get or create the singleton LLMRouter instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance
