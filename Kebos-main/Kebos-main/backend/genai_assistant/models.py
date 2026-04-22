"""
GenAI Assistant Models

Pydantic v2 models for the context-aware GenAI assistant with RAG architecture.
Enhanced with modern validation, type safety, and performance optimizations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from enum import Enum
import uuid
import re


class QueryType(str, Enum):
    """Types of queries the assistant can handle"""
    THREAT_ANALYSIS = "threat_analysis"
    NETWORK_INVESTIGATION = "network_investigation"
    INCIDENT_RESPONSE = "incident_response"
    GENERAL_SECURITY = "general_security"
    MITRE_LOOKUP = "mitre_lookup"
    TREND_ANALYSIS = "trend_analysis"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    COMPLIANCE_CHECK = "compliance_check"


class ConversationContext(BaseModel):
    """Context for maintaining conversation state"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    session_id: str = Field(..., min_length=1, max_length=100, description="Unique session identifier")
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, max_length=100)
    current_topic: Optional[str] = Field(default=None, max_length=200)
    active_investigation: Optional[str] = Field(default=None, max_length=100)
    last_query_timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('session_id', 'user_id')
    @classmethod
    def validate_ids(cls, v: str) -> str:
        """Validate ID format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('IDs must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @field_validator('conversation_history')
    @classmethod
    def validate_history_items(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate conversation history entries"""
        for item in v:
            if not isinstance(item, dict) or 'timestamp' not in item or 'message' not in item:
                raise ValueError('Each history item must be a dict with timestamp and message')
        return v


class AssistantQuery(BaseModel):
    """Query structure for the GenAI assistant"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query_id: str = Field(default_factory=lambda: f"q_{uuid.uuid4().hex[:8]}")
    session_id: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=100)
    query_text: str = Field(..., min_length=1, max_length=8000, description="User query text")
    query_type: QueryType
    
    # Context enrichment flags
    include_network_data: bool = Field(default=True, description="Include network packet data")
    include_threat_alerts: bool = Field(default=True, description="Include threat detection alerts")
    include_siem_events: bool = Field(default=True, description="Include SIEM events")
    time_window_hours: int = Field(default=24, ge=1, le=168, description="Time window in hours (1-168)")
    
    # Specific filters
    ip_addresses: Optional[List[str]] = Field(default=None, max_length=50)
    asset_names: Optional[List[str]] = Field(default=None, max_length=20)
    threat_types: Optional[List[str]] = Field(default=None, max_length=10)
    
    # LLM parameters
    max_tokens: int = Field(default=2048, ge=100, le=8192, description="Maximum response tokens")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="LLM temperature")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('query_text')
    @classmethod
    def validate_query_text(cls, v: str) -> str:
        """Validate and clean query text"""
        if not v or v.isspace():
            raise ValueError('Query text cannot be empty or whitespace only')
        
        # Remove potential malicious patterns
        forbidden_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        v_lower = v.lower()
        for pattern in forbidden_patterns:
            if pattern in v_lower:
                raise ValueError(f'Query contains forbidden pattern: {pattern}')
        
        return v.strip()
    
    @field_validator('ip_addresses')
    @classmethod
    def validate_ip_addresses(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate IP address format"""
        if v is None:
            return v
        
        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        
        validated_ips = []
        for ip in v:
            if ip_pattern.match(ip):
                validated_ips.append(ip)
            else:
                raise ValueError(f'Invalid IP address format: {ip}')
        
        return validated_ips


