"""
Common Exception Classes

This module contains custom exception classes used throughout the backend
application for consistent error handling and reporting.
"""

from typing import Optional, Dict, Any, List
import traceback
from datetime import datetime


class BaseApplicationError(Exception):
    """Base class for all application-specific exceptions"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        self.traceback_str = traceback.format_exc() if cause else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback_str
        }
    
    def __str__(self) -> str:
        base_str = f"{self.__class__.__name__}: {self.message}"
        if self.error_code and self.error_code != self.__class__.__name__:
            base_str += f" (Code: {self.error_code})"
        return base_str


# =============================================================================
# VALIDATION EXCEPTIONS
# =============================================================================

class ValidationError(BaseApplicationError):
    """Raised when input validation fails"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        
        super().__init__(message, error_code="VALIDATION_ERROR", details=details, **kwargs)
        self.field = field
        self.value = value


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails"""
    
    def __init__(self, message: str = "Schema validation failed", schema: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if schema:
            details['schema'] = schema
        
        super().__init__(message, error_code="SCHEMA_VALIDATION_ERROR", details=details, **kwargs)
        self.schema = schema


class ConfigurationError(BaseApplicationError):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str = "Configuration error", config_key: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(message, error_code="CONFIGURATION_ERROR", details=details, **kwargs)
        self.config_key = config_key


# =============================================================================
# RESOURCE EXCEPTIONS
# =============================================================================

class ResourceError(BaseApplicationError):
    """Base class for resource-related exceptions"""
    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource is not found"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        
        super().__init__(message, error_code="RESOURCE_NOT_FOUND", details=details, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceAlreadyExistsError(ResourceError):
    """Raised when trying to create a resource that already exists"""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        
        super().__init__(message, error_code="RESOURCE_ALREADY_EXISTS", details=details, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceLimitExceededError(ResourceError):
    """Raised when resource limits are exceeded"""
    
    def __init__(
        self,
        message: str = "Resource limit exceeded",
        resource_type: Optional[str] = None,
        limit: Optional[Any] = None,
        current: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if limit is not None:
            details['limit'] = str(limit)
        if current is not None:
            details['current'] = str(current)
        
        super().__init__(message, error_code="RESOURCE_LIMIT_EXCEEDED", details=details, **kwargs)
        self.resource_type = resource_type
        self.limit = limit
        self.current = current


class ResourceUnavailableError(ResourceError):
    """Raised when a resource is temporarily unavailable"""
    
    def __init__(
        self,
        message: str = "Resource temporarily unavailable",
        resource_type: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if retry_after:
            details['retry_after'] = retry_after
        
        super().__init__(message, error_code="RESOURCE_UNAVAILABLE", details=details, **kwargs)
        self.resource_type = resource_type
        self.retry_after = retry_after


# =============================================================================
# DATABASE EXCEPTIONS
# =============================================================================

class DatabaseError(BaseApplicationError):
    """Base class for database-related exceptions"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    
    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(message, error_code="DATABASE_CONNECTION_ERROR", **kwargs)


