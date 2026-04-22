"""
Job Manager Configuration

This module contains configuration settings for the job management system,
including Celery configuration, Redis settings, job execution parameters,
and environment-specific configurations.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import timedelta
from pydantic import BaseSettings, Field, validator
from enum import Enum

# =============================================================================
# ENUMS FOR CONFIGURATION
# =============================================================================

class EnvironmentType(str, Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class QueuePriority(str, Enum):
    """Queue priority levels"""
    LOW = "low_priority"
    NORMAL = "normal_priority"
    HIGH = "high_priority"
    CRITICAL = "critical_priority"


# =============================================================================
# MAIN CONFIGURATION CLASS
# =============================================================================

class JobManagerSettings(BaseSettings):
    """Main configuration class for job management system"""
    
    # =============================================================================
    # ENVIRONMENT SETTINGS
    # =============================================================================
    
    environment: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT,
        env="JOB_MANAGER_ENVIRONMENT",
        description="Deployment environment"
    )
    
    debug: bool = Field(
        default=True,
        env="JOB_MANAGER_DEBUG",
        description="Enable debug mode"
    )
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        env="JOB_MANAGER_LOG_LEVEL",
        description="Logging level"
    )
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/kebos_ctp",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    
    database_pool_size: int = Field(
        default=20,
        env="DATABASE_POOL_SIZE",
        description="Database connection pool size"
    )
    
    database_max_overflow: int = Field(
        default=30,
        env="DATABASE_MAX_OVERFLOW",
        description="Database connection pool overflow"
    )
    
    database_pool_timeout: int = Field(
        default=30,
        env="DATABASE_POOL_TIMEOUT",
        description="Database connection timeout in seconds"
    )
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    
    redis_max_connections: int = Field(
        default=100,
        env="REDIS_MAX_CONNECTIONS",
        description="Maximum Redis connections"
    )
    
    redis_socket_timeout: float = Field(
        default=30.0,
        env="REDIS_SOCKET_TIMEOUT",
        description="Redis socket timeout in seconds"
    )
    
    redis_socket_connect_timeout: float = Field(
        default=30.0,
        env="REDIS_SOCKET_CONNECT_TIMEOUT",
        description="Redis connection timeout in seconds"
    )
    
    # =============================================================================
    # CELERY CONFIGURATION
    # =============================================================================
    
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_BROKER_URL",
        description="Celery broker URL"
    )
    
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_RESULT_BACKEND",
        description="Celery result backend URL"
    )
    
    celery_task_serializer: str = Field(
        default="json",
        env="CELERY_TASK_SERIALIZER",
        description="Celery task serialization format"
    )
    
    celery_result_serializer: str = Field(
        default="json",
        env="CELERY_RESULT_SERIALIZER",
        description="Celery result serialization format"
    )
    
    celery_accept_content: List[str] = Field(
        default=["json"],
        env="CELERY_ACCEPT_CONTENT",
        description="Accepted content types for Celery"
    )
    
    celery_timezone: str = Field(
        default="UTC",
        env="CELERY_TIMEZONE",
        description="Celery timezone"
    )
    
    celery_enable_utc: bool = Field(
        default=True,
        env="CELERY_ENABLE_UTC",
        description="Enable UTC in Celery"
    )
    
    # Worker settings
    celery_worker_concurrency: int = Field(
        default=4,
        env="CELERY_WORKER_CONCURRENCY",
        description="Number of worker processes"
    )
    
    celery_worker_prefetch_multiplier: int = Field(
        default=4,
        env="CELERY_WORKER_PREFETCH_MULTIPLIER",
        description="Worker prefetch multiplier"
    )
    
    celery_task_acks_late: bool = Field(
        default=True,
        env="CELERY_TASK_ACKS_LATE",
        description="Acknowledge tasks after completion"
    )
    
    celery_worker_max_tasks_per_child: int = Field(
        default=1000,
        env="CELERY_WORKER_MAX_TASKS_PER_CHILD",
        description="Maximum tasks per worker child"
    )
    
    # Task routing
    celery_task_routes: Dict[str, Dict[str, str]] = Field(
        default={
            "job_manager.tasks.execute_job": {"queue": "job_execution"},
            "job_manager.tasks.send_notification": {"queue": "notifications"},
            "job_manager.tasks.cleanup_jobs": {"queue": "maintenance"},
            "job_manager.tasks.health_check": {"queue": "health"},
        },
        description="Celery task routing configuration"
    )
    
    # =============================================================================
    # JOB EXECUTION SETTINGS
    # =============================================================================
    
    default_job_timeout: int = Field(
        default=3600,  # 1 hour
        env="DEFAULT_JOB_TIMEOUT",
        description="Default job timeout in seconds"
    )
    
    max_job_timeout: int = Field(
        default=86400,  # 24 hours
        env="MAX_JOB_TIMEOUT",
        description="Maximum job timeout in seconds"
    )
    
    default_retry_attempts: int = Field(
        default=3,
        env="DEFAULT_RETRY_ATTEMPTS",
        description="Default number of retry attempts"
    )
    
    max_retry_attempts: int = Field(
        default=10,
        env="MAX_RETRY_ATTEMPTS",
        description="Maximum number of retry attempts"
    )
    
    retry_delay_seconds: int = Field(
        default=60,
        env="RETRY_DELAY_SECONDS",
        description="Delay between retry attempts in seconds"
    )
    
    max_concurrent_jobs: int = Field(
        default=100,
        env="MAX_CONCURRENT_JOBS",
        description="Maximum number of concurrent jobs"
    )
    
    job_cleanup_interval: int = Field(
        default=3600,  # 1 hour
        env="JOB_CLEANUP_INTERVAL",
        description="Job cleanup interval in seconds"
    )
    
    job_retention_days: int = Field(
        default=30,
        env="JOB_RETENTION_DAYS",
        description="Number of days to retain completed jobs"
    )
    
    # =============================================================================
    # QUEUE CONFIGURATION
    # =============================================================================
    
    queue_names: Dict[str, str] = Field(
        default={
            "default": "default",
            "high_priority": "high_priority",
            "low_priority": "low_priority",
            "job_execution": "job_execution",
            "notifications": "notifications",
            "maintenance": "maintenance",
            "health": "health",
        },
        description="Queue name mappings"
    )
    
    queue_priorities: Dict[str, int] = Field(
        default={
            "critical_priority": 10,
            "high_priority": 7,
            "normal_priority": 5,
            "low_priority": 3,
            "maintenance": 1,
        },
        description="Queue priority levels"
    )
    
    # =============================================================================
    # RESOURCE LIMITS
    # =============================================================================
    
    default_memory_limit_mb: int = Field(
        default=512,
        env="DEFAULT_MEMORY_LIMIT_MB",
        description="Default memory limit per job in MB"
    )
    
    max_memory_limit_mb: int = Field(
        default=4096,
        env="MAX_MEMORY_LIMIT_MB",
        description="Maximum memory limit per job in MB"
    )
    
    default_cpu_limit_percent: float = Field(
        default=50.0,
        env="DEFAULT_CPU_LIMIT_PERCENT",
        description="Default CPU limit per job as percentage"
    )
    
    max_cpu_limit_percent: float = Field(
        default=100.0,
        env="MAX_CPU_LIMIT_PERCENT",
        description="Maximum CPU limit per job as percentage"
    )
    
    default_disk_limit_mb: int = Field(
        default=1024,
        env="DEFAULT_DISK_LIMIT_MB",
        description="Default disk limit per job in MB"
    )
    
    max_disk_limit_mb: int = Field(
        default=10240,
        env="MAX_DISK_LIMIT_MB",
        description="Maximum disk limit per job in MB"
    )
    
    # =============================================================================
    # NOTIFICATION SETTINGS
    # =============================================================================
    
    enable_notifications: bool = Field(
        default=True,
        env="ENABLE_NOTIFICATIONS",
        description="Enable job notifications"
    )
    
    smtp_server: Optional[str] = Field(
        default=None,
        env="SMTP_SERVER",
        description="SMTP server for email notifications"
    )
    
    smtp_port: int = Field(
        default=587,
        env="SMTP_PORT",
        description="SMTP server port"
    )
    
    smtp_username: Optional[str] = Field(
        default=None,
        env="SMTP_USERNAME",
        description="SMTP username"
    )
    
    smtp_password: Optional[str] = Field(
        default=None,
        env="SMTP_PASSWORD",
        description="SMTP password"
    )
    
    smtp_use_tls: bool = Field(
        default=True,
        env="SMTP_USE_TLS",
        description="Use TLS for SMTP"
    )
    
    notification_from_email: str = Field(
        default="noreply@kebos.local",
        env="NOTIFICATION_FROM_EMAIL",
        description="From email address for notifications"
    )
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    
    enable_job_isolation: bool = Field(
        default=True,
        env="ENABLE_JOB_ISOLATION",
        description="Enable job execution isolation"
    )
    
    allowed_job_types: Optional[List[str]] = Field(
        default=None,
        env="ALLOWED_JOB_TYPES",
        description="List of allowed job types (None = all allowed)"
    )
    
    blocked_job_types: List[str] = Field(
        default=[],
        env="BLOCKED_JOB_TYPES",
        description="List of blocked job types"
    )
    
    require_job_approval: bool = Field(
        default=False,
        env="REQUIRE_JOB_APPROVAL",
        description="Require approval for job execution"
    )
    
    max_job_payload_size_mb: int = Field(
        default=100,
        env="MAX_JOB_PAYLOAD_SIZE_MB",
        description="Maximum job payload size in MB"
    )
    
    # =============================================================================
    # MONITORING AND HEALTH
    # =============================================================================
    
    health_check_interval: int = Field(
        default=300,  # 5 minutes
        env="HEALTH_CHECK_INTERVAL",
        description="Health check interval in seconds"
    )
    
    metrics_collection_enabled: bool = Field(
        default=True,
        env="METRICS_COLLECTION_ENABLED",
        description="Enable metrics collection"
    )
    
    metrics_retention_days: int = Field(
        default=7,
        env="METRICS_RETENTION_DAYS",
        description="Number of days to retain metrics"
    )
    
    alert_on_job_failure: bool = Field(
        default=True,
        env="ALERT_ON_JOB_FAILURE",
        description="Send alerts on job failures"
    )
    
    alert_on_queue_backlog: bool = Field(
        default=True,
        env="ALERT_ON_QUEUE_BACKLOG",
        description="Send alerts on queue backlogs"
    )
    
    max_queue_size_alert_threshold: int = Field(
        default=1000,
        env="MAX_QUEUE_SIZE_ALERT_THRESHOLD",
        description="Queue size threshold for alerts"
    )
    
    # =============================================================================
    # DEVELOPMENT AND TESTING
    # =============================================================================
    
    enable_test_mode: bool = Field(
        default=False,
        env="ENABLE_TEST_MODE",
        description="Enable test mode (disables some features)"
    )
    
    mock_external_services: bool = Field(
        default=False,
        env="MOCK_EXTERNAL_SERVICES",
        description="Mock external services for testing"
    )
    
    log_sql_queries: bool = Field(
        default=False,
        env="LOG_SQL_QUERIES",
        description="Log SQL queries (for debugging)"
    )
    
    enable_profiling: bool = Field(
        default=False,
        env="ENABLE_PROFILING",
        description="Enable performance profiling"
    )
    
    # =============================================================================
    # VALIDATORS
    # =============================================================================
    
    @validator('celery_worker_concurrency')
    def validate_worker_concurrency(cls, v):
        if v < 1:
            raise ValueError('Worker concurrency must be at least 1')
        if v > 32:
            raise ValueError('Worker concurrency should not exceed 32')
        return v
    
    @validator('default_job_timeout')
    def validate_default_timeout(cls, v, values):
        max_timeout = values.get('max_job_timeout', 86400)
        if v > max_timeout:
            raise ValueError(f'Default timeout cannot exceed max timeout ({max_timeout})')
        return v
    
    @validator('job_retention_days')
    def validate_retention_days(cls, v):
        if v < 1:
            raise ValueError('Job retention must be at least 1 day')
        if v > 365:
            raise ValueError('Job retention should not exceed 365 days')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# =============================================================================
# CELERY CONFIGURATION BUILDER
# =============================================================================

def build_celery_config(settings: JobManagerSettings) -> Dict[str, Any]:
    """Build Celery configuration from settings"""
    return {
        # Broker and backend
        'broker_url': settings.celery_broker_url,
        'result_backend': settings.celery_result_backend,
        
        # Serialization
        'task_serializer': settings.celery_task_serializer,
        'result_serializer': settings.celery_result_serializer,
        'accept_content': settings.celery_accept_content,
        
        # Timezone
        'timezone': settings.celery_timezone,
        'enable_utc': settings.celery_enable_utc,
        
        # Worker settings
        'worker_concurrency': settings.celery_worker_concurrency,
        'worker_prefetch_multiplier': settings.celery_worker_prefetch_multiplier,
        'task_acks_late': settings.celery_task_acks_late,
        'worker_max_tasks_per_child': settings.celery_worker_max_tasks_per_child,
        
        # Task routing
        'task_routes': settings.celery_task_routes,
        
        # Task execution
        'task_time_limit': settings.max_job_timeout,
        'task_soft_time_limit': settings.default_job_timeout,
        
        # Result settings
        'result_expires': 3600,  # 1 hour
        'result_persistent': True,
        
        # Monitoring
        'worker_send_task_events': True,
        'task_send_sent_event': True,
        
        # Security
        'worker_hijack_root_logger': False,
        'worker_log_color': settings.debug,
        
        # Beat schedule (for periodic tasks)
        'beat_schedule': {
            'cleanup-jobs': {
                'task': 'job_manager.tasks.cleanup_jobs',
                'schedule': timedelta(seconds=settings.job_cleanup_interval),
            },
            'health-check': {
                'task': 'job_manager.tasks.health_check',
                'schedule': timedelta(seconds=settings.health_check_interval),
            },
        },
        
        # Additional broker options
        'broker_connection_retry_on_startup': True,
        'broker_connection_retry': True,
        'broker_connection_max_retries': 10,
    }


# =============================================================================
# CONFIGURATION INSTANCE
# =============================================================================

# Global configuration instance
job_manager_settings = JobManagerSettings()

# Celery configuration
celery_config = build_celery_config(job_manager_settings)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_queue_for_priority(priority: str) -> str:
    """Get queue name for given priority"""
    priority_queue_mapping = {
        "critical": "critical_priority",
        "high": "high_priority", 
        "normal": "normal_priority",
        "low": "low_priority",
    }
    return priority_queue_mapping.get(priority.lower(), "normal_priority")


def get_job_timeout(job_type: str, custom_timeout: Optional[int] = None) -> int:
    """Get timeout for job based on type and custom settings"""
    if custom_timeout:
        return min(custom_timeout, job_manager_settings.max_job_timeout)
    
    # Default timeouts by job type
    job_type_timeouts = {
        "data_processing": 3600,  # 1 hour
        "ml_training": 14400,     # 4 hours  
        "ml_inference": 1800,     # 30 minutes
        "threat_analysis": 7200,  # 2 hours
        "network_scan": 1800,     # 30 minutes
        "custom": 3600,           # 1 hour
    }
    
    timeout = job_type_timeouts.get(job_type.lower(), job_manager_settings.default_job_timeout)
    return min(timeout, job_manager_settings.max_job_timeout)


def is_job_type_allowed(job_type: str) -> bool:
    """Check if job type is allowed"""
    if job_type in job_manager_settings.blocked_job_types:
        return False
    
    if job_manager_settings.allowed_job_types is None:
        return True
        
    return job_type in job_manager_settings.allowed_job_types


def get_resource_limits(job_type: str) -> Dict[str, Any]:
    """Get resource limits for job type"""
    # Default limits by job type
    type_limits = {
        "data_processing": {
            "memory_mb": 1024,
            "cpu_percent": 75.0,
            "disk_mb": 2048,
        },
        "ml_training": {
            "memory_mb": 2048,
            "cpu_percent": 90.0,
            "disk_mb": 4096,
        },
        "ml_inference": {
            "memory_mb": 512,
            "cpu_percent": 50.0,
            "disk_mb": 1024,
        },
        "threat_analysis": {
            "memory_mb": 1024,
            "cpu_percent": 60.0,
            "disk_mb": 2048,
        },
        "network_scan": {
            "memory_mb": 256,
            "cpu_percent": 40.0,
            "disk_mb": 512,
        },
    }
    
    limits = type_limits.get(job_type.lower(), {
        "memory_mb": job_manager_settings.default_memory_limit_mb,
        "cpu_percent": job_manager_settings.default_cpu_limit_percent,
        "disk_mb": job_manager_settings.default_disk_limit_mb,
    })
    
    # Ensure limits don't exceed maximums
    limits["memory_mb"] = min(limits["memory_mb"], job_manager_settings.max_memory_limit_mb)
    limits["cpu_percent"] = min(limits["cpu_percent"], job_manager_settings.max_cpu_limit_percent)
    limits["disk_mb"] = min(limits["disk_mb"], job_manager_settings.max_disk_limit_mb)
    
    return limits


def get_environment_config() -> Dict[str, Any]:
    """Get environment-specific configuration"""
    env_configs = {
        EnvironmentType.DEVELOPMENT: {
            "debug": True,
            "log_level": "DEBUG",
            "enable_profiling": True,
            "mock_external_services": True,
        },
        EnvironmentType.TESTING: {
            "debug": True,
            "log_level": "INFO",
            "enable_test_mode": True,
            "mock_external_services": True,
        },
        EnvironmentType.STAGING: {
            "debug": False,
            "log_level": "INFO",
            "enable_test_mode": False,
            "mock_external_services": False,
        },
        EnvironmentType.PRODUCTION: {
            "debug": False,
            "log_level": "WARNING",
            "enable_test_mode": False,
            "mock_external_services": False,
        },
    }
    
    return env_configs.get(job_manager_settings.environment, env_configs[EnvironmentType.DEVELOPMENT])