class RetrievedContext(BaseModel):
    """Context retrieved from various data sources"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        extra='forbid'
    )
    
    network_data: List[Dict[str, Any]] = Field(default_factory=list, max_length=1000)
    threat_alerts: List[Dict[str, Any]] = Field(default_factory=list, max_length=500)
    siem_events: List[Dict[str, Any]] = Field(default_factory=list, max_length=1000)
    threat_intelligence: List[Dict[str, Any]] = Field(default_factory=list, max_length=200)
    
    # Metadata
    retrieval_timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources_queried: List[str] = Field(default_factory=list, max_length=20)
    total_records: int = Field(default=0, ge=0, le=10000)
    time_range: Dict[str, datetime] = Field(default_factory=dict)
    
    @field_validator('sources_queried')
    @classmethod
    def validate_sources(cls, v: List[str]) -> List[str]:
        """Validate data source names"""
        valid_sources = {
            'network_data', 'threat_alerts', 'siem_events', 
            'threat_intelligence', 'mitre_attack', 'vulnerability_db'
        }
        
        for source in v:
            if source not in valid_sources:
                raise ValueError(f'Invalid data source: {source}')
        
        return v


class AssistantResponse(BaseModel):
    """Response from the GenAI assistant"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        extra='forbid'
    )
    
    query_id: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    response_id: str = Field(default_factory=lambda: f"r_{uuid.uuid4().hex[:8]}")
    
    # Main response
    response_text: str = Field(..., min_length=1, max_length=16000, description="Generated response text")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Response confidence score")
    
    # Context used
    context_summary: str = Field(..., max_length=2000, description="Summary of context used")
    sources_consulted: List[str] = Field(default_factory=list, max_length=50)
    retrieved_context: Optional[RetrievedContext] = None
    
    # Analysis insights
    key_insights: List[str] = Field(default_factory=list, max_length=20)
    recommended_actions: List[str] = Field(default_factory=list, max_length=20)
    mitre_techniques: List[str] = Field(default_factory=list, max_length=50)
    related_alerts: List[str] = Field(default_factory=list, max_length=30)
    
    # Response metadata
    processing_time_ms: float = Field(..., ge=0.0, le=300000.0, description="Processing time in milliseconds")
    tokens_used: int = Field(..., ge=0, le=50000, description="LLM tokens consumed")
    model_used: str = Field(..., min_length=1, max_length=100, description="LLM model used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Follow-up suggestions
    suggested_queries: List[str] = Field(default_factory=list, max_length=10)
    investigation_leads: List[str] = Field(default_factory=list, max_length=15)
    
    @field_validator('response_text')
    @classmethod
    def validate_response_text(cls, v: str) -> str:
        """Validate response text quality"""
        if not v or v.isspace():
            raise ValueError('Response text cannot be empty')
        
        # Check for potential harmful content
        harmful_patterns = ['<script>', 'javascript:', 'data:', 'file://']
        v_lower = v.lower()
        for pattern in harmful_patterns:
            if pattern in v_lower:
                raise ValueError(f'Response contains potentially harmful content: {pattern}')
        
        return v.strip()
    
    @field_validator('mitre_techniques')
    @classmethod
    def validate_mitre_techniques(cls, v: List[str]) -> List[str]:
        """Validate MITRE ATT&CK technique format"""
        mitre_pattern = re.compile(r'^T\d{4}(?:\.\d{3})?$')
        
        validated_techniques = []
        for technique in v:
            if mitre_pattern.match(technique):
                validated_techniques.append(technique.upper())
            else:
                # Allow descriptive names too, but validate them
                if len(technique) > 100:
                    raise ValueError(f'MITRE technique name too long: {technique}')
                validated_techniques.append(technique)
        
        return validated_techniques


class RAGQuery(BaseModel):
    """Query structure for RAG (Retrieval-Augmented Generation)"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query_text: str = Field(..., min_length=1, max_length=4000, description="RAG query text")
    query_type: QueryType
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    time_window_hours: int = Field(default=24, ge=1, le=8760, description="Time window for data retrieval")
    max_results: int = Field(default=100, ge=10, le=1000, description="Maximum results to retrieve")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold for matching")
    
    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate query filters"""
        allowed_filter_keys = {
            'threat_level', 'source_ip', 'destination_ip', 'protocol', 
            'severity', 'attack_type', 'time_range', 'asset_id'
        }
        
        for key in v.keys():
            if key not in allowed_filter_keys:
                raise ValueError(f'Invalid filter key: {key}')
        
        return v


class KnowledgeBase(BaseModel):
    """Knowledge base entry for RAG"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    id: str = Field(..., min_length=1, max_length=100, description="Unique knowledge base entry ID")
    title: str = Field(..., min_length=1, max_length=500, description="Entry title")
    content: str = Field(..., min_length=1, max_length=50000, description="Entry content")
    source_type: str = Field(..., description="Type of source data")
    source_id: str = Field(..., min_length=1, max_length=100, description="Source identifier")
    embedding: Optional[List[float]] = Field(default=None, max_length=1536, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        """Validate source type"""
        valid_types = {
            'threat_alert', 'siem_event', 'network_data', 'vulnerability_report',
            'incident_report', 'threat_intelligence', 'mitre_attack', 'cve_data'
        }
        
        if v not in valid_types:
            raise ValueError(f'Invalid source type: {v}. Must be one of {valid_types}')
        
        return v
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate embedding dimensions and values"""
        if v is None:
            return v
        
        if not all(isinstance(x, (int, float)) for x in v):
            raise ValueError('Embedding must contain only numeric values')
        
        if not all(-1.0 <= x <= 1.0 for x in v):
            raise ValueError('Embedding values must be between -1.0 and 1.0')
        
        return v


class ModelTrainingData(BaseModel):
    """Structure for model training feedback"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query_id: str = Field(..., min_length=1, max_length=100)
    response_id: str = Field(..., min_length=1, max_length=100)
    user_feedback: str = Field(..., description="User feedback type")
    feedback_details: Optional[str] = Field(default=None, max_length=2000)
    correct_answer: Optional[str] = Field(default=None, max_length=8000)
    improvement_suggestions: List[str] = Field(default_factory=list, max_length=10)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('user_feedback')
    @classmethod
    def validate_user_feedback(cls, v: str) -> str:
        """Validate feedback type"""
        valid_feedback = {'helpful', 'not_helpful', 'partially_helpful', 'incorrect', 'excellent'}
        
        if v not in valid_feedback:
            raise ValueError(f'Invalid feedback type: {v}. Must be one of {valid_feedback}')
        
        return v


class ThreatNarrativeRequest(BaseModel):
    """Request for generating threat narratives"""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    threat_data: Dict[str, Any] = Field(..., description="Raw threat detection data")
    anomaly_scores: List[float] = Field(..., max_length=100, description="Anomaly detection scores")
    network_context: Dict[str, Any] = Field(..., description="Network context information")
    attack_indicators: List[str] = Field(..., max_length=50, description="Attack indicators")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold")
    include_mitre_mapping: bool = Field(default=True, description="Include MITRE ATT&CK mapping")
    generate_recommendations: bool = Field(default=True, description="Generate recommendations")
    
    @field_validator('anomaly_scores')
    @classmethod
    def validate_anomaly_scores(cls, v: List[float]) -> List[float]:
        """Validate anomaly scores range"""
        for score in v:
            if not 0.0 <= score <= 1.0:
                raise ValueError(f'Anomaly score must be between 0.0 and 1.0, got: {score}')
        
        return v
    
    @field_validator('attack_indicators')
    @classmethod
    def validate_attack_indicators(cls, v: List[str]) -> List[str]:
        """Validate attack indicators format"""
        validated_indicators = []
        for indicator in v:
            if len(indicator.strip()) == 0:
                continue
            if len(indicator) > 500:
                raise ValueError(f'Attack indicator too long: {indicator[:50]}...')
            validated_indicators.append(indicator.strip())
        
        return validated_indicators


class ThreatNarrative(BaseModel):
    """Generated threat narrative response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        extra='forbid'
    )
    
    narrative_id: str = Field(default_factory=lambda: f"tn_{uuid.uuid4().hex[:8]}")
    threat_description: str = Field(..., min_length=1, max_length=10000, description="Detailed threat description")
    attack_vector: str = Field(..., min_length=1, max_length=2000, description="Attack vector analysis")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Narrative confidence score")
    
    # MITRE ATT&CK mapping
    mitre_tactics: List[str] = Field(default_factory=list, max_length=20, description="MITRE ATT&CK tactics")
    mitre_techniques: List[str] = Field(default_factory=list, max_length=50, description="MITRE ATT&CK techniques")
    mitre_technique_ids: List[str] = Field(default_factory=list, max_length=50, description="MITRE technique IDs")
    
    # Analysis details
    evidence_summary: str = Field(..., min_length=1, max_length=5000, description="Evidence summary")
    timeline_analysis: str = Field(..., min_length=1, max_length=5000, description="Timeline analysis")
    impact_assessment: str = Field(..., min_length=1, max_length=5000, description="Impact assessment")
    
    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list, max_length=20, description="Immediate actions")
    investigation_steps: List[str] = Field(default_factory=list, max_length=30, description="Investigation steps")
    preventive_measures: List[str] = Field(default_factory=list, max_length=20, description="Preventive measures")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(..., min_length=1, max_length=100, description="Model version used")
    processing_time_ms: float = Field(..., ge=0.0, le=300000.0, description="Processing time")
    
    @field_validator('mitre_technique_ids')
    @classmethod
    def validate_mitre_ids(cls, v: List[str]) -> List[str]:
        """Validate MITRE ATT&CK technique ID format"""
        mitre_pattern = re.compile(r'^T\d{4}(?:\.\d{3})?$')
        
        validated_ids = []
        for technique_id in v:
            if mitre_pattern.match(technique_id.upper()):
                validated_ids.append(technique_id.upper())
            else:
                raise ValueError(f'Invalid MITRE technique ID format: {technique_id}')
        
        return validated_ids
    
    @field_validator('immediate_actions', 'investigation_steps', 'preventive_measures')
    @classmethod
    def validate_action_lists(cls, v: List[str]) -> List[str]:
        """Validate action item lists"""
        validated_actions = []
        for action in v:
            action = action.strip()
            if len(action) == 0:
                continue
            if len(action) > 500:
                raise ValueError(f'Action item too long: {action[:50]}...')
            validated_actions.append(action)
        
        return validated_actions


