"""Network Analytics Models - Modernized with ORM and Pydantic schemas"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
from common.models import Base

# =============================================================================
# ENUMS
# =============================================================================

class TimeRange(str, Enum):
    """Time range options for analytics"""
    LAST_HOUR = "last_hour"
    LAST_DAY = "last_day"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class VisualizationType(str, Enum):
    """Types of visualizations available"""
    TIME_SERIES = "time_series"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    HEATMAP = "heatmap"
    NETWORK_GRAPH = "network_graph"
    SANKEY_DIAGRAM = "sankey_diagram"
    GEO_MAP = "geo_map"
    HISTOGRAM = "histogram"
    SCATTER_PLOT = "scatter_plot"


class MetricType(str, Enum):
    """Types of network metrics"""
    PACKET_COUNT = "packet_count"
    BYTE_COUNT = "byte_count"
    BANDWIDTH_USAGE = "bandwidth_usage"
    UNIQUE_IPS = "unique_ips"
    UNIQUE_PORTS = "unique_ports"
    CONNECTION_COUNT = "connection_count"
    PROTOCOL_DISTRIBUTION = "protocol_distribution"
    PORT_DISTRIBUTION = "port_distribution"
    ANOMALY_SCORE = "anomaly_score"
    THREAT_LEVEL = "threat_level"
    LATENCY = "latency"
    JITTER = "jitter"
    PACKET_LOSS = "packet_loss"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CONCURRENT_CONNECTIONS = "concurrent_connections"


class TrafficDirection(str, Enum):
    """Traffic direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"
    EXTERNAL = "external"
    BIDIRECTIONAL = "bidirectional"


class ProtocolType(str, Enum):
    """Network protocol types"""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    FTP = "ftp"
    SSH = "ssh"
    SMTP = "smtp"
    SNMP = "snmp"
    OTHER = "other"


class TrafficPatternType(str, Enum):
    """Types of traffic patterns"""
    PERIODIC = "periodic"
    BURST = "burst"
    TREND = "trend"
    BASELINE = "baseline"
    ANOMALOUS = "anomalous"
    SEASONAL = "seasonal"
    SPIKE = "spike"
    DIP = "dip"


class AnomalyType(str, Enum):
    """Types of network anomalies"""
    VOLUME_ANOMALY = "volume_anomaly"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    PROTOCOL_ANOMALY = "protocol_anomaly"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    STATISTICAL_ANOMALY = "statistical_anomaly"


