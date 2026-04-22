"""
Common Module Schemas
Pydantic v2 compliant schemas for shared models and utilities.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from enum import Enum


class StatusEnum(str, Enum):
    """Common status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeverityLevel(str, Enum):
    """Severity level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogLevel(str, Enum):
    """Logging level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseResponse):
    """Standardized error response model."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    error_code: str = Field(..., description="Error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    trace_id: Optional[str] = Field(None, description="Request trace ID")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    model_config = ConfigDict(from_attributes=True)
    
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database connection status")
    celery: str = Field(..., description="Celery worker status")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="External dependencies status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")


class UserCreate(BaseModel):
    """User creation schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    role: str = Field(default="operator", description="User role")
    is_active: bool = Field(default=True, description="User active status")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain alphanumeric characters, underscores, and hyphens')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    role: Optional[str] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="User active status")


class UserResponse(BaseModel):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class ModelMetadata(BaseModel):
    """Model metadata schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    name: str = Field(..., min_length=1, max_length=100, description="Model name")
    description: Optional[str] = Field(None, max_length=1000, description="Model description")
    tags: List[str] = Field(default_factory=list, description="Model tags")
    framework: str = Field(..., description="ML framework")
    version: str = Field(..., description="Model version")
    model_type: str = Field(..., description="Model type classification")
    use_case: Optional[str] = Field(None, description="Model use case")
    data_sensitivity: str = Field(default="medium", description="Data sensitivity level")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags list."""
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        for tag in v:
            if len(tag) > 30:
                raise ValueError('Tag length cannot exceed 30 characters')
        return v


class AuditLogRequest(BaseModel):
    """Audit log creation request."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    action: str = Field(..., min_length=1, max_length=100, description="Action performed")
    resource: Optional[str] = Field(None, max_length=200, description="Resource identifier")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional details")
    ip_address: Optional[str] = Field(None, max_length=45, description="Client IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    success: bool = Field(default=True, description="Action success status")
    
    @field_validator('details')
    @classmethod
    def validate_details_size(cls, v):
        """Validate details JSON size."""
        import json
        if v and len(json.dumps(v)) > 10000:  # 10KB limit
            raise ValueError('Details payload too large (max 10KB)')
        return v


class ValidationRequest(BaseModel):
    """Data validation request schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    data_type: str = Field(..., description="Type of data to validate")
    data: Any = Field(..., description="Data to validate")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    strict_mode: bool = Field(default=False, description="Enable strict validation")


class ValidationResponse(BaseResponse):
    """Data validation response schema."""
    is_valid: bool = Field(..., description="Validation result")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Validation metadata")


class UtilityRequest(BaseModel):
    """Generic utility request schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    operation: str = Field(..., description="Utility operation to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional options")


class UtilityResponse(BaseResponse):
    """Generic utility response schema."""
    result: Any = Field(None, description="Operation result")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Result metadata")


class WorkflowStep(BaseModel):
    """Workflow step schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    step_id: str = Field(..., description="Step identifier")
    name: str = Field(..., description="Step name")
    description: Optional[str] = Field(None, description="Step description")
    module: str = Field(..., description="Module responsible for step")
    status: StatusEnum = Field(default=StatusEnum.PENDING, description="Step status")
    dependencies: List[str] = Field(default_factory=list, description="Step dependencies")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    results: Dict[str, Any] = Field(default_factory=dict, description="Step results")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Step start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Step completion timestamp")


class SecurityConfig(BaseModel):
    """Security configuration schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    max_requests_per_minute: int = Field(default=100, ge=1, le=10000, description="Max requests per minute")
    enable_ip_whitelist: bool = Field(default=False, description="Enable IP whitelist")
    allowed_ips: List[str] = Field(default_factory=list, description="Allowed IP addresses")
    session_timeout_minutes: int = Field(default=60, ge=5, le=1440, description="Session timeout in minutes")
    require_mfa: bool = Field(default=False, description="Require multi-factor authentication")
    password_policy: Dict[str, Any] = Field(default_factory=dict, description="Password policy settings")


class DatabaseConfig(BaseModel):
    """Database configuration schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    host: str = Field(..., description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Max pool overflow")
    pool_timeout: int = Field(default=30, ge=1, le=300, description="Pool timeout in seconds")
    
    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v):
        """Ensure password is not empty."""
        if not v or v.strip() == "":
            raise ValueError('Database password cannot be empty')
        return v


class CeleryConfig(BaseModel):
    """Celery configuration schema."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    broker_url: str = Field(..., description="Celery broker URL")
    result_backend: str = Field(..., description="Celery result backend")
    task_serializer: str = Field(default="json", description="Task serialization format")
    result_serializer: str = Field(default="json", description="Result serialization format")
    task_soft_time_limit: int = Field(default=300, ge=10, le=3600, description="Task soft time limit")
    task_hard_time_limit: int = Field(default=600, ge=30, le=7200, description="Task hard time limit")
    worker_concurrency: int = Field(default=4, ge=1, le=32, description="Worker concurrency")


class SystemInfo(BaseModel):
    """System information schema."""
    model_config = ConfigDict(from_attributes=True)
    
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Deployment environment")
    python_version: str = Field(..., description="Python version")
    platform: str = Field(..., description="Operating system platform")
    cpu_count: int = Field(..., description="CPU core count")
    memory_total: int = Field(..., description="Total memory in bytes")
    disk_usage: Dict[str, Any] = Field(default_factory=dict, description="Disk usage statistics")
    uptime: float = Field(..., description="Service uptime in seconds")
    timezone: str = Field(..., description="System timezone")
    build_info: Dict[str, Any] = Field(default_factory=dict, description="Build information")
