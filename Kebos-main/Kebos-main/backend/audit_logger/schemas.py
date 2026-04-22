"""
Audit Logger Schemas
Pydantic models for audit log entries with comprehensive validation.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class SeverityLevel(str, Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditActionType(str, Enum):
    """Common audit action types."""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    THREAT_DETECTION = "threat_detection"
    SECURITY_EVENT = "security_event"
    MODEL_OPERATION = "model_operation"
    ADMIN_ACTION = "admin_action"


class ResourceType(str, Enum):
    """Common resource types for audit logging."""
    USER = "user"
    MODEL = "model"
    NETWORK_PACKET = "network_packet"
    ALERT = "alert"
    SIEM_CONFIG = "siem_config"
    SECURITY_SYSTEM = "security_system"
    FILE = "file"
    DATABASE = "database"


class AuditLogCreateRequest(BaseModel):
    """Request model for creating audit log entries."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    action: str = Field(..., min_length=1, max_length=100, description="Action performed")
    user_id: Optional[int] = Field(None, ge=1, description="ID of user performing action")
    resource: Optional[str] = Field(None, max_length=200, description="Resource being acted upon")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional action details")
    ip_address: Optional[str] = Field(None, max_length=45, description="Client IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="Client user agent")
    success: bool = Field(True, description="Whether the action was successful")
    
    @field_validator('details')
    @classmethod
    def validate_details_size(cls, v):
        """Validate details JSON size for security."""
        import json
        if v and len(json.dumps(v)) > 10000:  # 10KB limit
            raise ValueError('Details payload too large (max 10KB)')
        return v


class SecurityEventCreateRequest(BaseModel):
    """Request model for security event logging."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    event_type: str = Field(..., min_length=1, max_length=100, description="Type of security event")
    severity: SeverityLevel = Field(..., description="Severity level")
    description: str = Field(..., min_length=1, max_length=1000, description="Event description")
    source_ip: Optional[str] = Field(None, max_length=45, description="Source IP address")
    user_id: Optional[int] = Field(None, ge=1, description="Associated user ID")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")


class ThreatDetectionLogRequest(BaseModel):
    """Request model for threat detection event logging."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    user_id: Optional[int] = Field(None, ge=1, description="User who initiated detection")
    packet_info: Dict[str, Any] = Field(..., description="Information about analyzed packet")
    threat_level: str = Field(..., min_length=1, max_length=50, description="Detected threat level")
    detection_result: Dict[str, Any] = Field(..., description="Detection system results")


class ModelOperationLogRequest(BaseModel):
    """Request model for model operation logging."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    user_id: int = Field(..., ge=1, description="User performing operation")
    operation: str = Field(..., min_length=1, max_length=50, description="Type of operation")
    model_info: Dict[str, Any] = Field(..., description="Model information")
    success: bool = Field(True, description="Whether operation was successful")


class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Unique log entry ID")
    user_id: Optional[int] = Field(None, description="User ID")
    action_type: str = Field(..., description="Action performed")
    resource: Optional[str] = Field(None, description="Resource acted upon")
    details: Optional[Dict[str, Any]] = Field(None, description="Action details")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    success: bool = Field(..., description="Action success status")
    timestamp: datetime = Field(..., description="When the action occurred")
    created_at: datetime = Field(..., description="When the log was created")


class AuditLogSearchRequest(BaseModel):
    """Request model for searching audit logs."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    user_id: Optional[int] = Field(None, ge=1, description="Filter by user ID")
    action: Optional[str] = Field(None, max_length=100, description="Filter by action type")
    resource: Optional[str] = Field(None, max_length=200, description="Filter by resource")
    start_time: Optional[datetime] = Field(None, description="Filter by start time")
    end_time: Optional[datetime] = Field(None, description="Filter by end time")
    success: Optional[bool] = Field(None, description="Filter by success status")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class AuditLogSearchResponse(BaseModel):
    """Response model for audit log searches."""
    logs: List[AuditLogResponse] = Field(..., description="List of audit log entries")
    total: int = Field(..., description="Total number of matching entries")
    limit: int = Field(..., description="Applied limit")
    offset: int = Field(..., description="Applied offset")


class AuditLogCreateResponse(BaseModel):
    """Response model for audit log creation."""
    status: str = Field(..., description="Operation status")
    log_id: Optional[int] = Field(None, description="Created log entry ID")
    task_id: Optional[str] = Field(None, description="Background task ID")
    message: Optional[str] = Field(None, description="Status message")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    database: str = Field(..., description="Database connection status")
    celery: str = Field(..., description="Celery worker status")
    storage: str = Field(..., description="Storage system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