class AnalysisStatus(str, Enum):
    """Status of analytics processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# ORM MODELS
# =============================================================================

class NetworkFlowORM(Base):
    """Network flow data storage"""
    __tablename__ = "network_flows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(String(255), nullable=False, index=True)
    source_ip = Column(INET, nullable=False, index=True)
    destination_ip = Column(INET, nullable=False, index=True)
    source_port = Column(Integer, index=True)
    destination_port = Column(Integer, index=True)
    protocol = Column(String(20), nullable=False, index=True)
    direction = Column(String(20), nullable=False, index=True)
    
    # Traffic metrics
    packet_count = Column(Integer, default=0)
    byte_count = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    
    # Timing information
    first_seen = Column(DateTime, nullable=False, index=True)
    last_seen = Column(DateTime, nullable=False, index=True)
    
    # Geographic and network context
    source_country = Column(String(10))
    destination_country = Column(String(10))
    source_asn = Column(String(20))
    destination_asn = Column(String(20))
    
    # Analysis results
    threat_score = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    is_malicious = Column(Boolean, default=False)
    
    # Metadata
    raw_data = Column(JSONB)
    processed_data = Column(JSONB)
    tags = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # TODO: Add relationships when foreign keys are properly defined in migration
    # patterns = relationship("TrafficPatternORM", back_populates="flows")
    # anomalies = relationship("NetworkAnomalyORM", back_populates="flow")
    
    # Indexes
    __table_args__ = (
        Index('idx_network_flows_time_range', 'first_seen', 'last_seen'),
        Index('idx_network_flows_ips', 'source_ip', 'destination_ip'),
        Index('idx_network_flows_ports', 'source_port', 'destination_port'),
        Index('idx_network_flows_metrics', 'packet_count', 'byte_count'),
        Index('idx_network_flows_scores', 'threat_score', 'anomaly_score'),
    )


class TrafficPatternORM(Base):
    """Detected traffic patterns"""
    __tablename__ = "traffic_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(String(255), nullable=False, unique=True, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)
    pattern_name = Column(String(255))
    description = Column(Text)
    
    # Pattern characteristics
    confidence_score = Column(Float, nullable=False)
    frequency = Column(String(50))  # hourly, daily, weekly, etc.
    duration_minutes = Column(Integer)
    
    # Traffic characteristics
    affected_ips = Column(JSONB)
    affected_ports = Column(JSONB)
    protocols = Column(JSONB)
    traffic_volume = Column(JSONB)
    
    # Time information
    first_detected = Column(DateTime, nullable=False, index=True)
    last_detected = Column(DateTime, nullable=False, index=True)
    next_predicted = Column(DateTime)
    
    # Analysis metadata
    detection_algorithm = Column(String(100))
    parameters = Column(JSONB)
    baseline_data = Column(JSONB)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_baseline = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # TODO: Add relationships when foreign keys are properly defined in migration
    # flows = relationship("NetworkFlowORM", back_populates="patterns")
    
    # Indexes
    __table_args__ = (
        Index('idx_traffic_patterns_type', 'pattern_type'),
        Index('idx_traffic_patterns_confidence', 'confidence_score'),
        Index('idx_traffic_patterns_detection_time', 'first_detected', 'last_detected'),
        Index('idx_traffic_patterns_active', 'is_active'),
    )


class NetworkAnomalyORM(Base):
    """Network anomalies and suspicious activities"""
    __tablename__ = "network_anomalies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anomaly_id = Column(String(255), nullable=False, unique=True, index=True)
    anomaly_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500))
    description = Column(Text)
    
    # Anomaly scoring
    severity_score = Column(Float, nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    risk_level = Column(String(20), index=True)  # low, medium, high, critical
    
    # Associated flow
    flow_id = Column(UUID(as_uuid=True), ForeignKey('network_flows.id'))
    # TODO: Add relationship when other side is properly defined
    # flow = relationship("NetworkFlowORM", back_populates="anomalies")
    
    # Detection details
    detection_algorithm = Column(String(100))
    detection_parameters = Column(JSONB)
    baseline_comparison = Column(JSONB)
    statistical_measures = Column(JSONB)
    
    # Time information
    detected_at = Column(DateTime, nullable=False, index=True)
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime, index=True)
    
    # Investigation status
    is_investigated = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)
    investigation_notes = Column(Text)
    
    # Metadata
    tags = Column(JSONB)
    additional_context = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_network_anomalies_type', 'anomaly_type'),
        Index('idx_network_anomalies_severity', 'severity_score'),
        Index('idx_network_anomalies_risk', 'risk_level'),
        Index('idx_network_anomalies_detection_time', 'detected_at'),
        Index('idx_network_anomalies_status', 'is_investigated', 'is_confirmed'),
    )


class AnalyticsJobORM(Base):
    """Analytics job tracking"""
    __tablename__ = "analytics_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), nullable=False, unique=True, index=True)
    job_type = Column(String(50), nullable=False, index=True)
    job_name = Column(String(255))
    description = Column(Text)
    
    # Job parameters
    query_parameters = Column(JSONB)
    processing_parameters = Column(JSONB)
    
    # Status tracking
    status = Column(String(20), nullable=False, default='pending', index=True)
    progress_percentage = Column(Float, default=0.0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    result_data = Column(JSONB)
    result_summary = Column(JSONB)
    processing_time_seconds = Column(Float)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # User context
    created_by = Column(String(255))
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_jobs_type', 'job_type'),
        Index('idx_analytics_jobs_status', 'status'),
        Index('idx_analytics_jobs_created', 'created_at'),
        Index('idx_analytics_jobs_user', 'created_by'),
    )


class NetworkTopologyORM(Base):
    """Network topology and asset discovery"""
    __tablename__ = "network_topology"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(INET, nullable=False, unique=True, index=True)
    hostname = Column(String(255), index=True)
    mac_address = Column(String(17))
    
    # Asset classification
    asset_type = Column(String(50))  # server, workstation, router, etc.
    operating_system = Column(String(100))
    device_vendor = Column(String(100))
    device_model = Column(String(100))
    
    # Network information
    subnet = Column(String(50))
    vlan_id = Column(Integer)
    network_segment = Column(String(100))
    
    # Geographic and organizational
    location = Column(String(255))
    department = Column(String(100))
    owner = Column(String(255))
    
    # Discovery information
    first_seen = Column(DateTime, nullable=False, index=True)
    last_seen = Column(DateTime, nullable=False, index=True)
    discovery_method = Column(String(50))
    
    # Status and metrics
    is_active = Column(Boolean, default=True, index=True)
    is_managed = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    
    # Open ports and services
    open_ports = Column(JSONB)
    running_services = Column(JSONB)
    
    # Metadata
    tags = Column(JSONB)
    custom_attributes = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_network_topology_type', 'asset_type'),
        Index('idx_network_topology_subnet', 'subnet'),
        Index('idx_network_topology_active', 'is_active'),
        Index('idx_network_topology_seen', 'first_seen', 'last_seen'),
    )


# =============================================================================
# PYDANTIC MODELS - REQUEST/RESPONSE SCHEMAS
# =============================================================================

class AnalyticsQueryCreate(BaseModel):
    """Request model for creating analytics queries"""
    query_name: Optional[str] = None
    time_range: TimeRange
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metrics: List[MetricType]
    visualization_type: VisualizationType
    filters: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None
    limit: int = Field(default=1000, ge=1, le=10000)
    
    @validator('start_time', 'end_time')
    def validate_custom_time_range(cls, v, values):
        if values.get('time_range') == TimeRange.CUSTOM:
            if not v:
                raise ValueError('start_time and end_time required for custom time range')
        return v


class TimeSeriesDataPoint(BaseModel):
    """Data point for time series visualization"""
    timestamp: datetime
    value: float
    metric_type: str
    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CategoryDataPoint(BaseModel):
    """Data point for categorical visualizations"""
    category: str
    value: float
    percentage: Optional[float] = None
    count: Optional[int] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NetworkNode(BaseModel):
    """Node for network graph visualization"""
    id: str
    label: str
    node_type: str  # "ip", "host", "service", "subnet"
    size: float = 1.0
    color: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    metrics: Dict[str, float] = {}
    metadata: Optional[Dict[str, Any]] = None


class NetworkEdge(BaseModel):
    """Edge for network graph visualization"""
    source: str
    target: str
    weight: float = 1.0
    edge_type: str = "connection"
    label: Optional[str] = None
    color: Optional[str] = None
    metrics: Dict[str, float] = {}
    metadata: Optional[Dict[str, Any]] = None


class NetworkGraph(BaseModel):
    """Network graph visualization data"""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    layout_algorithm: Optional[str] = "force_directed"
    metadata: Optional[Dict[str, Any]] = None


class GeoPoint(BaseModel):
    """Geographic point for geo visualizations"""
    latitude: float
    longitude: float
    label: Optional[str] = None
    value: float = 1.0
    color: Optional[str] = None
    popup_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsResult(BaseModel):
    """Result of network analytics query"""
    query_id: str
    query_name: Optional[str]
    visualization_type: VisualizationType
    
    # Data arrays based on visualization type
    time_series_data: Optional[List[TimeSeriesDataPoint]] = None
    category_data: Optional[List[CategoryDataPoint]] = None
    network_graph: Optional[NetworkGraph] = None
    geo_data: Optional[List[GeoPoint]] = None
    raw_data: Optional[List[Dict[str, Any]]] = None
    
    # Summary information
    summary_metrics: Dict[str, Any] = {}
    data_quality_score: Optional[float] = None
    confidence_level: Optional[float] = None
    
    # Processing metadata
    processing_time_ms: float
    data_points_count: int = 0
    query_execution_time_ms: Optional[float] = None
    
    # Time information
    data_time_range: Optional[Dict[str, datetime]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TrafficPatternResponse(BaseModel):
    """Response model for traffic patterns"""
    id: str
    pattern_id: str
    pattern_type: TrafficPatternType
    pattern_name: Optional[str]
    description: Optional[str]
    confidence_score: float
    frequency: Optional[str]
    duration_minutes: Optional[int]
    affected_ips: Optional[List[str]] = None
    affected_ports: Optional[List[int]] = None
    protocols: Optional[List[str]] = None
    first_detected: datetime
    last_detected: datetime
    next_predicted: Optional[datetime] = None
    is_active: bool
    is_baseline: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NetworkAnomalyResponse(BaseModel):
    """Response model for network anomalies"""
    id: str
    anomaly_id: str
    anomaly_type: AnomalyType
    title: Optional[str]
    description: Optional[str]
    severity_score: float
    confidence_score: float
    risk_level: str
    detected_at: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_investigated: bool
    is_confirmed: bool
    is_false_positive: bool
    investigation_notes: Optional[str]
    tags: Optional[List[str]] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NetworkFlowResponse(BaseModel):
    """Response model for network flows"""
    id: str
    flow_id: str
    source_ip: str
    destination_ip: str
    source_port: Optional[int]
    destination_port: Optional[int]
    protocol: str
    direction: TrafficDirection
    packet_count: int
    byte_count: int
    duration_seconds: float
    first_seen: datetime
    last_seen: datetime
    source_country: Optional[str]
    destination_country: Optional[str]
    threat_score: float
    anomaly_score: float
    is_malicious: bool
    tags: Optional[List[str]] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NetworkTopologyResponse(BaseModel):
    """Response model for network topology"""
    id: str
    ip_address: str
    hostname: Optional[str]
    mac_address: Optional[str]
    asset_type: Optional[str]
    operating_system: Optional[str]
    device_vendor: Optional[str]
    subnet: Optional[str]
    location: Optional[str]
    first_seen: datetime
    last_seen: datetime
    is_active: bool
    is_managed: bool
    risk_score: float
    open_ports: Optional[List[int]] = None
    running_services: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsJobResponse(BaseModel):
    """Response model for analytics jobs"""
    id: str
    job_id: str
    job_type: str
    job_name: Optional[str]
    description: Optional[str]
    status: AnalysisStatus
    progress_percentage: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_seconds: Optional[float]
    created_by: Optional[str]
    error_message: Optional[str]
    result_summary: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NetworkStatsResponse(BaseModel):
    """Response model for network statistics"""
    total_flows: int
    unique_ips: int
    unique_ports: int
    total_bytes: int
    total_packets: int
    protocol_distribution: Dict[str, int]
    top_talkers: List[Dict[str, Any]]
    anomaly_count: int
    threat_count: int
    active_patterns: int
    time_range: Dict[str, datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
