"""
SIEM Integration Models

Comprehensive models for SIEM integration including:
- Database ORM models for persistence
- Pydantic models for API validation
- Enums for standardized values
- Modern async-compatible design
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, HttpUrl, validator
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum
import uuid

from common.models import Base

# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class SIEMType(str, Enum):
    """Supported SIEM systems with their identifiers"""
    SPLUNK = "splunk"
    QRADAR = "qradar"
    ELASTIC_SIEM = "elastic_siem"
    ELASTICSEARCH = "elasticsearch"
    AZURE_SENTINEL = "azure_sentinel"
    MICROSOFT_SENTINEL = "microsoft_sentinel"
    CHRONICLE = "chronicle"
    ARCSIGHT = "arcsight"
    SUMO_LOGIC = "sumo_logic"
    LOGRHYTHM = "logrhythm"
    SECURONIX = "securonix"
    DEVO = "devo"
    GENERIC = "generic"


class SIEMAuthType(str, Enum):
    """SIEM authentication methods"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    SAML = "saml"
    NONE = "none"


class SIEMEventSeverity(str, Enum):
    """Standardized event severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"


class SIEMEventCategory(str, Enum):
    """Standardized event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    MALWARE = "malware"
    DATA_LOSS = "data_loss"
    INTRUSION = "intrusion"
    VULNERABILITY = "vulnerability"
    COMPLIANCE = "compliance"
    SYSTEM = "system"
    APPLICATION = "application"
    OTHER = "other"


