"""
Job Manager Models - Comprehensive ORM and Pydantic Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from common.db import Base


# =============================================================================
# ENUMS
# =============================================================================

class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"


class JobPriority(str, Enum):
    """Job priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class JobType(str, Enum):
    """Available job types"""
    DATA_PROCESSING = "data_processing"
    ML_TRAINING = "ml_training"
    ML_INFERENCE = "ml_inference"
    THREAT_ANALYSIS = "threat_analysis"
    NETWORK_SCAN = "network_scan"
    SIEM_QUERY = "siem_query"
    REPORT_GENERATION = "report_generation"
    DATA_EXPORT = "data_export"
    SYSTEM_MAINTENANCE = "system_maintenance"
    BACKUP_OPERATION = "backup_operation"
    CUSTOM = "custom"


class NotificationType(str, Enum):
    """Job notification types"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    INTERNAL = "internal"
    SLACK = "slack"
    TEAMS = "teams"


# =============================================================================
# ORM MODELS
# =============================================================================

class JobORM(Base):
    """Main job execution tracking"""
    __tablename__ = "jobs"
    
    # Primary key and identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), nullable=False, unique=True, index=True)
    job_name = Column(String(500))
    
    # Job classification
    job_type = Column(String(50), nullable=False, index=True)
    job_category = Column(String(100))
    priority = Column(String(20), default=JobPriority.NORMAL, index=True)
    
    # Execution details
    status = Column(String(20), default=JobStatus.PENDING, nullable=False, index=True)
    celery_task_id = Column(String(255), index=True)
    worker_node = Column(String(100))
    
    # Timing information
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    scheduled_at = Column(DateTime, index=True)
    started_at = Column(DateTime, index=True)
    completed_at = Column(DateTime, index=True)
    expires_at = Column(DateTime, index=True)
    
    # Progress and metrics
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(255))
    total_steps = Column(Integer)
    
    # Resource usage
    estimated_duration_seconds = Column(Integer)
    actual_duration_seconds = Column(Float)
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    
    # Job configuration
    input_parameters = Column(JSONB)
    configuration = Column(JSONB)
    environment_variables = Column(JSONB)
    
    # Results and outputs
    result_data = Column(JSONB)
    output_files = Column(JSONB)
    logs = Column(Text)
    error_message = Column(Text)
    error_traceback = Column(Text)
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    retry_delay_seconds = Column(Integer, default=60)
    
    # User and access control
    created_by = Column(String(255), nullable=False, index=True)
    assigned_to = Column(String(255))
    organization_id = Column(String(255), index=True)
    
    # Monitoring and health
    heartbeat_at = Column(DateTime)
    health_check_interval_seconds = Column(Integer, default=30)
    
    # Metadata
    tags = Column(JSONB)
    job_metadata = Column(JSONB)
    
    # Audit fields
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_jobs_status_priority', 'status', 'priority'),
        Index('idx_jobs_type_status', 'job_type', 'status'),
        Index('idx_jobs_created_status', 'created_at', 'status'),
        Index('idx_jobs_user_status', 'created_by', 'status'),
        Index('idx_jobs_celery_task', 'celery_task_id'),
        Index('idx_jobs_scheduled_pending', 'scheduled_at', 'status'),
    )


class JobDependencyORM(Base):
    """Job dependency relationships"""
    __tablename__ = "job_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    child_job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    dependency_type = Column(String(50), default="sequential")  # sequential, parallel, conditional
    condition_expression = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_job_deps_parent', 'parent_job_id'),
        Index('idx_job_deps_child', 'child_job_id'),
    )


class JobQueueORM(Base):
    """Job queue management"""
    __tablename__ = "job_queues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Queue configuration
    max_concurrent_jobs = Column(Integer, default=10)
    priority_weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    
    # Queue statistics
    total_jobs = Column(Integer, default=0)
    running_jobs = Column(Integer, default=0)
    pending_jobs = Column(Integer, default=0)
    completed_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    
    # Resource limits
    memory_limit_mb = Column(Integer)
    cpu_limit_percent = Column(Float)
    disk_limit_mb = Column(Integer)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    configuration = Column(JSONB)
    tags = Column(JSONB)


class JobNotificationORM(Base):
    """Job notification configuration and logs"""
    __tablename__ = "job_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Notification configuration
    notification_type = Column(String(50), nullable=False)
    trigger_events = Column(JSONB)  # ["completed", "failed", "started"]
    recipient = Column(String(500))
    
    # Delivery details
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    delivery_status = Column(String(50))
    error_message = Column(Text)
    
    # Content
    subject = Column(String(500))
    message = Column(Text)
    attachment_paths = Column(JSONB)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    notification_metadata = Column(JSONB)


class JobLogORM(Base):
    """Detailed job execution logs"""
    __tablename__ = "job_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Log details
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    log_level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    
    # Context
    step_name = Column(String(255))
    function_name = Column(String(255))
    line_number = Column(Integer)
    
    # Structured data
    structured_data = Column(JSONB)
    exception_info = Column(JSONB)
    
    # Performance metrics
    execution_time_ms = Column(Float)
    memory_usage_mb = Column(Float)
    
    __table_args__ = (
        Index('idx_job_logs_job_timestamp', 'job_id', 'timestamp'),
        Index('idx_job_logs_level', 'log_level'),
    )


# =============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS
# =============================================================================

class JobCreate(BaseModel):
    """Request model for creating a new job"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    job_name: Optional[str] = Field(None, max_length=500)
    job_type: JobType
    job_category: Optional[str] = Field(None, max_length=100)
    priority: JobPriority = JobPriority.NORMAL
    
    # Scheduling
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Configuration
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    environment_variables: Optional[Dict[str, str]] = None
    
    # Resource requirements
    estimated_duration_seconds: Optional[int] = Field(None, gt=0)
    memory_limit_mb: Optional[int] = Field(None, gt=0)
    cpu_limit_percent: Optional[float] = Field(None, gt=0, le=100)
    
    # Retry configuration
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay_seconds: int = Field(60, ge=0)
    
    # Metadata
    tags: Optional[Dict[str, str]] = None
    job_metadata: Optional[Dict[str, Any]] = None
    
    # Dependencies
    depends_on: Optional[List[str]] = Field(None, description="List of job IDs this job depends on")
    
    @validator('scheduled_at')
    def scheduled_at_must_be_future(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('scheduled_at must be in the future')
        return v


class JobUpdate(BaseModel):
    """Request model for updating job status and progress"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: Optional[JobStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    current_step: Optional[str] = Field(None, max_length=255)
    
    # Results
    result_data: Optional[Dict[str, Any]] = None
    output_files: Optional[List[str]] = None
    
    # Error information
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Resource usage
    memory_usage_mb: Optional[float] = Field(None, ge=0)
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    
    # Metadata updates
    tags: Optional[Dict[str, str]] = None
    job_metadata: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    """Response model for job information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    job_id: str
    job_name: Optional[str]
    job_type: str
    job_category: Optional[str]
    priority: str
    status: str
    
    # Timing
    created_at: datetime
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    # Progress
    progress_percentage: float
    current_step: Optional[str]
    total_steps: Optional[int]
    
    # Resource usage
    estimated_duration_seconds: Optional[int]
    actual_duration_seconds: Optional[float]
    memory_usage_mb: Optional[float]
    cpu_usage_percent: Optional[float]
    
    # Configuration
    input_parameters: Dict[str, Any]
    configuration: Dict[str, Any]
    
    # Results
    result_data: Optional[Dict[str, Any]]
    output_files: Optional[List[str]]
    
    # Error information
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    
    # User information
    created_by: str
    assigned_to: Optional[str]
    
    # Metadata
    tags: Optional[Dict[str, str]]
    job_metadata: Optional[Dict[str, Any]]
    
    updated_at: datetime


class JobSummaryResponse(BaseModel):
    """Simplified job information for listings"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    job_id: str
    job_name: Optional[str]
    job_type: str
    status: str
    priority: str
    progress_percentage: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: str
    estimated_duration_seconds: Optional[int]
    actual_duration_seconds: Optional[float]


class JobQuery(BaseModel):
    """Query parameters for job search and filtering"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Filtering
    job_type: Optional[JobType] = None
    status: Optional[JobStatus] = None
    priority: Optional[JobPriority] = None
    created_by: Optional[str] = None
    
    # Date ranges
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    completed_after: Optional[datetime] = None
    completed_before: Optional[datetime] = None
    
    # Search
    search_term: Optional[str] = Field(None, max_length=255)
    tags: Optional[Dict[str, str]] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field("created_at", pattern="^(created_at|started_at|completed_at|priority|status|job_type)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class JobStatistics(BaseModel):
    """Job execution statistics"""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    
    average_execution_time_seconds: Optional[float]
    success_rate_percentage: float
    
    # By job type
    jobs_by_type: Dict[str, int]
    jobs_by_priority: Dict[str, int]
    jobs_by_status: Dict[str, int]
    
    # Time series data
    jobs_created_last_24h: int
    jobs_completed_last_24h: int
    jobs_failed_last_24h: int


class JobLogResponse(BaseModel):
    """Job log entry response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    job_id: str
    timestamp: datetime
    log_level: str
    message: str
    step_name: Optional[str]
    function_name: Optional[str]
    line_number: Optional[int]
    structured_data: Optional[Dict[str, Any]]
    exception_info: Optional[Dict[str, Any]]
    execution_time_ms: Optional[float]


class JobNotificationCreate(BaseModel):
    """Create job notification configuration"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    notification_type: NotificationType
    trigger_events: List[str] = Field(..., min_items=1)
    recipient: str = Field(..., max_length=500)
    subject: Optional[str] = Field(None, max_length=500)
    message: Optional[str] = None
    
    @validator('trigger_events')
    def validate_trigger_events(cls, v):
        valid_events = {"started", "completed", "failed", "cancelled", "progress_update"}
        for event in v:
            if event not in valid_events:
                raise ValueError(f'Invalid trigger event: {event}. Must be one of {valid_events}')
        return v


class JobHealthResponse(BaseModel):
    """Job manager health check response"""
    status: str
    timestamp: datetime
    total_jobs: int
    running_jobs: int
    failed_jobs_last_hour: int
    average_queue_time_seconds: Optional[float]
    worker_nodes: List[str]
    queue_status: Dict[str, Any]