class DatabaseOperationError(DatabaseError):
    """Raised when database operation fails"""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if operation:
            details['operation'] = operation
        
        super().__init__(message, error_code="DATABASE_OPERATION_ERROR", details=details, **kwargs)
        self.operation = operation


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraints are violated"""
    
    def __init__(
        self,
        message: str = "Database integrity constraint violated",
        constraint: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if constraint:
            details['constraint'] = constraint
        
        super().__init__(message, error_code="DATABASE_INTEGRITY_ERROR", details=details, **kwargs)
        self.constraint = constraint


# =============================================================================
# AUTHENTICATION & AUTHORIZATION EXCEPTIONS
# =============================================================================

class AuthenticationError(BaseApplicationError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(BaseApplicationError):
    """Raised when authorization/permission check fails"""
    
    def __init__(
        self,
        message: str = "Authorization failed",
        required_permission: Optional[str] = None,
        user_permissions: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if required_permission:
            details['required_permission'] = required_permission
        if user_permissions:
            details['user_permissions'] = user_permissions
        
        super().__init__(message, error_code="AUTHORIZATION_ERROR", details=details, **kwargs)
        self.required_permission = required_permission
        self.user_permissions = user_permissions


class TokenError(AuthenticationError):
    """Raised when token validation fails"""
    
    def __init__(
        self,
        message: str = "Token validation failed",
        token_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if token_type:
            details['token_type'] = token_type
        
        super().__init__(message, error_code="TOKEN_ERROR", details=details, **kwargs)
        self.token_type = token_type


# =============================================================================
# BUSINESS LOGIC EXCEPTIONS
# =============================================================================

class BusinessLogicError(BaseApplicationError):
    """Raised when business logic rules are violated"""
    
    def __init__(
        self,
        message: str = "Business logic error",
        rule: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if rule:
            details['rule'] = rule
        
        super().__init__(message, error_code="BUSINESS_LOGIC_ERROR", details=details, **kwargs)
        self.rule = rule


class StateError(BusinessLogicError):
    """Raised when an operation is invalid for current state"""
    
    def __init__(
        self,
        message: str = "Invalid state for operation",
        current_state: Optional[str] = None,
        required_state: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if current_state:
            details['current_state'] = current_state
        if required_state:
            details['required_state'] = required_state
        
        super().__init__(message, error_code="STATE_ERROR", details=details, **kwargs)
        self.current_state = current_state
        self.required_state = required_state


class DependencyError(BusinessLogicError):
    """Raised when dependency requirements are not met"""
    
    def __init__(
        self,
        message: str = "Dependency requirements not met",
        missing_dependencies: Optional[List[str]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if missing_dependencies:
            details['missing_dependencies'] = missing_dependencies
        
        super().__init__(message, error_code="DEPENDENCY_ERROR", details=details, **kwargs)
        self.missing_dependencies = missing_dependencies


# =============================================================================
# EXTERNAL SERVICE EXCEPTIONS
# =============================================================================

class ExternalServiceError(BaseApplicationError):
    """Base class for external service-related exceptions"""
    pass


class ServiceUnavailableError(ExternalServiceError):
    """Raised when external service is unavailable"""
    
    def __init__(
        self,
        message: str = "External service unavailable",
        service_name: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if service_name:
            details['service_name'] = service_name
        
        super().__init__(message, error_code="SERVICE_UNAVAILABLE", details=details, **kwargs)
        self.service_name = service_name


class ServiceTimeoutError(ExternalServiceError):
    """Raised when external service request times out"""
    
    def __init__(
        self,
        message: str = "External service timeout",
        service_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if service_name:
            details['service_name'] = service_name
        if timeout_seconds:
            details['timeout_seconds'] = timeout_seconds
        
        super().__init__(message, error_code="SERVICE_TIMEOUT", details=details, **kwargs)
        self.service_name = service_name
        self.timeout_seconds = timeout_seconds


class APIError(ExternalServiceError):
    """Raised when external API returns an error"""
    
    def __init__(
        self,
        message: str = "API error",
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        api_response: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if api_name:
            details['api_name'] = api_name
        if status_code:
            details['status_code'] = status_code
        if api_response:
            details['api_response'] = api_response
        
        super().__init__(message, error_code="API_ERROR", details=details, **kwargs)
        self.api_name = api_name
        self.status_code = status_code
        self.api_response = api_response


# =============================================================================
# JOB MANAGEMENT SPECIFIC EXCEPTIONS
# =============================================================================

class JobError(BaseApplicationError):
    """Base class for job-related exceptions"""
    pass


class JobNotFoundError(JobError, ResourceNotFoundError):
    """Raised when a job is not found"""
    
    def __init__(self, job_id: str, **kwargs):
        super().__init__(
            message=f"Job not found: {job_id}",
            error_code="JOB_NOT_FOUND",
            resource_type="job",
            resource_id=job_id,
            **kwargs
        )


class JobExecutionError(JobError):
    """Raised when job execution fails"""
    
    def __init__(
        self,
        message: str = "Job execution failed",
        job_id: Optional[str] = None,
        job_type: Optional[str] = None,
        exit_code: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if job_id:
            details['job_id'] = job_id
        if job_type:
            details['job_type'] = job_type
        if exit_code is not None:
            details['exit_code'] = exit_code
        
        super().__init__(message, error_code="JOB_EXECUTION_ERROR", details=details, **kwargs)
        self.job_id = job_id
        self.job_type = job_type
        self.exit_code = exit_code


class JobTimeoutError(JobError):
    """Raised when job execution times out"""
    
    def __init__(
        self,
        message: str = "Job execution timed out",
        job_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if job_id:
            details['job_id'] = job_id
        if timeout_seconds:
            details['timeout_seconds'] = timeout_seconds
        
        super().__init__(message, error_code="JOB_TIMEOUT_ERROR", details=details, **kwargs)
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds


class JobCancellationError(JobError):
    """Raised when job cancellation fails"""
    
    def __init__(
        self,
        message: str = "Job cancellation failed",
        job_id: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if job_id:
            details['job_id'] = job_id
        if reason:
            details['reason'] = reason
        
        super().__init__(message, error_code="JOB_CANCELLATION_ERROR", details=details, **kwargs)
        self.job_id = job_id
        self.reason = reason


class QueueError(JobError):
    """Raised when queue operations fail"""
    
    def __init__(
        self,
        message: str = "Queue operation failed",
        queue_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if queue_name:
            details['queue_name'] = queue_name
        if operation:
            details['operation'] = operation
        
        super().__init__(message, error_code="QUEUE_ERROR", details=details, **kwargs)
        self.queue_name = queue_name
        self.operation = operation


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def handle_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    reraise_as: Optional[type] = None
) -> None:
    """Handle and optionally convert exceptions"""
    if isinstance(exception, BaseApplicationError):
        if context:
            exception.details.update(context)
        if reraise_as and not isinstance(exception, reraise_as):
            raise reraise_as(
                message=str(exception),
                details=exception.details,
                cause=exception
            ) from exception
        raise exception
    
    # Convert standard exceptions to application exceptions
    if reraise_as:
        details = context or {}
        details['original_exception'] = str(exception)
        details['original_type'] = type(exception).__name__
        
        raise reraise_as(
            message=f"Converted from {type(exception).__name__}: {str(exception)}",
            details=details,
            cause=exception
        ) from exception
    
    # Re-raise original exception if no conversion specified
    raise exception


def format_exception_for_response(exception: Exception) -> Dict[str, Any]:
    """Format exception for API response"""
    if isinstance(exception, BaseApplicationError):
        return {
            "error": True,
            "error_type": exception.__class__.__name__,
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details,
            "timestamp": exception.timestamp.isoformat()
        }
    
    return {
        "error": True,
        "error_type": type(exception).__name__,
        "error_code": "UNKNOWN_ERROR",
        "message": str(exception),
        "details": {},
        "timestamp": datetime.utcnow().isoformat()
    }


def create_error_response(
    message: str,
    error_code: str = "GENERIC_ERROR",
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": True,
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code
    }