class SIEMConnectionStatus(str, Enum):
    """SIEM connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TESTING = "testing"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


# =============================================================================
# DATABASE ORM MODELS
# =============================================================================

class SIEMConfigORM(Base):
    """Database model for SIEM system configurations"""
    __tablename__ = "siem_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    display_name = Column(String)
    description = Column(Text)
    
    # SIEM system details
    siem_type = Column(String, nullable=False)  # SIEMType enum value
    base_url = Column(String, nullable=False)
    api_version = Column(String, default="v1")
    
    # Authentication
    auth_type = Column(String, nullable=False)  # SIEMAuthType enum value
    auth_config = Column(JSON)  # Encrypted auth credentials
    
    # Connection settings
    timeout_seconds = Column(Integer, default=30)
    max_retries = Column(Integer, default=3)
    rate_limit_per_minute = Column(Integer, default=100)
    
    # Feature flags
    supports_webhooks = Column(Boolean, default=False)
    supports_real_time = Column(Boolean, default=False)
    supports_bulk_query = Column(Boolean, default=True)
    
    # Status and monitoring
    is_active = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=False)
    last_health_check = Column(DateTime)
    last_successful_query = Column(DateTime)
    connection_status = Column(String, default=SIEMConnectionStatus.UNKNOWN.value)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)  # User ID
    
    # Relationships
    events = relationship("SIEMEventORM", back_populates="siem_config")
    queries = relationship("SIEMQueryORM", back_populates="siem_config")
    health_logs = relationship("SIEMHealthLogORM", back_populates="siem_config")


class SIEMEventORM(Base):
    """Database model for SIEM events"""
    __tablename__ = "siem_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False, index=True)  # Original SIEM event ID
    siem_config_id = Column(String, ForeignKey("siem_configs.id"), nullable=False)
    
    # Event metadata
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # SIEMEventSeverity enum value
    category = Column(String)  # SIEMEventCategory enum value
    
    # Network details
    source_ip = Column(String, index=True)
    destination_ip = Column(String, index=True)
    source_port = Column(Integer)
    destination_port = Column(Integer)
    protocol = Column(String)
    
    # Host details
    source_hostname = Column(String)
    destination_hostname = Column(String)
    
    # User and asset information
    user = Column(String, index=True)
    asset = Column(String)
    
    # Event content
    title = Column(String)
    description = Column(Text)
    signature = Column(String)
    
    # Raw data and enrichment
    raw_event = Column(JSON)  # Original event from SIEM
    normalized_event = Column(JSON)  # Normalized event structure
    enrichment_data = Column(JSON)  # Additional enrichment
    
    # Geolocation
    geo_location = Column(JSON)
    
    # Threat intelligence
    threat_intelligence = Column(JSON)
    ioc_matches = Column(JSON)  # Indicators of Compromise matches
    
    # Correlation
    correlation_id = Column(String, index=True)
    parent_event_id = Column(String)
    related_events = Column(JSON)  # List of related event IDs
    
    # Processing metadata
    ingested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")
    
    # Relationships
    siem_config = relationship("SIEMConfigORM", back_populates="events")


class SIEMQueryORM(Base):
    """Database model for SIEM queries and their results"""
    __tablename__ = "siem_queries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    siem_config_id = Column(String, ForeignKey("siem_configs.id"), nullable=False)
    
    # Query details
    query_text = Column(Text, nullable=False)
    query_type = Column(String, nullable=False)  # search, alert, report, etc.
    query_parameters = Column(JSON)
    
    # Time range
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # Results
    total_events = Column(Integer, default=0)
    returned_events = Column(Integer, default=0)
    execution_time_ms = Column(Float)
    
    # Status
    status = Column(String, default="pending")  # pending, running, completed, failed
    error_message = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_by = Column(String)  # User ID
    
    # Relationships
    siem_config = relationship("SIEMConfigORM", back_populates="queries")


class SIEMHealthLogORM(Base):
    """Database model for SIEM health check logs"""
    __tablename__ = "siem_health_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    siem_config_id = Column(String, ForeignKey("siem_configs.id"), nullable=False)
    
    # Health check results
    status = Column(String, nullable=False)  # SIEMConnectionStatus enum value
    response_time_ms = Column(Float)
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Connectivity tests
    dns_resolution_ms = Column(Float)
    tcp_connection_ms = Column(Float)
    ssl_handshake_ms = Column(Float)
    http_response_ms = Column(Float)
    
    # API tests
    auth_test_success = Column(Boolean)
    api_test_success = Column(Boolean)
    webhook_test_success = Column(Boolean)
    
    # Metadata
    check_time = Column(DateTime, default=datetime.utcnow)
    check_type = Column(String, default="scheduled")  # scheduled, manual, startup
    
    # Relationships
    siem_config = relationship("SIEMConfigORM", back_populates="health_logs")


class SIEMWebhookORM(Base):
    """Database model for SIEM webhook configurations"""
    __tablename__ = "siem_webhooks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    siem_config_id = Column(String, ForeignKey("siem_configs.id"), nullable=False)
    
    # Webhook details
    webhook_url = Column(String, nullable=False)
    webhook_secret = Column(String)  # For verification
    is_active = Column(Boolean, default=True)
    
    # Event filtering
    event_types = Column(JSON)  # List of event types to forward
    severity_filter = Column(JSON)  # List of severities to include
    
    # Statistics
    events_received = Column(Integer, default=0)
    last_event_received = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# PYDANTIC MODELS FOR API
# =============================================================================

class SIEMConfigCreate(BaseModel):
    """Request model for creating SIEM configuration"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = None
    description: Optional[str] = None
    siem_type: SIEMType
    base_url: HttpUrl
    api_version: str = "v1"
    auth_type: SIEMAuthType
    auth_config: Dict[str, Any]
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    rate_limit_per_minute: int = Field(default=100, ge=1, le=1000)
    supports_webhooks: bool = False
    supports_real_time: bool = False
    supports_bulk_query: bool = True

    @validator('auth_config')
    def validate_auth_config(cls, v, values):
        """Validate auth_config based on auth_type"""
        auth_type = values.get('auth_type')
        if auth_type == SIEMAuthType.API_KEY:
            if 'api_key' not in v:
                raise ValueError('api_key required for API_KEY auth type')
        elif auth_type == SIEMAuthType.BASIC_AUTH:
            if 'username' not in v or 'password' not in v:
                raise ValueError('username and password required for BASIC_AUTH')
        elif auth_type == SIEMAuthType.OAUTH2:
            if 'client_id' not in v or 'client_secret' not in v:
                raise ValueError('client_id and client_secret required for OAUTH2')
        return v


