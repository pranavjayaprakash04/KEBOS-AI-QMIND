"""
Job Manager Schemas - Pydantic Models for Request/Response Validation

This module contains all Pydantic schemas used for API request/response validation
and data serialization in the job management system. It provides comprehensive
models for job creation, updates, queries, and responses with proper validation.
"""

from pydantic import BaseModel, Field, ConfigDict, validator, field_validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum

# Re-export models from the main models module for backwards compatibility
from .models import (
    # Enums
    JobStatus, JobPriority, JobType, NotificationType,
    
    # Request Models
    JobCreate, JobUpdate, JobQuery, JobNotificationCreate,
    
    # Response Models
    JobResponse, JobSummaryResponse, JobStatistics, 
    JobLogResponse, JobHealthResponse,
    
    # Legacy compatibility schemas (if needed)
)

# =============================================================================
# ADDITIONAL SPECIALIZED SCHEMAS
# =============================================================================

class JobCreationRequest(BaseModel):
    """Simplified job creation request for common use cases"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., max_length=500, description="Human-readable job name")
    type: JobType = Field(..., description="Type of job to execute")
    priority: JobPriority = Field(JobPriority.NORMAL, description="Job execution priority")
    
    # Simplified parameters
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data for the job")
    config: Optional[Dict[str, Any]] = Field(None, description="Job configuration parameters")
    
    # Scheduling options
    run_immediately: bool = Field(True, description="Whether to run job immediately")
    scheduled_for: Optional[datetime] = Field(None, description="When to run the job (if not immediate)")
    
    # Resource requirements
    timeout_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Job timeout in minutes")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    
    # Metadata
    tags: Optional[Dict[str, str]] = Field(None, description="Job tags for organization")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('scheduled_for')
    @classmethod
    def validate_scheduled_time(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class JobStatusUpdate(BaseModel):
    """Simplified job status update"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: JobStatus = Field(..., description="New job status")
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, max_length=500, description="Status message")
    
    # Results for completed jobs
    results: Optional[Dict[str, Any]] = Field(None, description="Job execution results")
    error_details: Optional[str] = Field(None, description="Error details for failed jobs")


class JobSearchRequest(BaseModel):
    """Job search and filtering request"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Basic filters
    status: Optional[List[JobStatus]] = Field(None, description="Filter by job statuses")
    type: Optional[List[JobType]] = Field(None, description="Filter by job types")
    priority: Optional[List[JobPriority]] = Field(None, description="Filter by priorities")
    
    # User filters
    created_by_me: bool = Field(False, description="Show only jobs created by current user")
    assigned_to_me: bool = Field(False, description="Show only jobs assigned to current user")
    
    # Date filters
    created_after: Optional[datetime] = Field(None, description="Jobs created after this date")
    created_before: Optional[datetime] = Field(None, description="Jobs created before this date")
    
    # Text search
    search_text: Optional[str] = Field(None, max_length=255, description="Search in job names and descriptions")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: str = Field("created_at", description="Sort field")
    sort_desc: bool = Field(True, description="Sort in descending order")


class JobSummary(BaseModel):
    """Compact job information for lists"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Job unique identifier")
    name: str = Field(..., description="Job name")
    type: str = Field(..., description="Job type")
    status: str = Field(..., description="Current status")
    priority: str = Field(..., description="Job priority")
    
    progress: float = Field(..., description="Progress percentage")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    
    created_by: str = Field(..., description="Creator user ID")
    current_step: Optional[str] = Field(None, description="Current execution step")