# Response models for API endpoints
class HealthResponse(BaseModel):
    """Health check response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    service: str = "genai_assistant"
    status: str = Field(..., pattern=r'^(healthy|degraded|unhealthy)$')
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response model"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    error: str = Field(..., min_length=1, max_length=200)
    detail: Optional[str] = Field(default=None, max_length=1000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ChatMessage(BaseModel):
    """WebSocket chat message"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        extra='forbid'
    )
    
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    session_id: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=100)
    message_type: str = Field(..., pattern=r'^(user_message|assistant_response|system_notification)$')
    content: str = Field(..., min_length=1, max_length=8000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    """Service metrics response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True
    )
    
    total_queries: int = Field(default=0, ge=0, description="Total queries processed")
    successful_queries: int = Field(default=0, ge=0, description="Successful queries")
    failed_queries: int = Field(default=0, ge=0, description="Failed queries")
    avg_response_time_ms: float = Field(default=0.0, ge=0.0, description="Average response time")
    avg_confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Average confidence score")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Success rate")
    uptime_hours: float = Field(default=0.0, ge=0.0, description="Service uptime in hours")
    popular_query_types: List[str] = Field(default_factory=list, description="Popular query types")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Export all models
__all__ = [
    'QueryType',
    'ConversationContext', 
    'AssistantQuery',
    'RetrievedContext',
    'AssistantResponse',
    'RAGQuery',
    'KnowledgeBase',
    'ModelTrainingData',
    'ThreatNarrativeRequest',
    'ThreatNarrative',
    'HealthResponse',
    'MetricsResponse',
    'ErrorResponse',
    'ChatMessage'
]
