"""
GenAI Assistant Services

Modern async services for context-aware threat analysis using Mixtral LLM.
Enhanced with Pydantic v2, comprehensive error handling, and performance optimizations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import uuid4
import httpx
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
import re

from .models import (
    AssistantQuery, 
    AssistantResponse, 
    ConversationContext,
    RetrievedContext,
    RAGQuery,
    ThreatNarrative,
    ThreatNarrativeRequest,
    QueryType,
    KnowledgeBase,
    ModelTrainingData,
    HealthResponse,
    ErrorResponse
)

from .schemas import (
    QueryRequest,
    QueryResponse,
    ThreatAnalysisRequest,
    ThreatAnalysisResponse,
    MetricsResponse
)

# Mock audit logger for now
logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service errors"""
    def __init__(self, message: str, error_code: str = "SERVICE_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class LLMError(ServiceError):
    """LLM service specific errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "LLM_ERROR", details)


class RAGError(ServiceError):
    """RAG service specific errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "RAG_ERROR", details)


class MixtralLLMService:
    """Enhanced service for interacting with local Mixtral LLM"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_name = "mixtral:8x7b-instruct"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.request_count = 0
        self.total_tokens = 0
        self.avg_response_time = 0.0
        
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 2048,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using Mixtral LLM with enhanced error handling"""
        start_time = time.time()
        
        try:
            # Validate inputs
            if not prompt or len(prompt.strip()) == 0:
                raise LLMError("Prompt cannot be empty")
            
            if len(prompt) > 50000:
                raise LLMError("Prompt too long", {"prompt_length": len(prompt)})
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt or "You are a cybersecurity expert assistant.",
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                },
                "stream": False
            }
            
            # Make request to Ollama API
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise LLMError(
                    f"LLM API request failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
            
            result = response.json()
            
            # Extract response
            generated_text = result.get("response", "")
            if not generated_text:
                raise LLMError("Empty response from LLM")
            
            # Calculate metrics
            processing_time = (time.time() - start_time) * 1000
            tokens_used = len(generated_text.split())  # Approximate token count
            
            # Update service metrics
            self.request_count += 1
            self.total_tokens += tokens_used
            self.avg_response_time = (self.avg_response_time * (self.request_count - 1) + processing_time) / self.request_count
            
            return {
                "response": generated_text,
                "tokens_used": tokens_used,
                "processing_time_ms": processing_time,
                "model": self.model_name,
                "success": True
            }
            
        except httpx.RequestError as e:
            raise LLMError(f"Network error communicating with LLM: {str(e)}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in LLM service: {e}")
            raise LLMError(f"Unexpected LLM error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if LLM service is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=10.0)
            return response.status_code == 200
        except:
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get LLM service metrics"""
        return {
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "avg_response_time_ms": self.avg_response_time,
            "model_name": self.model_name,
            "base_url": self.base_url
        }


class RAGService:
    """Enhanced Retrieval-Augmented Generation service with caching and optimization"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base: Dict[str, KnowledgeBase] = {}
        self.embedding_cache: Dict[str, List[float]] = {}
        self.query_cache: Dict[str, RetrievedContext] = {}
        self.cache_ttl = 3600  # 1 hour
        
    async def retrieve_context(self, query: RAGQuery) -> RetrievedContext:
        """Retrieve relevant context from multiple data sources with caching"""
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(query)
            
            # Check cache first
            if cache_key in self.query_cache:
                cached_result = self.query_cache[cache_key]
                # Check if cache is still valid
                if (datetime.utcnow() - cached_result.retrieval_timestamp).total_seconds() < self.cache_ttl:
                    logger.info(f"Cache hit for RAG query: {query.query_text[:50]}...")
                    return cached_result
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time_data = end_time - timedelta(hours=query.time_window_hours)
            
            # Retrieve data from various sources concurrently
            tasks = []
            
            if "network_data" not in query.filters.get("exclude_sources", []):
                tasks.append(self._query_network_data(query, start_time_data, end_time))
            
            if "threat_alerts" not in query.filters.get("exclude_sources", []):
                tasks.append(self._query_threat_alerts(query, start_time_data, end_time))
            
            if "siem_events" not in query.filters.get("exclude_sources", []):
                tasks.append(self._query_siem_events(query, start_time_data, end_time))
            
            if "threat_intelligence" not in query.filters.get("exclude_sources", []):
                tasks.append(self._query_threat_intelligence(query))
            
            # Execute all queries concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            network_data = results[0] if len(results) > 0 and not isinstance(results[0], Exception) else []
            threat_alerts = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else []
            siem_events = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []
            threat_intelligence = results[3] if len(results) > 3 and not isinstance(results[3], Exception) else []
            
            # Create retrieved context
            context = RetrievedContext(
                network_data=network_data,
                threat_alerts=threat_alerts,
                siem_events=siem_events,
                threat_intelligence=threat_intelligence,
                retrieval_timestamp=datetime.utcnow(),
                sources_queried=["network_data", "threat_alerts", "siem_events", "threat_intelligence"],
                total_records=len(network_data) + len(threat_alerts) + len(siem_events) + len(threat_intelligence),
                time_range={"start": start_time_data, "end": end_time}
            )
            
            # Cache the result
            self.query_cache[cache_key] = context
            
            # Clean up old cache entries periodically
            await self._cleanup_cache()
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving RAG context: {e}")
            raise RAGError(f"Failed to retrieve context: {str(e)}")
    
    async def _query_network_data(self, query: RAGQuery, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query network packet data with enhanced filtering"""
        # Mock implementation - replace with actual database queries
        mock_data = [
            {
                "id": str(uuid4()),
                "timestamp": (start_time + timedelta(minutes=i*10)).isoformat(),
                "source_ip": f"192.168.1.{100 + i}",
                "destination_ip": f"203.0.113.{45 + i}",
                "protocol": "TCP",
                "port": 443 + i,
                "payload_size": 1024 + i*100,
                "flags": ["SYN", "ACK"] if i % 2 == 0 else ["PSH", "ACK"],
                "suspicious_indicator": "port_scan" if i % 3 == 0 else None
            }
            for i in range(min(10, query.max_results // 4))
        ]
        
        # Apply filters
        if "source_ip" in query.filters:
            mock_data = [d for d in mock_data if d["source_ip"] in query.filters["source_ip"]]
        
        if "protocol" in query.filters:
            mock_data = [d for d in mock_data if d["protocol"] == query.filters["protocol"]]
        
        return mock_data
    
    async def _query_threat_alerts(self, query: RAGQuery, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query threat detection alerts with enhanced filtering"""
        # Mock implementation
        mock_alerts = [
            {
                "id": str(uuid4()),
                "timestamp": (start_time + timedelta(hours=i)).isoformat(),
                "threat_level": ["low", "medium", "high", "critical"][i % 4],
                "attack_type": ["malware", "phishing", "lateral_movement", "data_exfiltration"][i % 4],
                "confidence_score": 0.7 + (i * 0.05),
                "source_ip": f"10.0.1.{100 + i}",
                "target_asset": f"server_{i+1}",
                "description": f"Potential {['malware', 'phishing', 'lateral_movement', 'data_exfiltration'][i % 4]} detected",
                "mitre_technique": [f"T{1000 + i:04d}" for i in range(3)]
            }
            for i in range(min(8, query.max_results // 4))
        ]
        
        # Apply filters
        if "threat_level" in query.filters:
            mock_alerts = [a for a in mock_alerts if a["threat_level"] == query.filters["threat_level"]]
        
        if "attack_type" in query.filters:
            mock_alerts = [a for a in mock_alerts if a["attack_type"] in query.filters["attack_type"]]
        
        return mock_alerts
    
    async def _query_siem_events(self, query: RAGQuery, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query SIEM events with enhanced filtering"""
        # Mock implementation
        mock_events = [
            {
                "id": str(uuid4()),
                "timestamp": (start_time + timedelta(minutes=i*30)).isoformat(),
                "event_type": ["login_failure", "privilege_escalation", "file_access", "network_connection"][i % 4],
                "severity": ["info", "warning", "error", "critical"][i % 4],
                "source": f"host_{i+1}",
                "user": f"user_{i+1}",
                "description": f"SIEM event: {['login_failure', 'privilege_escalation', 'file_access', 'network_connection'][i % 4]}",
                "raw_log": f"Event log data for event {i+1}"
            }
            for i in range(min(12, query.max_results // 3))
        ]
        
        # Apply filters
        if "severity" in query.filters:
            mock_events = [e for e in mock_events if e["severity"] == query.filters["severity"]]
        
        return mock_events
    
    async def _query_threat_intelligence(self, query: RAGQuery) -> List[Dict[str, Any]]:
        """Query threat intelligence feeds"""
        # Mock implementation
        mock_intel = [
            {
                "id": str(uuid4()),
                "ioc_type": ["ip", "domain", "hash", "url"][i % 4],
                "ioc_value": f"threat_indicator_{i+1}",
                "threat_type": ["malware", "botnet", "apt", "ransomware"][i % 4],
                "confidence": 0.8 + (i * 0.02),
                "source": f"threat_feed_{i+1}",
                "tags": ["malware", "c2", "apt"] if i % 2 == 0 else ["phishing", "credential_theft"],
                "first_seen": (datetime.utcnow() - timedelta(days=i+1)).isoformat(),
                "last_seen": datetime.utcnow().isoformat()
            }
            for i in range(min(5, query.max_results // 8))
        ]
        
        return mock_intel
    
    def _generate_cache_key(self, query: RAGQuery) -> str:
        """Generate cache key for query"""
        key_data = {
            "query_text": query.query_text,
            "query_type": query.query_type.value,
            "filters": query.filters,
            "time_window": query.time_window_hours,
            "max_results": query.max_results
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, context in self.query_cache.items():
            if (current_time - context.retrieval_timestamp).total_seconds() > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.query_cache[key]
    
    async def add_to_knowledge_base(self, entry: KnowledgeBase):
        """Add entry to knowledge base with embedding"""
        try:
            # Generate embedding if not provided
            if entry.embedding is None:
                embedding = self.embedding_model.encode(entry.content)
                entry.embedding = embedding.tolist()
            
            self.knowledge_base[entry.id] = entry
            logger.info(f"Added knowledge base entry: {entry.id}")
            
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {e}")
            raise RAGError(f"Failed to add knowledge base entry: {str(e)}")
    
    async def search_knowledge_base(self, query_text: str, max_results: int = 10) -> List[KnowledgeBase]:
        """Search knowledge base using semantic similarity"""
        try:
            if not self.knowledge_base:
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query_text)
            
            # Calculate similarities
            similarities = []
            for entry_id, entry in self.knowledge_base.items():
                if entry.embedding:
                    similarity = np.dot(query_embedding, entry.embedding)
                    similarities.append((similarity, entry))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [entry for _, entry in similarities[:max_results]]
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
