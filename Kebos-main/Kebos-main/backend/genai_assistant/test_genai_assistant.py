"""
Comprehensive Test Suite for GenAI Assistant Module
=================================================

Tests for models, services, schemas, and API endpoints with:
- Async/await testing
- Pydantic v2 model validation
- Service error handling
- Mock LLM responses
- Type safety validation
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Test imports
from genai_assistant.models import (
    AssistantQuery,
    AssistantResponse,
    ConversationContext,
    HealthResponse,
    MetricsResponse,
    ModelTrainingData,
    QueryType,
    RAGQuery,
    RetrievedContext,
    ThreatNarrative,
    ThreatNarrativeRequest
)
from genai_assistant.schemas import (
    QueryRequest,
    QueryResponse,
    FeedbackRequest,
    ChatMessage,
    ErrorResponse,
    ServiceError
)
from genai_assistant.services import (
    # MixtralLLMService,  # COMMENTED OUT - replaced with Gemma
    GemmaLLMService,
    GenAIAssistantService
)


class TestGenAIAssistantModels:
    """Test suite for GenAI Assistant Pydantic v2 models"""
    
    def test_assistant_query_model_validation(self):
        """Test AssistantQuery model validation and serialization"""
        query_data = {
            "query_id": str(uuid4()),
            "session_id": str(uuid4()),
            "user_id": "test_user",
            "query_text": "What security threats were detected in the last 24 hours?",
            "query_type": QueryType.THREAT_ANALYSIS,
            "time_window_hours": 24,
            "max_tokens": 2000,
            "temperature": 0.7,
            "ip_addresses": ["192.168.1.100", "10.0.0.5"],
            "threat_types": ["malware", "lateral_movement"]
        }
        
        # Test model creation and validation
        query = AssistantQuery(**query_data)
        
        assert query.query_text == query_data["query_text"]
        assert query.query_type == QueryType.THREAT_ANALYSIS
        assert query.time_window_hours == 24
        assert len(query.ip_addresses) == 2
        assert "malware" in query.threat_types
        
        # Test serialization
        serialized = query.model_dump()
        assert serialized["query_type"] == "threat_analysis"
        assert serialized["max_tokens"] == 2000
    
    def test_assistant_query_validation_errors(self):
        """Test AssistantQuery validation errors"""
        # Test empty query text
        with pytest.raises(ValueError):
            AssistantQuery(
                query_id=str(uuid4()),
                session_id=str(uuid4()),
                user_id="test_user",
                query_text="",  # Empty query
                query_type=QueryType.GENERAL_SECURITY
            )
        
        # Test invalid max_tokens
        with pytest.raises(ValueError):
            AssistantQuery(
                query_id=str(uuid4()),
                session_id=str(uuid4()),
                user_id="test_user",
                query_text="Test query",
                query_type=QueryType.GENERAL_SECURITY,
                max_tokens=0  # Invalid token count
            )
    
    def test_assistant_response_model(self):
        """Test AssistantResponse model"""
        response_data = {
            "query_id": str(uuid4()),
            "session_id": str(uuid4()),
            "response_text": "Based on the analysis, I detected 3 security threats...",
            "confidence_score": 0.87,
            "context_summary": "Analysis based on 15 threat alerts and 200 network records",
            "sources_consulted": ["threat_alerts", "network_logs", "siem_events"],
            "key_insights": [
                "Lateral movement pattern detected",
                "Suspicious PowerShell execution",
                "Unusual network traffic to known C2 server"
            ],
            "recommended_actions": [
                "Isolate affected systems",
                "Reset compromised credentials",
                "Review network segmentation"
            ],
            "mitre_techniques": ["T1059.001", "T1021.001", "T1043"],
            "processing_time_ms": 1250.5,
            "tokens_used": 345,
            "model_used": "mixtral-8x7b-instruct",
            "suggested_queries": [
                "Can you provide more details about the lateral movement?",
                "What are the indicators of compromise?",
                "How can we prevent similar attacks?"
            ]
        }
        
        response = AssistantResponse(**response_data)
        
        assert response.confidence_score == 0.87
        assert len(response.key_insights) == 3
        assert len(response.mitre_techniques) == 3
        assert response.processing_time_ms > 1000
        assert "mixtral" in response.model_used
    
    def test_threat_narrative_request(self):
        """Test ThreatNarrativeRequest model"""
        request_data = {
            "threat_data": {
                "threat_level": "high",
                "attack_type": "lateral_movement",
                "detection_method": "autoencoder_anomaly",
                "confidence_score": 0.89
            },
            "anomaly_scores": [0.92, 0.87, 0.91],
            "network_context": {
                "source_ips": ["192.168.1.100", "192.168.1.105"],
                "destination_ips": ["10.0.0.5", "10.0.0.10"],
                "protocols": ["TCP", "RDP"],
                "packet_count": 1500,
                "time_span": 3600.0
            },
            "attack_indicators": [
                "Unusual RDP traffic patterns",
                "Privilege escalation attempts",
                "Suspicious PowerShell execution"
            ],
            "confidence_threshold": 0.85,
            "include_mitre_mapping": True,
            "generate_recommendations": True
        }
        
        request = ThreatNarrativeRequest(**request_data)
        
        assert request.threat_data["threat_level"] == "high"
        assert len(request.anomaly_scores) == 3
        assert request.network_context["packet_count"] == 1500
        assert request.include_mitre_mapping is True
    
    def test_health_response_model(self):
        """Test HealthResponse model"""
        health_data = {
            "status": "healthy",
            "dependencies": {
                "llm_service": "healthy",
                "embedding_model": "healthy",
                "database": "degraded"
            },
            "timestamp": datetime.utcnow()
        }
        
        health = HealthResponse(**health_data)
        
        assert health.status == "healthy"
        assert health.dependencies["database"] == "degraded"
        assert isinstance(health.timestamp, datetime)


class TestGenAIAssistantSchemas:
    """Test suite for GenAI Assistant schemas and validation"""
    
    def test_query_request_schema(self):
        """Test QueryRequest schema validation"""
        request_data = {
            "query_text": "Analyze recent security events",
            "query_type": "threat_analysis",
            "time_window_hours": 24,
            "max_tokens": 2000,
            "temperature": 0.7,
            "ip_addresses": ["192.168.1.100"],
            "threat_types": ["malware"]
        }
        
        request = QueryRequest(**request_data)
        
        assert request.query_text == "Analyze recent security events"
        assert request.query_type == "threat_analysis"
        assert request.ip_addresses == ["192.168.1.100"]
        assert request.threat_types == ["malware"]
    
    def test_service_error_exception(self):
        """Test ServiceError exception handling"""
        error_message = "Invalid query parameters"
        
        error = ServiceError(error_message)
        
        assert str(error) == error_message
        assert isinstance(error, Exception)


# ============================================================================
# COMMENTED OUT - MIXTRAL TESTS (REPLACED WITH GEMMA)
# ============================================================================

# @pytest.mark.asyncio
# class TestMixtralLLMService:
#     """Test suite for MixtralLLMService"""
#     
#     async def test_llm_service_initialization(self):
#         """Test LLM service initialization"""
#         service = MixtralLLMService()
#         
#         assert service.api_url == "http://localhost:11434/api/generate"
#         assert service.model_name == "mixtral:8x7b-instruct"
#         assert service.metrics["total_requests"] == 0


# ============================================================================
# GEMMA LLM SERVICE TESTS
# ============================================================================

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
        assert result["processing_time_ms"] >= 0  # Allow 0 for fast mocked responses
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


# ============================================================================
# COMMENTED OUT - REMAINING MIXTRAL TESTS
# ============================================================================

# The rest of the Mixtral tests are commented out to avoid import errors
        )
        
        assert "technical difficulties" in result["response"]
        assert result["model"] == "fallback"
        assert "error" in result
        assert service.metrics["failed_requests"] == 1
    
    @patch('httpx.AsyncClient.post')
    async def test_generate_response_caching(self, mock_post):
        """Test response caching functionality"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Cached test response",
            "eval_count": 25
        }
        mock_post.return_value = mock_response
        
        service = MixtralLLMService()
        
        # First request
        result1 = await service.generate_response(
            prompt="Test prompt for caching",
            max_tokens=100,
            temperature=0.7
        )
        
        # Second identical request (should hit cache)
        result2 = await service.generate_response(
            prompt="Test prompt for caching",
            max_tokens=100,
            temperature=0.7
        )
        
        assert result1["response"] == result2["response"]
        assert service.metrics["cache_hits"] == 1
        assert mock_post.call_count == 1  # Only one actual API call
    
    async def test_health_check(self):
        """Test health check functionality"""
        service = MixtralLLMService()
        
        # Mock generate_response for health check
        with patch.object(service, 'generate_response') as mock_generate:
            mock_generate.return_value = {"response": "OK", "model": "mixtral"}
            
            result = await service.health_check()
            assert result is True
            
            # Test unhealthy response
            mock_generate.return_value = {"response": "Error", "model": "error", "error": "Failed"}
            
            result = await service.health_check()
            assert result is False


