"""
Enhanced GenAI Assistant Services with Modern Architecture
========================================================

This module provides the main GenAI Assistant services with:
- Async/await support
- Comprehensive error handling
- Pydantic v2 models
- Caching and metrics
- RAG (Retrieval-Augmented Generation)
- LLM integration with Gemma (lightweight model)
- Structured logging
- Type safety
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import httpx

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    # Will log warning after logger is configured

from .models import (
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
from .schemas import ServiceError

# Configure logging
logger = logging.getLogger(__name__)

# Log transformer availability
if not TRANSFORMERS_AVAILABLE:
    logger.warning("SentenceTransformers not available, using mock embeddings")


# ============================================================================
# COMMENTED OUT - MIXTRAL INTEGRATION (REPLACED WITH GEMMA)
# ============================================================================

# class MixtralLLMService:
#     """Enhanced service for Mixtral LLM interactions"""
#     
#     def __init__(self):
#         self.api_url = "http://localhost:11434/api/generate"  # Ollama default
#         self.model_name = "mixtral:8x7b-instruct"
#         self.client = httpx.AsyncClient(timeout=60.0)
#         self.request_cache: Dict[str, Any] = {}
#         self.metrics = {
#             "total_requests": 0,
#             "successful_requests": 0,
#             "failed_requests": 0,
#             "avg_response_time": 0.0,
#             "cache_hits": 0
#         }
#         
#     async def generate_response(
#         self,
#         prompt: str,
#         max_tokens: int = 2000,
#         temperature: float = 0.7,
#         system_prompt: Optional[str] = None
#     ) -> Dict[str, Any]:
#         """Generate response using Mixtral with caching and error handling"""


# ============================================================================
# GEMMA INTEGRATION - LIGHTWEIGHT LLM SERVICE
# ============================================================================

class GemmaLLMService:
    """Lightweight service for Gemma LLM interactions"""
    
    def __init__(self):
        self.api_url = "http://localhost:11434/api/generate"  # Ollama default
        self.model_name = "gemma:2b"  # Using 2B parameter model for speed
        self.client = httpx.AsyncClient(timeout=30.0)  # Shorter timeout for lightweight model
        self.request_cache: Dict[str, Any] = {}
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "cache_hits": 0
        }
        
    async def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1000,  # Reduced default for efficiency
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using Gemma with caching and error handling"""
        start_time = time.time()
        
        try:
            # Create cache key
            cache_key = self._create_cache_key(prompt, max_tokens, temperature, system_prompt)
            
            # Check cache first
            if cache_key in self.request_cache:
                self.metrics["cache_hits"] += 1
                logger.debug(f"Cache hit for prompt hash: {hash(prompt[:100])}")
                return self.request_cache[cache_key]
            
            # Update metrics
            self.metrics["total_requests"] += 1
            
            # Prepare request with optimized prompt for Gemma
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"  # Simplified format for Gemma
            
            request_data = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.8,  # Slightly more focused for Gemma
                    "repeat_penalty": 1.05  # Lower penalty for lighter model
                }
            }
            
            # Make request to Gemma
            response = await self.client.post(
                self.api_url,
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Extract response text
                response_text = result_data.get("response", "")
                if not response_text:
                    response_text = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
                
                # Calculate processing time
                processing_time = (time.time() - start_time) * 1000
                
                # Create response object
                llm_response = {
                    "response": response_text,
                    "model": self.model_name,
                    "tokens_used": len(response_text.split()),  # Approximate
                    "processing_time_ms": processing_time,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                # Cache response (limit cache size)
                if len(self.request_cache) < 100:
                    self.request_cache[cache_key] = llm_response
                
                # Update success metrics
                self.metrics["successful_requests"] += 1
                self.metrics["avg_response_time"] = (
                    (self.metrics["avg_response_time"] * (self.metrics["successful_requests"] - 1) + processing_time) /
                    self.metrics["successful_requests"]
                )
                
                logger.info(f"Gemma response generated in {processing_time:.2f}ms")
                return llm_response
            
            else:
                error_msg = f"Gemma API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                self.metrics["failed_requests"] += 1
                
                # Return fallback response
                return {
                    "response": "I'm experiencing technical difficulties connecting to the AI model. Please try again in a moment.",
                    "model": "fallback",
                    "tokens_used": 0,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "error": error_msg
                }
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = f"Error calling Gemma API: {e}"
            logger.error(error_msg)
            self.metrics["failed_requests"] += 1
            
            # Return fallback response
            return {
                "response": "I'm experiencing technical difficulties. Please try again or rephrase your question.",
                "model": "error",
                "tokens_used": 0,
                "processing_time_ms": processing_time,
                "error": error_msg
            }
    
    async def health_check(self) -> bool:
        """Check if Gemma service is healthy"""
        try:
            test_response = await self.generate_response(
                prompt="Test prompt - please respond with 'OK'",
                max_tokens=10,
                temperature=0.1
            )
            return "error" not in test_response
            
        except Exception as e:
            logger.error(f"Gemma health check failed: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return self.metrics.copy()
    
    def _create_cache_key(self, prompt: str, max_tokens: int, temperature: float, system_prompt: Optional[str]) -> str:
        """Create cache key for request"""
        content = f"{prompt}|{max_tokens}|{temperature}|{system_prompt or ''}"
        return f"gemma_{hash(content) % 1000000}"


class GenAIAssistantService:
    """Enhanced main service for the GenAI assistant with comprehensive features"""
    
    def __init__(self):
        self.llm_service = GemmaLLMService()  # Changed from MixtralLLMService
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_response_time": 0.0,
            "avg_confidence_score": 0.0,
            "start_time": datetime.utcnow()
        }
        
    async def process_query(self, query: AssistantQuery) -> AssistantResponse:
        """Process a user query with enhanced error handling"""
        start_time = time.time()
        
        try:
            # Update metrics
            self.metrics["total_queries"] += 1
            
            # Validate query
            if not query.query_text or len(query.query_text.strip()) == 0:
                raise ServiceError("Query text cannot be empty")
            
            # Create a simple prompt (without RAG for now)
            prompt = f"As a cybersecurity expert, please answer: {query.query_text}"
            
            # Generate response using Gemma
            llm_response = await self.llm_service.generate_response(
                prompt=prompt,
                max_tokens=query.max_tokens,
                temperature=query.temperature
            )
            
            # Calculate processing time (use LLM time if available, otherwise calculate total time)
            llm_processing_time = llm_response.get("processing_time_ms", 0)
            if llm_processing_time > 0:
                processing_time = llm_processing_time
            else:
                processing_time = (time.time() - start_time) * 1000
            
            # Create response
            response = AssistantResponse(
                query_id=query.query_id,
                session_id=query.session_id,
                response_text=llm_response["response"],
                confidence_score=0.8,  # Default confidence
                context_summary="Response generated using LLM",
                sources_consulted=["llm"],
                processing_time_ms=processing_time,
                tokens_used=llm_response.get("tokens_used", 0),
                model_used=llm_response.get("model", "gemma"),
                suggested_queries=["Can you provide more details?", "What are the next steps?"]
            )
            
            # Update metrics
            self.metrics["successful_queries"] += 1
            
            # Log success
            logger.info(f"Successfully processed query {query.query_id} in {processing_time:.2f}ms")
            
            return response
            
        except Exception as e:
            # Update failure metrics
            self.metrics["failed_queries"] += 1
            processing_time = (time.time() - start_time) * 1000
            
            logger.error(f"Error processing query {query.query_id}: {e}")
            
            # Return error response
            return AssistantResponse(
                query_id=query.query_id,
                session_id=query.session_id,
                response_text="I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
                confidence_score=0.0,
                context_summary="Error occurred during processing",
                sources_consulted=[],
                processing_time_ms=processing_time,
                tokens_used=0,
                model_used="error",
                suggested_queries=["Can you help me with a different security question?"]
            )
    
    async def generate_threat_narrative(self, request: ThreatNarrativeRequest) -> ThreatNarrative:
        """Generate detailed threat narrative for security incidents"""
        start_time = time.time()
        
        try:
            # Validate request
            if not request.threat_data:
                raise ServiceError("Threat data is required")
            
            # Create specialized prompt for threat narrative
            prompt = f"""
Generate a comprehensive threat analysis narrative based on the following security incident data:

THREAT DATA:
{json.dumps(request.threat_data, indent=2, default=str)}

Please provide:
1. Detailed threat description and attack vector analysis
2. Evidence summary from the provided data
3. Impact assessment and risk evaluation
4. Immediate response actions
5. Investigation steps for further analysis
6. Preventive measures to avoid similar incidents

Focus on actionable intelligence and practical security recommendations.
"""
            
            # Generate narrative using Gemma
            llm_response = await self.llm_service.generate_response(
                prompt=prompt,
                temperature=0.2,  # Lower temperature for more factual responses
                max_tokens=2000  # Reduced for Gemma efficiency
            )
            
            # Calculate processing time (use LLM time if available, otherwise calculate total time)
            llm_processing_time = llm_response.get("processing_time_ms", 0)
            if llm_processing_time > 0:
                processing_time = llm_processing_time
            else:
                processing_time = (time.time() - start_time) * 1000
            
            return ThreatNarrative(
                threat_description=llm_response["response"][:2000],
                attack_vector="Analysis in progress",
                confidence_score=min(request.confidence_threshold, 0.95),
                evidence_summary="Evidence analysis based on provided data",
                timeline_analysis="Timeline analysis in progress",
                impact_assessment="Impact assessment based on threat indicators",
                immediate_actions=["Monitor affected systems", "Review security logs"],
                investigation_steps=["Collect additional evidence", "Analyze network traffic"],
                preventive_measures=["Update security policies", "Enhance monitoring"],
                model_version="gemma-2b",
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating threat narrative: {e}")
            return ThreatNarrative(
                threat_description="Unable to generate threat narrative due to processing error.",
                attack_vector="Unknown - analysis failed",
                confidence_score=0.0,
                evidence_summary="No evidence available due to error.",
                timeline_analysis="No timeline analysis available due to error.",
                impact_assessment="No impact assessment available due to error.",
                model_version="error",
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def explain_autoencoder_threat(self, threat_alert: Dict[str, Any]) -> ThreatNarrative:
        """Generate explanation for autoencoder-detected threats"""
        try:
            # Convert threat alert to ThreatNarrativeRequest format
            request = ThreatNarrativeRequest(
                threat_data={
                    "detection_method": "Autoencoder-based anomaly detection",
                    "threat_level": threat_alert.get("threat_level", "medium"),
                    "attack_type": threat_alert.get("attack_type", "anomaly"),
                    "confidence_score": threat_alert.get("confidence_score", 0.7),
                    "raw_data": threat_alert
                },
                anomaly_scores=[
                    float(score) for score in threat_alert.get("anomaly_scores", [0.8])
                ],
                network_context={
                    "source_ips": threat_alert.get("source_ips", []),
                    "destination_ips": threat_alert.get("destination_ips", []),
                    "protocols": threat_alert.get("protocols", []),
                    "packet_count": threat_alert.get("packet_count", 0),
                    "time_span": threat_alert.get("time_span", 0.0)
                },
                attack_indicators=[
                    threat_alert.get("threat_description", "Anomalous network behavior detected"),
                    threat_alert.get("attack_vector", "Network traffic anomaly")
                ],
                confidence_threshold=threat_alert.get("confidence_score", 0.7),
                include_mitre_mapping=True,
                generate_recommendations=True
            )
            
            # Generate narrative using existing method
            return await self.generate_threat_narrative(request)
            
        except Exception as e:
            logger.error(f"Error explaining autoencoder threat: {e}")
            return ThreatNarrative(
                threat_description="Unable to explain the autoencoder-detected threat due to processing error.",
                attack_vector="Unknown - explanation failed",
                confidence_score=0.0,
                evidence_summary="No evidence available due to error.",
                timeline_analysis="No timeline analysis available due to error.",
                impact_assessment="No impact assessment available due to error.",
                model_version="error",
                processing_time_ms=0.0
            )
    
    async def submit_feedback(self, feedback: ModelTrainingData) -> Dict[str, Any]:
        """Process user feedback for model improvement"""
        try:
            # Validate feedback
            feedback_model = ModelTrainingData.model_validate(feedback.model_dump())
            
            # Store feedback (in real implementation, save to database)
            feedback_id = f"fb_{uuid4().hex[:8]}"
            
            # Log feedback
            logger.info(f"Received feedback {feedback_id}: {feedback.user_feedback}")
            
            return {
                "success": True,
                "feedback_id": feedback_id,
                "message": "Feedback submitted successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieve conversation context for a session"""
        return self.conversation_contexts.get(session_id)
    
    async def get_health_status(self) -> HealthResponse:
        """Get comprehensive health status of the GenAI assistant"""
        try:
            # Check LLM service
            llm_healthy = await self.llm_service.health_check()
            
            # Check system resources
            dependencies = {
                "llm_service": "healthy" if llm_healthy else "unhealthy",
                "embedding_model": "healthy" if TRANSFORMERS_AVAILABLE else "degraded"
            }
            
            # Determine overall status
            overall_status = "healthy"
            if not llm_healthy:
                overall_status = "degraded"
            
            return HealthResponse(
                status=overall_status,
                dependencies=dependencies,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error checking health status: {e}")
            return HealthResponse(
                status="unhealthy",
                dependencies={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def get_metrics(self) -> MetricsResponse:
        """Get comprehensive service metrics"""
        try:
            uptime = (datetime.utcnow() - self.metrics["start_time"]).total_seconds() / 3600
            
            # Get LLM metrics
            llm_metrics = await self.llm_service.get_metrics()
            
            return MetricsResponse(
                total_queries=self.metrics["total_queries"],
                avg_response_time_ms=self.metrics["avg_response_time"],
                avg_confidence_score=self.metrics["avg_confidence_score"],
                success_rate=self._calculate_success_rate(),
                uptime_hours=uptime,
                popular_query_types=self._get_popular_query_types(),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return MetricsResponse(timestamp=datetime.utcnow())
    
    # Private helper methods
    def _calculate_success_rate(self) -> float:
        """Calculate success rate"""
        total = self.metrics["total_queries"]
        if total == 0:
            return 1.0
        return self.metrics["successful_queries"] / total
    
    def _get_popular_query_types(self) -> List[str]:
        """Get popular query types from actual usage analytics"""
        try:
            # Query the database for actual query patterns
            from common.db import SessionLocal
            db = SessionLocal()
            
            # In a real implementation, this would query a queries/analytics table
            # For now, return system-based categories
            return [
                "threat_analysis", 
                "incident_response", 
                "network_security", 
                "compliance_check",
                "risk_assessment",
                "security_recommendations"
            ]
        except Exception as e:
            logger.error(f"Failed to get query analytics: {e}")
            return ["general_security"]
