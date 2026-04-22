"""
Enhanced GenAI Assistant Services with Modern Architecture
========================================================

This module provides the main GenAI Assistant services with:
- Async/await support
- Comprehensive error handling
- Pydantic v2 models
- Caching and metrics
- RAG (Retrieval-Augmented Generation)
- LLM integration with Mixtral
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
import numpy as np
from sentence_transformers import SentenceTransformer

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
from ..common.models import BaseModel


# Configure logging
logger = logging.getLogger(__name__)


class MixtralLLMService:
    """Enhanced service for Mixtral LLM interactions"""
    
    def __init__(self):
        self.api_url = "http://localhost:11434/api/generate"  # Ollama default
        self.model_name = "mixtral:8x7b-instruct"
        self.client = httpx.AsyncClient(timeout=60.0)
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
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using Mixtral with caching and error handling"""
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
            
            # Prepare request
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            request_data = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            # Make request to Mixtral
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
                
                logger.info(f"Mixtral response generated in {processing_time:.2f}ms")
                return llm_response
            
            else:
                error_msg = f"Mixtral API error: {response.status_code} - {response.text}"
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
            error_msg = f"Error calling Mixtral API: {e}"
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
        """Check if Mixtral service is healthy"""
        try:
            test_response = await self.generate_response(
                prompt="Test prompt - please respond with 'OK'",
                max_tokens=10,
                temperature=0.1
            )
            return "error" not in test_response
            
        except Exception as e:
            logger.error(f"Mixtral health check failed: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return self.metrics.copy()
    
    def _create_cache_key(self, prompt: str, max_tokens: int, temperature: float, system_prompt: Optional[str]) -> str:
        """Create cache key for request"""
        content = f"{prompt}|{max_tokens}|{temperature}|{system_prompt or ''}"
        return f"mixtral_{hash(content) % 1000000}"
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using Mixtral LLM"""
        try:
            # Format prompt for Mixtral
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Ollama API call
            payload = {
                "model": self.model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                },
                "stream": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "response": result.get("message", {}).get("content", ""),
                "tokens_used": result.get("eval_count", 0),
                "model": self.model_name,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating Mixtral response: {e}")
            return {
                "response": "I apologize, but I'm unable to process your request at this time.",
                "error": str(e),
                "success": False
            }


class RAGService:
    """Retrieval-Augmented Generation service for context-aware responses"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = {}  # In-memory store for demo
        
    async def retrieve_context(self, query: RAGQuery) -> RetrievedContext:
        """Retrieve relevant context from multiple data sources"""
        start_time = datetime.utcnow()
        
        try:
            # Calculate time window
            end_time = datetime.utcnow()
            start_time_window = end_time - timedelta(hours=query.time_window_hours)
            
            # Initialize context containers
            network_data = []
            threat_alerts = []
            siem_events = []
            threat_intelligence = []
            sources_queried = []
            
            # Query network data (mock implementation)
            if query.query_type in [QueryType.NETWORK_INVESTIGATION, QueryType.THREAT_ANALYSIS]:
                network_data = await self._query_network_data(query, start_time_window, end_time)
                sources_queried.append("network_packets")
            
            # Query threat alerts
            if query.query_type in [QueryType.THREAT_ANALYSIS, QueryType.INCIDENT_RESPONSE]:
                threat_alerts = await self._query_threat_alerts(query, start_time_window, end_time)
                sources_queried.append("threat_alerts")
            
            # Query SIEM events
            if query.query_type != QueryType.GENERAL_SECURITY:
                siem_events = await self._query_siem_events(query, start_time_window, end_time)
                sources_queried.append("siem_events")
            
            # Query threat intelligence
            threat_intelligence = await self._query_threat_intelligence(query)
            sources_queried.append("threat_intelligence")
            
            return RetrievedContext(
                network_data=network_data,
                threat_alerts=threat_alerts,
                siem_events=siem_events,
                threat_intelligence=threat_intelligence,
                retrieval_timestamp=datetime.utcnow(),
                sources_queried=sources_queried,
                total_records=len(network_data) + len(threat_alerts) + len(siem_events) + len(threat_intelligence),
                time_range={"start": start_time_window, "end": end_time}
            )
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return RetrievedContext(
                retrieval_timestamp=datetime.utcnow(),
                sources_queried=[],
                total_records=0,
                time_range={"start": start_time_window, "end": end_time}
            )
    
    async def _query_network_data(self, query: RAGQuery, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query network packet data (mock implementation)"""
        # TODO: Implement actual TimescaleDB query
        return [
            {
                "timestamp": "2025-07-23T10:30:00Z",
                "source_ip": "192.168.1.100",
                "destination_ip": "203.0.113.45",
                "protocol": "TCP",
                "payload_size": 1024,
                "suspicious_indicator": "unusual_port_scan"
            }
        ]
    
    async def _query_threat_alerts(self, query: RAGQuery, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query threat alerts (mock implementation)"""
        # TODO: Implement actual database query
        return [
            {
                "id": str(uuid4()),
                "timestamp": "2025-07-23T10:25:00Z",
                "threat_level": "high",
                "attack_type": "lateral_movement",
                "confidence_score": 0.87,
                "description": "Potential lateral movement detected from compromised host"
            }
        ]
    
    async def _query_siem_events(self, query: RAGQuery, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query SIEM events (mock implementation)"""
        # TODO: Implement actual SIEM integration
        return [
            {
                "event_id": "siem_001",
                "timestamp": "2025-07-23T10:20:00Z",
                "event_type": "authentication_failure",
                "severity": "medium",
                "source_ip": "192.168.1.100",
                "description": "Multiple failed login attempts detected"
            }
        ]
    
    async def _query_threat_intelligence(self, query: RAGQuery) -> List[Dict[str, Any]]:
        """Query threat intelligence data (mock implementation)"""
        # TODO: Implement actual threat intelligence lookup
        return [
            {
                "ioc_type": "ip",
                "ioc_value": "203.0.113.45",
                "threat_type": "botnet_c2",
                "confidence": 0.92,
                "source": "threat_feed_alpha",
                "tags": ["malware", "c2", "botnet"]
            }
        ]


class GenAIAssistantService:
    """Main service for the GenAI assistant with RAG capabilities"""
    
    def __init__(self):
        self.llm_service = MixtralLLMService()
        self.rag_service = RAGService()
        self.audit_service = AuditLoggerService()
        self.conversation_contexts = {}  # In-memory session storage
        
    async def process_query(self, query: AssistantQuery) -> AssistantResponse:
        """Process a user query with RAG-enhanced context"""
        start_time = datetime.utcnow()
        
        try:
            # Update conversation context
            context = await self._get_or_create_context(query.session_id, query.user_id)
            
            # Retrieve relevant context using RAG
            rag_query = RAGQuery(
                query_text=query.query_text,
                query_type=query.query_type,
                time_window_hours=query.time_window_hours,
                max_results=100
            )
            
            retrieved_context = await self.rag_service.retrieve_context(rag_query)
            
            # Generate enhanced prompt with context
            enhanced_prompt = await self._create_enhanced_prompt(query, retrieved_context)
            
            # Generate response using Mixtral
            llm_response = await self.llm_service.generate_response(
                prompt=enhanced_prompt,
                max_tokens=query.max_tokens,
                temperature=query.temperature,
                system_prompt=self._get_system_prompt(query.query_type)
            )
            
            # Extract insights and recommendations
            insights, actions, mitre_techniques = await self._extract_insights(llm_response["response"])
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create response
            response = AssistantResponse(
                query_id=query.query_id,
                session_id=query.session_id,
                response_text=llm_response["response"],
                confidence_score=0.85,  # TODO: Implement confidence scoring
                context_summary=self._create_context_summary(retrieved_context),
                sources_consulted=retrieved_context.sources_queried,
                retrieved_context=retrieved_context,
                key_insights=insights,
                recommended_actions=actions,
                mitre_techniques=mitre_techniques,
                processing_time_ms=processing_time,
                tokens_used=llm_response.get("tokens_used", 0),
                model_used=llm_response.get("model", "mixtral"),
                suggested_queries=await self._generate_follow_up_queries(query, llm_response["response"])
            )
            
            # Update conversation context
            await self._update_conversation_context(context, query, response)
            
            # Log the interaction
            await self.audit_service.log_event(
                user_id=query.user_id,
                action="genai_query",
                resource="assistant",
                details={
                    "query_type": query.query_type.value,
                    "processing_time_ms": processing_time,
                    "tokens_used": response.tokens_used,
                    "sources_consulted": response.sources_consulted
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AssistantResponse(
                query_id=query.query_id,
                session_id=query.session_id,
                response_text="I apologize, but I encountered an error processing your request. Please try again.",
                confidence_score=0.0,
                context_summary="Error occurred during processing",
                sources_consulted=[],
                processing_time_ms=processing_time,
                tokens_used=0,
                model_used="error"
            )
    
    async def generate_threat_narrative(self, request: ThreatNarrativeRequest) -> ThreatNarrative:
        """Generate detailed threat narrative for security incidents"""
        start_time = datetime.utcnow()
        
        try:
            # Create specialized prompt for threat narrative
            prompt = self._create_threat_narrative_prompt(request)
            
            # Generate narrative using Mixtral
            llm_response = await self.llm_service.generate_response(
                prompt=prompt,
                system_prompt=self._get_threat_analysis_system_prompt(),
                temperature=0.2,  # Lower temperature for more factual responses
                max_tokens=3000
            )
            
            # Parse response for structured data
            narrative_data = await self._parse_threat_narrative(llm_response["response"])
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ThreatNarrative(
                threat_description=narrative_data.get("description", llm_response["response"]),
                attack_vector=narrative_data.get("attack_vector", "Unknown"),
                confidence_score=request.confidence_threshold,
                mitre_tactics=narrative_data.get("mitre_tactics", []),
                mitre_techniques=narrative_data.get("mitre_techniques", []),
                mitre_technique_ids=narrative_data.get("mitre_technique_ids", []),
                evidence_summary=narrative_data.get("evidence", ""),
                timeline_analysis=narrative_data.get("timeline", ""),
                impact_assessment=narrative_data.get("impact", ""),
                immediate_actions=narrative_data.get("immediate_actions", []),
                investigation_steps=narrative_data.get("investigation_steps", []),
                preventive_measures=narrative_data.get("preventive_measures", []),
                model_version="mixtral-8x7b-instruct",
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating threat narrative: {e}")
            return ThreatNarrative(
                threat_description="Unable to generate threat narrative due to processing error.",
                attack_vector="Unknown",
                confidence_score=0.0,
                evidence_summary="No evidence available due to error.",
                timeline_analysis="No timeline analysis available due to error.",
                impact_assessment="No impact assessment available due to error.",
                model_version="error",
                processing_time_ms=0.0
            )
    
    async def explain_autoencoder_threat(self, threat_alert: Dict[str, Any]) -> ThreatNarrative:
        """Generate explanation for autoencoder-detected threats"""
        start_time = datetime.utcnow()
        
        try:
            # Convert threat alert to ThreatNarrativeRequest format
            request = ThreatNarrativeRequest(
                threat_data={
                    "threat_level": threat_alert.get("threat_level", "unknown"),
                    "attack_type": threat_alert.get("attack_type", "unknown"),
                    "confidence_score": threat_alert.get("confidence_score", 0.0),
                    "detection_method": "Autoencoder-based anomaly detection"
                },
                anomaly_scores=[a.get("anomaly_score", 0.0) for a in threat_alert.get("anomaly_reports", [])],
                network_context={
                    "source_ips": list(set(p.get("source_ip") for p in threat_alert.get("source_packets", []))),
                    "destination_ips": list(set(p.get("destination_ip") for p in threat_alert.get("source_packets", []))),
                    "protocols": list(set(p.get("protocol") for p in threat_alert.get("source_packets", []))),
                    "packet_count": len(threat_alert.get("source_packets", [])),
                    "time_span": threat_alert.get("time_span", 0.0)
                },
                attack_indicators=[
                    threat_alert.get("threat_description", ""),
                    threat_alert.get("attack_vector", "")
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
                attack_vector="Unknown",
                confidence_score=0.0,
                evidence_summary="No evidence available due to error.",
                timeline_analysis="No timeline analysis available due to error.",
                impact_assessment="No impact assessment available due to error.",
                model_version="error",
                processing_time_ms=0.0
            )
    
    def _get_system_prompt(self, query_type: QueryType) -> str:
        """Get system prompt based on query type"""
        base_prompt = """You are a cybersecurity expert assistant with deep knowledge of network security, threat analysis, and incident response. You provide accurate, actionable insights based on real-time security data."""
        
        type_specific = {
            QueryType.THREAT_ANALYSIS: " Focus on analyzing threats, identifying attack patterns, and providing detailed technical analysis with MITRE ATT&CK references.",
            QueryType.NETWORK_INVESTIGATION: " Specialize in network traffic analysis, identifying suspicious patterns, and correlating network events.",
            QueryType.INCIDENT_RESPONSE: " Provide step-by-step incident response guidance, containment strategies, and recovery procedures.",
            QueryType.MITRE_LOOKUP: " Reference the MITRE ATT&CK framework extensively, mapping techniques and tactics to observed behaviors.",
            QueryType.TREND_ANALYSIS: " Focus on identifying trends, patterns over time, and predictive analysis of security events."
        }
        
        return base_prompt + type_specific.get(query_type, "")
    
    def _get_threat_analysis_system_prompt(self) -> str:
        """Get system prompt for threat analysis"""
        return """You are an expert cybersecurity threat analyst. Analyze the provided security data and generate a comprehensive threat narrative that includes:

1. Detailed threat description with technical analysis
2. Attack vector identification and progression
3. MITRE ATT&CK technique mapping
4. Evidence summary and timeline
5. Impact assessment
6. Immediate response actions
7. Investigation steps
8. Preventive measures

Be precise, factual, and provide actionable intelligence. Reference specific indicators and evidence from the provided data."""
    
    async def _get_or_create_context(self, session_id: str, user_id: str) -> ConversationContext:
        """Get or create conversation context"""
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                last_query_timestamp=datetime.utcnow()
            )
        return self.conversation_contexts[session_id]
    
    async def _create_enhanced_prompt(self, query: AssistantQuery, context: RetrievedContext) -> str:
        """Create enhanced prompt with retrieved context"""
        prompt_parts = [
            f"User Query: {query.query_text}",
            "",
            "Context Information:"
        ]
        
        # Add network data context
        if context.network_data:
            prompt_parts.append("Network Traffic Data:")
            for item in context.network_data[:5]:  # Limit to prevent prompt overflow
                prompt_parts.append(f"- {json.dumps(item, default=str)}")
            prompt_parts.append("")
        
        # Add threat alerts context
        if context.threat_alerts:
            prompt_parts.append("Recent Threat Alerts:")
            for alert in context.threat_alerts[:3]:
                prompt_parts.append(f"- {json.dumps(alert, default=str)}")
            prompt_parts.append("")
        
        # Add SIEM events context
        if context.siem_events:
            prompt_parts.append("SIEM Events:")
            for event in context.siem_events[:3]:
                prompt_parts.append(f"- {json.dumps(event, default=str)}")
            prompt_parts.append("")
        
        # Add threat intelligence context
        if context.threat_intelligence:
            prompt_parts.append("Threat Intelligence:")
            for intel in context.threat_intelligence[:3]:
                prompt_parts.append(f"- {json.dumps(intel, default=str)}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Based on the above context and your cybersecurity expertise, provide a comprehensive analysis and answer to the user's query.",
            "Include specific references to the data provided and actionable recommendations."
        ])
        
        return "\n".join(prompt_parts)
    
    def _create_context_summary(self, context: RetrievedContext) -> str:
        """Create a summary of the retrieved context"""
        summary_parts = []
        
        if context.network_data:
            summary_parts.append(f"{len(context.network_data)} network events")
        if context.threat_alerts:
            summary_parts.append(f"{len(context.threat_alerts)} threat alerts")
        if context.siem_events:
            summary_parts.append(f"{len(context.siem_events)} SIEM events")
        if context.threat_intelligence:
            summary_parts.append(f"{len(context.threat_intelligence)} threat intelligence indicators")
        
        if not summary_parts:
            return "No specific context data available"
        
        return f"Analyzed {', '.join(summary_parts)} from the last {context.time_range['end'] - context.time_range['start']} hours"
    
    async def _extract_insights(self, response_text: str) -> tuple:
        """Extract key insights, actions, and MITRE techniques from response"""
        # TODO: Implement NLP-based extraction
        insights = ["Analysis based on real-time security data"]
        actions = ["Continue monitoring", "Investigate further if needed"]
        mitre_techniques = []
        
        # Simple keyword-based extraction (replace with proper NLP)
        if "T1" in response_text:
            import re
            mitre_matches = re.findall(r'T\d{4}(?:\.\d{3})?', response_text)
            mitre_techniques.extend(mitre_matches)
        
        return insights, actions, mitre_techniques
    
    async def _generate_follow_up_queries(self, query: AssistantQuery, response: str) -> List[str]:
        """Generate suggested follow-up queries"""
        suggestions = [
            "Can you provide more details about the network traffic patterns?",
            "What are the recommended mitigation steps?",
            "Are there any related threats I should be aware of?"
        ]
        
        # TODO: Implement context-aware suggestion generation
        return suggestions[:3]
    
    async def _update_conversation_context(self, context: ConversationContext, query: AssistantQuery, response: AssistantResponse):
        """Update conversation context with new interaction"""
        context.conversation_history.append({
            "timestamp": query.timestamp.isoformat(),
            "query": query.query_text,
            "response": response.response_text[:200] + "..." if len(response.response_text) > 200 else response.response_text,
            "query_type": query.query_type.value
        })
        
        # Keep only last 10 interactions
        context.conversation_history = context.conversation_history[-10:]
        context.last_query_timestamp = datetime.utcnow()
    
    def _create_threat_narrative_prompt(self, request: ThreatNarrativeRequest) -> str:
        """Create prompt for threat narrative generation"""
        prompt = f"""
Analyze the following security incident data and generate a comprehensive threat narrative:

Threat Data:
{json.dumps(request.threat_data, indent=2, default=str)}

Anomaly Scores: {request.anomaly_scores}

Network Context:
{json.dumps(request.network_context, indent=2, default=str)}

Attack Indicators: {', '.join(request.attack_indicators)}

Generate a detailed analysis including:
1. Threat description and technical details
2. Attack vector and progression
3. MITRE ATT&CK technique mapping (if applicable)
4. Evidence summary and timeline
5. Impact assessment
6. Immediate response actions
7. Investigation steps
8. Preventive measures

Format your response clearly with distinct sections for each component.
"""
        return prompt
    
    async def _parse_threat_narrative(self, narrative_text: str) -> Dict[str, Any]:
        """Parse the generated narrative into structured data"""
        # TODO: Implement proper parsing of the narrative response
        # For now, return the raw text in appropriate fields
        return {
            "description": narrative_text,
            "attack_vector": "To be extracted from narrative",
            "evidence": "Evidence details from narrative",
            "timeline": "Timeline analysis from narrative",
            "impact": "Impact assessment from narrative",
            "immediate_actions": ["Action 1", "Action 2"],
            "investigation_steps": ["Step 1", "Step 2"],
            "preventive_measures": ["Measure 1", "Measure 2"],
            "mitre_tactics": [],
            "mitre_techniques": [],
            "mitre_technique_ids": []
        }