class SIEMConfigUpdate(BaseModel):
    """Request model for updating SIEM configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    api_version: Optional[str] = None
    auth_type: Optional[SIEMAuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    supports_webhooks: Optional[bool] = None
    supports_real_time: Optional[bool] = None
    supports_bulk_query: Optional[bool] = None
    is_active: Optional[bool] = None


class SIEMConfigResponse(BaseModel):
    """Response model for SIEM configuration"""
    id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    siem_type: SIEMType
    base_url: str
    api_version: str
    auth_type: SIEMAuthType
    timeout_seconds: int
    max_retries: int
    rate_limit_per_minute: int
    supports_webhooks: bool
    supports_real_time: bool
    supports_bulk_query: bool
    is_active: bool
    is_healthy: bool
    last_health_check: Optional[datetime]
    last_successful_query: Optional[datetime]
    connection_status: SIEMConnectionStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class SIEMEventCreate(BaseModel):
    """Request model for creating SIEM event"""
    event_id: str
    siem_config_id: str
    timestamp: datetime
    event_type: str
    severity: SIEMEventSeverity
    category: Optional[SIEMEventCategory] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = Field(None, ge=1, le=65535)
    destination_port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = None
    source_hostname: Optional[str] = None
    destination_hostname: Optional[str] = None
    user: Optional[str] = None
    asset: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    signature: Optional[str] = None
    raw_event: Optional[Dict[str, Any]] = None
    geo_location: Optional[Dict[str, Any]] = None
    threat_intelligence: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None


class SIEMEventResponse(BaseModel):
    """Response model for SIEM event"""
    id: str
    event_id: str
    siem_config_id: str
    timestamp: datetime
    event_type: str
    severity: SIEMEventSeverity
    category: Optional[SIEMEventCategory]
    source_ip: Optional[str]
    destination_ip: Optional[str]
    source_port: Optional[int]
    destination_port: Optional[int]
    protocol: Optional[str]
    source_hostname: Optional[str]
    destination_hostname: Optional[str]
    user: Optional[str]
    asset: Optional[str]
    title: Optional[str]
    description: Optional[str]
    signature: Optional[str]
    geo_location: Optional[Dict[str, Any]]
    threat_intelligence: Optional[Dict[str, Any]]
    correlation_id: Optional[str]
    parent_event_id: Optional[str]
    ingested_at: datetime
    processed_at: Optional[datetime]
    is_processed: bool
    processing_status: str

    class Config:
        from_attributes = True


class SIEMQueryRequest(BaseModel):
    """Request model for SIEM query"""
    query_text: str = Field(..., min_length=1)
    query_type: str = "search"
    query_parameters: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=1000, ge=1, le=10000)


class SIEMQueryResponse(BaseModel):
    """Response model for SIEM query results"""
    id: str
    query_text: str
    query_type: str
    status: str
    total_events: int
    returned_events: int
    execution_time_ms: Optional[float]
    events: List[SIEMEventResponse]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SIEMHealthStatus(BaseModel):
    """Response model for SIEM health status"""
    siem_id: str
    siem_name: str
    status: SIEMConnectionStatus
    is_healthy: bool
    last_check_time: datetime
    response_time_ms: Optional[float]
    error_message: Optional[str]
    connectivity_tests: Optional[Dict[str, Any]] = None
    api_tests: Optional[Dict[str, Any]] = None


class SIEMWebhookPayload(BaseModel):
    """Model for webhook payloads from SIEM systems"""
    webhook_id: str
    timestamp: datetime
    siem_source: str
    event_data: Dict[str, Any]
    signature: Optional[str] = None


class SIEMStatsResponse(BaseModel):
    """Response model for SIEM statistics"""
    total_configs: int
    active_configs: int
    healthy_configs: int
    total_events_today: int
    total_events_week: int
    total_events_month: int
    avg_response_time_ms: float
    top_event_types: List[Dict[str, Any]]
    event_severity_distribution: Dict[str, int]
    events: List[Dict[str, Any]]
    signature: Optional[str] = None


class SIEMQuery(BaseModel):
    """SIEM query configuration"""
    query_string: str
    start_time: datetime
    end_time: datetime
    max_results: int = Field(default=1000, ge=1, le=10000)
    fields: Optional[List[str]] = None


class SIEMHealthStatus(BaseModel):
    """SIEM connection health status"""
    siem_id: str
    status: str  # "healthy", "degraded", "down"
    last_successful_connection: Optional[datetime] = None  # Correct usage, ensure 'datetime' is the class
    last_check_time: Optional[datetime] = None
    last_error: Optional[str] = None
    response_time_ms: Optional[float] = None
    events_processed_24h: int = 0