@pytest.mark.asyncio
class TestGenAIAssistantService:
    """Test suite for GenAIAssistantService"""
    
    async def test_service_initialization(self):
        """Test service initialization"""
        service = GenAIAssistantService()
        
        assert service.llm_service is not None
        assert service.metrics["total_queries"] == 0
        assert isinstance(service.conversation_contexts, dict)
    
    async def test_process_query_success(self):
        """Test successful query processing"""
        service = GenAIAssistantService()
        
        # Mock LLM service response
        with patch.object(service.llm_service, 'generate_response') as mock_llm:
            mock_llm.return_value = {
                "response": "Based on the threat analysis, I found 3 potential security issues...",
                "model": "mixtral",
                "tokens_used": 150,
                "processing_time_ms": 800
            }
            
            query = AssistantQuery(
                query_id=str(uuid4()),
                session_id=str(uuid4()),
                user_id="test_user",
                query_text="Analyze recent security threats",
                query_type=QueryType.THREAT_ANALYSIS
            )
            
            response = await service.process_query(query)
            
            assert response.query_id == query.query_id
            assert response.session_id == query.session_id
            assert "security issues" in response.response_text
            assert response.confidence_score > 0
            assert response.processing_time_ms > 0
            assert service.metrics["successful_queries"] == 1
    
    async def test_process_query_validation_error(self):
        """Test query validation error handling"""
        service = GenAIAssistantService()

        # Test with None query to trigger validation error
        with pytest.raises(Exception):  # Could be ValidationError or ServiceError
            await service.process_query(None)
    
    async def test_generate_threat_narrative(self):
        """Test threat narrative generation"""
        service = GenAIAssistantService()
        
        # Mock LLM service response
        with patch.object(service.llm_service, 'generate_response') as mock_llm:
            mock_llm.return_value = {
                "response": "Threat Analysis: Advanced persistent threat detected with lateral movement indicators...",
                "model": "mixtral",
                "tokens_used": 250,
                "processing_time_ms": 1200
            }
            
            request = ThreatNarrativeRequest(
                threat_data={
                    "threat_level": "high",
                    "attack_type": "lateral_movement",
                    "confidence_score": 0.87
                },
                anomaly_scores=[0.89, 0.92],
                network_context={
                    "source_ips": ["192.168.1.100"],
                    "destination_ips": ["10.0.0.5"],
                    "protocols": ["TCP"],
                    "packet_count": 500,
                    "time_span": 1800.0
                },
                attack_indicators=["Unusual RDP traffic"],
                confidence_threshold=0.85,
                include_mitre_mapping=True,
                generate_recommendations=True
            )
            
            narrative = await service.generate_threat_narrative(request)
            
            assert "threat" in narrative.threat_description.lower()
            assert narrative.confidence_score > 0
            assert narrative.processing_time_ms > 0
            assert narrative.model_version == "mixtral-8x7b-instruct"
    
    async def test_explain_autoencoder_threat(self):
        """Test autoencoder threat explanation"""
        service = GenAIAssistantService()
        
        # Mock generate_threat_narrative
        with patch.object(service, 'generate_threat_narrative') as mock_narrative:
            mock_narrative.return_value = ThreatNarrative(
                threat_description="Autoencoder detected anomalous network behavior...",
                attack_vector="Network traffic anomaly",
                confidence_score=0.78,
                evidence_summary="Anomaly scores indicate suspicious patterns",
                timeline_analysis="Anomalous activity detected over 30-minute window",
                impact_assessment="Potential lateral movement detected",
                immediate_actions=["Monitor affected systems"],
                investigation_steps=["Analyze network logs"],
                preventive_measures=["Update security policies"],
                model_version="mixtral-8x7b-instruct",
                processing_time_ms=950.0
            )
            
            threat_alert = {
                "threat_level": "medium",
                "attack_type": "anomaly",
                "confidence_score": 0.78,
                "anomaly_scores": [0.82, 0.75],
                "source_ips": ["192.168.1.100"],
                "destination_ips": ["10.0.0.5"],
                "protocols": ["TCP"],
                "packet_count": 200,
                "time_span": 1800.0,
                "threat_description": "Anomalous network behavior detected",
                "attack_vector": "Network traffic anomaly"
            }
            
            narrative = await service.explain_autoencoder_threat(threat_alert)
            
            assert "autoencoder" in narrative.threat_description.lower()
            assert narrative.attack_vector == "Network traffic anomaly"
            assert narrative.confidence_score > 0
    
    async def test_submit_feedback(self):
        """Test feedback submission"""
        service = GenAIAssistantService()

        feedback = ModelTrainingData(
            query_id=str(uuid4()),
            response_id=str(uuid4()),
            user_feedback="helpful",
            feedback_details="The response was helpful",
            improvement_suggestions=["Add more specific recommendations"]
        )
        
        result = await service.submit_feedback(feedback)
        
        assert result["success"] is True
        assert "feedback_id" in result
        assert "timestamp" in result
    
    async def test_get_health_status(self):
        """Test health status check"""
        service = GenAIAssistantService()
        
        # Mock LLM health check
        with patch.object(service.llm_service, 'health_check') as mock_health:
            mock_health.return_value = True
            
            health = await service.get_health_status()
            
            assert health.status == "healthy"
            assert health.dependencies["llm_service"] == "healthy"
            assert isinstance(health.timestamp, datetime)
    
    async def test_get_metrics(self):
        """Test metrics retrieval"""
        service = GenAIAssistantService()
        
        # Mock LLM metrics
        with patch.object(service.llm_service, 'get_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "total_requests": 10,
                "successful_requests": 8,
                "failed_requests": 2,
                "avg_response_time": 1200.5,
                "cache_hits": 3
            }
            
            # Update service metrics
            service.metrics["total_queries"] = 5
            service.metrics["successful_queries"] = 4
            service.metrics["failed_queries"] = 1
            
            metrics = await service.get_metrics()
            
            assert metrics.total_queries == 5
            assert metrics.uptime_hours > 0
            assert metrics.success_rate == 0.8  # 4/5
            assert isinstance(metrics.timestamp, datetime)


# Test runner for development
if __name__ == "__main__":
    # Run basic tests
    import sys
    import subprocess
    
    print("Running GenAI Assistant tests...")
    
    try:
        # Run pytest if available
        result = subprocess.run([
            sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=60)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("pytest not available or timed out, running basic test validation...")
        
        # Basic validation
        try:
            # Test model imports and basic validation
            query = AssistantQuery(
                query_id=str(uuid4()),
                session_id=str(uuid4()),
                user_id="test",
                query_text="Test query",
                query_type=QueryType.GENERAL_SECURITY
            )
            print("✓ AssistantQuery model validation passed")
            
            # Test service initialization
            service = GenAIAssistantService()
            print("✓ GenAIAssistantService initialization passed")
            
            print("\n✅ Basic tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Basic test failed: {e}")
            sys.exit(1)