class JobMetrics(BaseModel):
    """Job execution metrics and statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    # Performance metrics
    average_duration_seconds: Optional[float] = Field(None, description="Average execution time")
    success_rate_percent: float = Field(..., description="Job success rate")
    throughput_per_hour: Optional[float] = Field(None, description="Jobs completed per hour")
    
    # Resource usage
    average_memory_mb: Optional[float] = Field(None, description="Average memory usage")
    average_cpu_percent: Optional[float] = Field(None, description="Average CPU usage")
    peak_memory_mb: Optional[float] = Field(None, description="Peak memory usage")
    
    # Queue metrics
    average_queue_time_seconds: Optional[float] = Field(None, description="Average time in queue")
    current_queue_size: int = Field(..., description="Current number of queued jobs")
    
    # Error analysis
    most_common_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Common error patterns")
    retry_rate_percent: float = Field(..., description="Percentage of jobs that retry")


class JobNotificationSettings(BaseModel):
    """Job notification configuration"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    enabled: bool = Field(True, description="Whether notifications are enabled")
    notification_type: NotificationType = Field(NotificationType.EMAIL, description="Notification method")
    
    # Event triggers
    on_completion: bool = Field(True, description="Notify on job completion")
    on_failure: bool = Field(True, description="Notify on job failure")
    on_start: bool = Field(False, description="Notify on job start")
    on_retry: bool = Field(False, description="Notify on job retry")
    
    # Notification details
    recipient: str = Field(..., description="Notification recipient")
    custom_message: Optional[str] = Field(None, max_length=500, description="Custom notification message")
    include_logs: bool = Field(False, description="Include job logs in notification")


class JobScheduleOptions(BaseModel):
    """Job scheduling configuration"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Immediate vs scheduled
    run_now: bool = Field(True, description="Run job immediately")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule for specific time")
    
    # Recurring jobs
    is_recurring: bool = Field(False, description="Whether job repeats")
    recurrence_pattern: Optional[str] = Field(None, description="Cron-like recurrence pattern")
    max_occurrences: Optional[int] = Field(None, ge=1, description="Maximum number of executions")
    
    # Dependencies
    depends_on_jobs: Optional[List[str]] = Field(None, description="Jobs this job depends on")
    wait_for_dependencies: bool = Field(True, description="Wait for all dependencies to complete")
    
    # Timeout and retry
    timeout_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Job timeout")
    retry_on_failure: bool = Field(True, description="Retry failed jobs")
    max_retry_attempts: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_minutes: int = Field(1, ge=0, le=60, description="Delay between retries")


class JobResourceLimits(BaseModel):
    """Job resource allocation limits"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Memory limits
    max_memory_mb: Optional[int] = Field(None, ge=64, description="Maximum memory allocation")
    reserved_memory_mb: Optional[int] = Field(None, ge=32, description="Reserved memory")
    
    # CPU limits
    max_cpu_percent: Optional[float] = Field(None, ge=1, le=100, description="Maximum CPU usage")
    cpu_priority: str = Field("normal", regex="^(low|normal|high)$", description="CPU scheduling priority")
    
    # Storage limits
    max_disk_mb: Optional[int] = Field(None, ge=100, description="Maximum disk usage")
    temp_storage_mb: Optional[int] = Field(None, ge=50, description="Temporary storage allocation")
    
    # Network limits
    max_network_mbps: Optional[float] = Field(None, ge=1, description="Maximum network bandwidth")
    
    # Execution limits
    max_execution_time_minutes: Optional[int] = Field(None, ge=1, description="Maximum execution time")
    max_parallel_tasks: Optional[int] = Field(None, ge=1, le=100, description="Maximum parallel sub-tasks")


