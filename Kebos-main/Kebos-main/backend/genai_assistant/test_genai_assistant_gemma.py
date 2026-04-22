"""
GenAI Assistant Test Suite - Gemma Integration
==============================================

Test suite for the GenAI Assistant with Gemma LLM integration.
Replaces Mixtral with lightweight Gemma model.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from backend.genai_assistant.models import (
    AssistantQuery,
    AssistantResponse, 
    ConversationContext,
    HealthResponse,
    MetricsResponse,
    QueryType,
    ThreatNarrative,
    ThreatNarrativeRequest
)
from backend.genai_assistant.services import (
    GemmaLLMService,
    GenAIAssistantService
)


class TestGenAIAssistantModels:
    """Test suite for GenAI Assistant Pydantic v2 models"""
    
    def test_assistant_query_model(self):
        """Test AssistantQuery model validation"""
        query = AssistantQuery(
            query_text="What are common cybersecurity threats?",
            query_type=QueryType.GENERAL,
            max_tokens=200,
            temperature=0.7
        )
        
        assert query.query_text == "What are common cybersecurity threats?"
        assert query.query_type == QueryType.GENERAL
        assert query.max_tokens == 200
        assert query.temperature == 0.7
        assert query.query_id is not None
        assert query.session_id is not None
    
    def test_assistant_response_model(self):
        """Test AssistantResponse model validation"""
        response = AssistantResponse(
            query_id=str(uuid4()),
            response_text="Here are common cybersecurity threats...",
            confidence_score=0.85,
            context_summary="General cybersecurity information",
            sources_consulted=["knowledge_base", "llm"],
            processing_time_ms=150.5,
            tokens_used=45,
            model_used="gemma:2b"
        )
        
        assert response.confidence_score == 0.85
        assert response.model_used == "gemma:2b"
        assert response.processing_time_ms == 150.5
        assert len(response.sources_consulted) == 2


@pytest.mark.asyncio
class TestGemmaLLMService:
    """Test suite for GemmaLLMService"""
    
    async def test_llm_service_initialization(self):
        """Test LLM service initialization"""
        service = GemmaLLMService()
        
        assert service.api_url == "http://localhost:11434/api/generate"
        assert service.model_name == "gemma:2b"
        assert service.metrics["total_requests"] == 0
    
    @patch('httpx.AsyncClient.post')
    async def test_generate_response_success(self, mock_post):
        """Test successful response generation"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from Gemma",
            "eval_count": 30
        }
        mock_post.return_value = mock_response
        
        service = GemmaLLMService()
        
        result = await service.generate_response(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        assert result["response"] == "This is a test response from Gemma"
        assert result["model"] == "gemma:2b"
        assert result["processing_time_ms"] >= 0
        assert service.metrics["successful_requests"] == 1
    
    @patch('httpx.AsyncClient.post')
    async def test_generate_response_api_error(self, mock_post):
        """Test API error handling"""
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        service = GemmaLLMService()
        
        result = await service.generate_response(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        assert "I'm experiencing technical difficulties" in result["response"]
        assert result["model"] == "fallback"
        assert service.metrics["failed_requests"] == 1
    
    @patch('httpx.AsyncClient.post')
    async def test_health_check_success(self, mock_post):
        """Test successful health check"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "OK",
            "eval_count": 1
        }
        mock_post.return_value = mock_response
        
        service = GemmaLLMService()
        
        is_healthy = await service.health_check()
        assert is_healthy is True


@pytest.mark.asyncio
class TestGenAIAssistantService:
    """Test suite for GenAIAssistantService with Gemma integration"""

    async def test_service_initialization(self):
        """Test service initialization"""
        service = GenAIAssistantService()
        
        assert service.llm_service is not None
        assert isinstance(service.llm_service, GemmaLLMService)
        assert service.metrics["total_queries"] == 0
        assert isinstance(service.conversation_contexts, dict)

    @patch.object(GemmaLLMService, 'generate_response')
    async def test_process_query_success(self, mock_generate):
        """Test successful query processing"""
        # Mock LLM response
        mock_generate.return_value = {
            "response": "This is a test cybersecurity response from Gemma",
            "model": "gemma:2b",
            "tokens_used": 15,
            "processing_time_ms": 250.0
        }
        
        service = GenAIAssistantService()
        query = AssistantQuery(
            query_text="What are common cyber threats?",
            query_type=QueryType.GENERAL,
            max_tokens=200,
            temperature=0.7
        )
        
        response = await service.process_query(query)
        
        assert response.query_id is not None
        assert "cybersecurity" in response.response_text
        assert response.confidence_score == 0.8
        assert response.processing_time_ms >= 0
        assert response.model_used == "gemma"
        assert service.metrics["successful_queries"] == 1

    @patch.object(GemmaLLMService, 'generate_response')
    async def test_generate_threat_narrative(self, mock_generate):
        """Test threat narrative generation"""
        # Mock LLM response
        mock_generate.return_value = {
            "response": "Detailed threat analysis narrative with indicators and recommendations from Gemma",
            "model": "gemma:2b",
            "tokens_used": 80,
            "processing_time_ms": 800.0
        }
        
        service = GenAIAssistantService()
        
        request = ThreatNarrativeRequest(
            threat_indicators=["unusual network traffic", "suspicious IP addresses"],
            attack_vectors=["SQL injection", "phishing"],
            affected_systems=["web server", "database"],
            severity_level="HIGH"
        )
        
        narrative = await service.generate_threat_narrative(request)
        
        assert narrative.narrative_id is not None
        assert "threat analysis" in narrative.narrative_text
        assert narrative.severity_level == "HIGH"
        assert len(narrative.threat_indicators) == 2
        assert len(narrative.attack_vectors) == 2
        assert len(narrative.affected_systems) == 2
        assert narrative.model_version == "gemma-2b"
        assert narrative.processing_time_ms >= 0

    async def test_get_service_health(self):
        """Test service health check"""
        service = GenAIAssistantService()
        
        health = await service.get_service_health()
        
        assert health.service_name == "genai_assistant"
        assert health.version == "1.0.0"
        assert isinstance(health.uptime_seconds, (int, float))
        assert health.uptime_seconds >= 0


if __name__ == "__main__":
    """Basic functionality test when run directly"""
    import sys
    
    async def run_basic_tests():
        try:
            print("🧪 Running basic GenAI Assistant tests with Gemma...")
            
            # Test model creation
            query = AssistantQuery(
                query_text="Test query",
                query_type=QueryType.GENERAL,
                max_tokens=100,
                temperature=0.7
            )
            print("✓ AssistantQuery model validation passed")
            
            # Test service initialization
            service = GenAIAssistantService()
            print("✓ GenAIAssistantService initialization passed")
            print(f"✓ LLM Service: {type(service.llm_service).__name__}")
            print(f"✓ Model: {service.llm_service.model_name}")
            
            print("\n✅ Basic tests completed successfully!")
            print("🔄 Gemma integration active - Mixtral commented out")
            
        except Exception as e:
            print(f"\n❌ Basic test failed: {e}")
            sys.exit(1)
    
    asyncio.run(run_basic_tests())
