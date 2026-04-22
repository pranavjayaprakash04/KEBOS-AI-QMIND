"""
Enhanced GenAI Assistant Schemas with Modern Architecture
========================================================

Additional Pydantic v2 schemas for request/response validation and API contracts:
- Request/Response models
- Error handling schemas  
- Chat and feedback schemas
- Validation and type safety
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum
import uuid

from .models import QueryType, AssistantResponse, ThreatNarrative


class ServiceError(Exception):
    """Custom exception for service errors"""
    pass


class QueryRequest(BaseModel):
    """Standard query request schema"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query_text: str = Field(..., min_length=1, max_length=4000, description="User query")
    query_type: QueryType = Field(default=QueryType.GENERAL_SECURITY)
    session_id: Optional[str] = Field(default=None, max_length=100)
    
    # Context options
    include_network_data: bool = Field(default=True)
    include_threat_alerts: bool = Field(default=True) 
    include_siem_events: bool = Field(default=True)
    time_window_hours: int = Field(default=24, ge=1, le=168)
    
    # Filter options
    ip_addresses: Optional[List[str]] = Field(default=None, max_length=10)
    asset_names: Optional[List[str]] = Field(default=None, max_length=10)
    threat_types: Optional[List[str]] = Field(default=None, max_length=5)
    
    # LLM parameters
    max_tokens: int = Field(default=2048, ge=100, le=8192)
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    """Standard query response schema"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    success: bool = True
    response: AssistantResponse
    message: str = "Query processed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ThreatAnalysisRequest(BaseModel):
    """Threat analysis request schema"""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    threat_indicators: List[str] = Field(..., min_length=1, max_length=20)
    network_data: Optional[Dict[str, Any]] = None
    time_range: Optional[Dict[str, datetime]] = None
    analysis_type: str = Field(default="comprehensive", pattern=r'^(quick|comprehensive|detailed)$')
    include_recommendations: bool = Field(default=True)
    
    @field_validator('threat_indicators')
    @classmethod
    def validate_indicators(cls, v: List[str]) -> List[str]:
        """Validate threat indicators"""
        validated = []
        for indicator in v:
            indicator = indicator.strip()
            if len(indicator) == 0:
                continue
            if len(indicator) > 200:
                raise ValueError(f'Threat indicator too long: {indicator[:50]}...')
            validated.append(indicator)
        
        if len(validated) == 0:
            raise ValueError('At least one valid threat indicator is required')
        
        return validated


class ThreatAnalysisResponse(BaseModel):
    """Threat analysis response schema"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    success: bool = True
    narrative: ThreatNarrative
    analysis_summary: str = Field(..., max_length=1000)
    risk_score: float = Field(..., ge=0.0, le=10.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRequest(BaseModel):
    """User feedback request schema"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query_id: str = Field(..., min_length=1, max_length=100)
    response_id: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_type: str = Field(..., pattern=r'^(helpful|not_helpful|partially_helpful|incorrect|excellent)$')
    feedback_text: Optional[str] = Field(default=None, max_length=1000)
    suggested_improvement: Optional[str] = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    """Feedback submission response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    success: bool = True
    message: str = "Feedback submitted successfully"
    feedback_id: str = Field(default_factory=lambda: f"fb_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContextRequest(BaseModel):
    """Context retrieval request"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )
    
    session_id: str = Field(..., min_length=1, max_length=100)
    include_history: bool = Field(default=True)
    max_history_items: int = Field(default=50, ge=1, le=100)


class ContextResponse(BaseModel):
    """Context retrieval response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    success: bool = True
    session_id: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_topic: Optional[str] = None
    active_investigation: Optional[str] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    total_queries: int = Field(default=0, ge=0)


class ExplainRequest(BaseModel):
    """Autoencoder threat explanation request"""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    threat_alert: Dict[str, Any] = Field(..., description="Threat alert data")
    include_technical_details: bool = Field(default=True)
    include_mitigation: bool = Field(default=True)
    explanation_level: str = Field(default="technical", pattern=r'^(basic|technical|expert)$')


class ExplainResponse(BaseModel):
    """Autoencoder threat explanation response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    success: bool = True
    explanation: ThreatNarrative
    technical_summary: str = Field(..., max_length=2000)
    layman_summary: str = Field(..., max_length=1000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsResponse(BaseModel):
    """Service metrics response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    total_queries: int = Field(default=0, ge=0)
    avg_response_time_ms: float = Field(default=0.0, ge=0.0)
    avg_confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    popular_query_types: List[str] = Field(default_factory=list)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_hours: float = Field(default=0.0, ge=0.0)


class WebSocketMessage(BaseModel):
    """WebSocket message schema"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        extra='forbid'
    )
    
    type: str = Field(..., pattern=r'^(query|response|error|notification|ping|pong)$')
    session_id: str = Field(..., min_length=1, max_length=100)
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_id: str = Field(default_factory=lambda: f"ws_{uuid.uuid4().hex[:8]}")


class BatchQueryRequest(BaseModel):
    """Batch query processing request"""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    queries: List[QueryRequest] = Field(..., min_length=1, max_length=10)
    batch_id: str = Field(default_factory=lambda: f"batch_{uuid.uuid4().hex[:8]}")
    parallel_processing: bool = Field(default=True)
    priority: str = Field(default="normal", pattern=r'^(low|normal|high)$')


class BatchQueryResponse(BaseModel):
    """Batch query processing response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    success: bool = True
    batch_id: str
    results: List[QueryResponse] = Field(default_factory=list)
    completed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    total_processing_time_ms: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConfigurationRequest(BaseModel):
    """Service configuration request"""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    default_temperature: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    default_max_tokens: Optional[int] = Field(default=None, ge=100, le=8192)
    enable_caching: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = Field(default=None, ge=60, le=86400)
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1, le=1000)


class ConfigurationResponse(BaseModel):
    """Service configuration response"""
    model_config = ConfigDict(
        extra='forbid'
    )
    
    success: bool = True
    message: str = "Configuration updated successfully"
    current_config: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """Chat message schema for WebSocket communication"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    session_id: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=100)
    message_type: str = Field(..., description="Message type (query, response, system)")
    content: str = Field(..., min_length=1, max_length=8000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v: str) -> str:
        """Validate message type"""
        valid_types = {'query', 'response', 'system', 'error', 'typing'}
        if v not in valid_types:
            raise ValueError(f'Invalid message type: {v}. Must be one of {valid_types}')
        return v


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='forbid'
    )
    
    success: bool = False
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default=None, description="Request identifier for tracking")


# Export all schemas
__all__ = [
    'ServiceError',
    'QueryRequest',
    'QueryResponse', 
    'ThreatAnalysisRequest',
    'ThreatAnalysisResponse',
    'FeedbackRequest',
    'FeedbackResponse',
    'ContextRequest',
    'ContextResponse',
    'ChatMessage',
    'ErrorResponse',
    'ConfigurationResponse'
]