class BatchJobRequest(BaseModel):
    """Request for creating multiple jobs"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    jobs: List[JobCreationRequest] = Field(..., min_items=1, max_items=100, description="Jobs to create")
    batch_options: Optional[Dict[str, Any]] = Field(None, description="Batch-specific options")
    
    # Batch execution options
    run_in_parallel: bool = Field(False, description="Run jobs in parallel")
    stop_on_first_failure: bool = Field(False, description="Stop batch if any job fails")
    max_concurrent_jobs: Optional[int] = Field(None, ge=1, le=10, description="Maximum concurrent jobs")


class BatchJobResponse(BaseModel):
    """Response for batch job creation"""
    model_config = ConfigDict(from_attributes=True)
    
    batch_id: str = Field(..., description="Batch identifier")
    total_jobs: int = Field(..., description="Total number of jobs in batch")
    created_jobs: int = Field(..., description="Number of successfully created jobs")
    failed_jobs: int = Field(..., description="Number of jobs that failed to create")
    
    # Job details
    job_ids: List[str] = Field(..., description="List of created job IDs")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Creation errors")
    
    # Batch status
    batch_status: str = Field(..., description="Overall batch status")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated batch completion time")


# =============================================================================
# LEGACY COMPATIBILITY SCHEMAS
# =============================================================================

class LegacyJobRequest(BaseModel):
    """Legacy job request format for backwards compatibility"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='allow')
    
    job_type: str = Field(..., description="Job type as string")
    payload: Dict[str, Any] = Field(..., description="Job payload")
    
    # Optional legacy fields
    priority: Optional[str] = Field("normal", description="Job priority")
    timeout: Optional[int] = Field(None, description="Job timeout in seconds")
    
    def to_modern_format(self) -> JobCreationRequest:
        """Convert legacy request to modern format"""
        # Map legacy job types to new enum values
        type_mapping = {
            "data_proc": JobType.DATA_PROCESSING,
            "ml_train": JobType.ML_TRAINING,
            "ml_infer": JobType.ML_INFERENCE,
            "threat_scan": JobType.THREAT_ANALYSIS,
            "network_scan": JobType.NETWORK_SCAN,
        }
        
        priority_mapping = {
            "low": JobPriority.LOW,
            "normal": JobPriority.NORMAL,
            "high": JobPriority.HIGH,
            "critical": JobPriority.CRITICAL,
        }
        
        return JobCreationRequest(
            name=f"Legacy {self.job_type} Job",
            type=type_mapping.get(self.job_type, JobType.CUSTOM),
            priority=priority_mapping.get(self.priority, JobPriority.NORMAL),
            input_data=self.payload,
            timeout_minutes=self.timeout // 60 if self.timeout else None
        )


class LegacyJobResponse(BaseModel):
    """Legacy job response format"""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(..., description="Operation status")
    job_type: str = Field(..., description="Job type")
    task_id: Optional[str] = Field(None, description="Celery task ID")
    detail: Optional[str] = Field(None, description="Additional details")
    
    @classmethod
    def from_modern_response(cls, job_response: JobResponse) -> "LegacyJobResponse":
        """Convert modern response to legacy format"""
        return cls(
            status="success",
            job_type=job_response.job_type,
            task_id=job_response.id,
            detail=f"Job {job_response.job_id} created successfully"
        )


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_job_configuration(job_type: JobType, config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate job configuration based on job type"""
    required_fields = {
        JobType.DATA_PROCESSING: ["input_path", "output_path"],
        JobType.ML_TRAINING: ["model_type", "training_data"],
        JobType.ML_INFERENCE: ["model_path", "input_data"],
        JobType.THREAT_ANALYSIS: ["data_source"],
        JobType.NETWORK_SCAN: ["target_range"],
    }
    
    if job_type in required_fields:
        missing_fields = [field for field in required_fields[job_type] if field not in config]
        if missing_fields:
            raise ValueError(f"Missing required configuration fields for {job_type}: {missing_fields}")
    
    return config


def sanitize_job_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize job input data"""
    # Remove potentially dangerous keys
    dangerous_keys = ["__class__", "__module__", "__dict__", "exec", "eval"]
    sanitized = {k: v for k, v in input_data.items() if k not in dangerous_keys}
    
    # Limit string lengths
    for key, value in sanitized.items():
        if isinstance(value, str) and len(value) > 10000:
            sanitized[key] = value[:10000] + "... (truncated)"
    
    return sanitized
