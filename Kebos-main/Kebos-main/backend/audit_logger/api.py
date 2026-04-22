"""
Audit Logger API
Comprehensive RESTful API for audit logging with validation and security.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

try:
    from ..common.db import get_db
    from ..auth.dependencies import get_current_user, require_permission
except ImportError:
    # Fallback for testing
    from common.db import get_db
    from auth.dependencies import get_current_user, require_permission
from .schemas import (
    AuditLogCreateRequest, AuditLogCreateResponse, AuditLogSearchRequest,
    AuditLogSearchResponse, AuditLogResponse, SecurityEventCreateRequest,
    ThreatDetectionLogRequest, ModelOperationLogRequest, HealthCheckResponse,
    ErrorResponse
)
from .services import AuditLoggerService
from .tasks import log_audit_action_async, cleanup_old_logs_task

router = APIRouter(tags=["audit"])
security = HTTPBearer()
audit_service = AuditLoggerService()


def get_client_info(request: Request) -> Dict[str, Optional[str]]:
    """Extract client information from request."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }


@router.post(
    "/log",
    response_model=AuditLogCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create audit log entry",
    description="Log an audit event with comprehensive details and validation."
)
async def create_audit_log(
    request: AuditLogCreateRequest,
    http_request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AuditLogCreateResponse:
    """Create a new audit log entry."""
    try:
        client_info = get_client_info(http_request)
        
        # Override user_id with current authenticated user if not provided
        user_id = request.user_id or current_user.id
        
        log_id = await audit_service.log_event(
            user_id=user_id,
            action=request.action,
            resource=request.resource,
            details=request.details,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            success=request.success,
            db=db
        )
        
        if log_id:
            return AuditLogCreateResponse(
                status="success",
                log_id=log_id,
                message="Audit log created successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create audit log"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/log/async",
    response_model=AuditLogCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create audit log entry asynchronously",
    description="Log an audit event asynchronously using Celery for high-throughput scenarios."
)
async def create_audit_log_async(
    request: AuditLogCreateRequest,
    http_request: Request,
    current_user = Depends(get_current_user)
) -> AuditLogCreateResponse:
    """Create an audit log entry asynchronously."""
    try:
        client_info = get_client_info(http_request)
        
        # Override user_id with current authenticated user if not provided
        user_id = request.user_id or current_user.id
        
        task = log_audit_action_async.delay(
            action=request.action,
            user_id=user_id,
            resource=request.resource,
            details=request.details,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            success=request.success
        )
        
        return AuditLogCreateResponse(
            status="accepted",
            task_id=task.id,
            message="Audit log queued for processing"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue audit log"
        )


@router.post(
    "/log/security",
    response_model=AuditLogCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log security event",
    description="Log a security-related event with severity classification."
)
async def log_security_event(
    request: SecurityEventCreateRequest,
    http_request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AuditLogCreateResponse:
    """Log a security event."""
    try:
        client_info = get_client_info(http_request)
        
        log_id = await audit_service.log_security_event(
            event_type=request.event_type,
            severity=request.severity.value,
            description=request.description,
            source_ip=request.source_ip or client_info["ip_address"],
            user_id=request.user_id or current_user.id,
            additional_data=request.additional_data
        )
        
        if log_id:
            return AuditLogCreateResponse(
                status="success",
                log_id=log_id,
                message="Security event logged successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log security event"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/log/threat-detection",
    response_model=AuditLogCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log threat detection event",
    description="Log a threat detection event with packet and detection details."
)
async def log_threat_detection(
    request: ThreatDetectionLogRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AuditLogCreateResponse:
    """Log a threat detection event."""
    try:
        log_id = await audit_service.log_threat_detection(
            user_id=request.user_id or current_user.id,
            packet_info=request.packet_info,
            threat_level=request.threat_level,
            detection_result=request.detection_result
        )
        
        if log_id:
            return AuditLogCreateResponse(
                status="success",
                log_id=log_id,
                message="Threat detection event logged successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log threat detection event"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/log/model-operation",
    response_model=AuditLogCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log model operation",
    description="Log a machine learning model operation."
)
async def log_model_operation(
    request: ModelOperationLogRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AuditLogCreateResponse:
    """Log a model operation."""
    try:
        log_id = await audit_service.log_model_operation(
            user_id=request.user_id,
            operation=request.operation,
            model_info=request.model_info,
            success=request.success
        )
        
        if log_id:
            return AuditLogCreateResponse(
                status="success",
                log_id=log_id,
                message="Model operation logged successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log model operation"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/logs",
    response_model=AuditLogSearchResponse,
    summary="Search audit logs",
    description="Search and filter audit logs with pagination."
)
async def search_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    success: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    current_user = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
) -> AuditLogSearchResponse:
    """Search audit logs with filtering and pagination."""
    try:
        search_params = AuditLogSearchRequest(
            user_id=user_id,
            action=action,
            resource=resource,
            start_time=start_time,
            end_time=end_time,
            success=success,
            limit=min(limit, 1000),  # Cap at 1000
            offset=offset
        )
        
        return await audit_service.search_audit_logs(search_params, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search audit logs"
        )


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogResponse,
    summary="Get audit log by ID",
    description="Retrieve a specific audit log entry by its ID."
)
async def get_audit_log(
    log_id: int,
    current_user = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
) -> AuditLogResponse:
    """Get a specific audit log by ID."""
    try:
        audit_log = await audit_service.get_audit_log_by_id(log_id, db)
        
        if not audit_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )
        
        return audit_log
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log"
        )


@router.get(
    "/statistics",
    response_model=Dict[str, Any],
    summary="Get audit statistics",
    description="Get audit log statistics for monitoring and reporting."
)
async def get_audit_statistics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get audit log statistics."""
    try:
        return await audit_service.get_audit_statistics(start_time, end_time, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit statistics"
        )


@router.post(
    "/cleanup",
    response_model=Dict[str, Any],
    summary="Cleanup old audit logs",
    description="Clean up audit logs older than specified retention period."
)
async def cleanup_audit_logs(
    retention_days: int = 90,
    async_cleanup: bool = False,
    current_user = Depends(require_permission("audit:admin")),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Clean up old audit logs."""
    try:
        if retention_days < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Retention days must be at least 1"
            )
        
        if async_cleanup:
            # Queue cleanup task
            task = cleanup_old_logs_task.delay(retention_days)
            return {
                "status": "queued",
                "task_id": task.id,
                "message": f"Cleanup task queued for logs older than {retention_days} days"
            }
        else:
            # Synchronous cleanup
            deleted_count = await audit_service.cleanup_old_logs(retention_days, db)
            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "message": f"Cleaned up {deleted_count} audit logs older than {retention_days} days"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup audit logs"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check the health status of the audit logger service."
)
async def health_check(
    db: Session = Depends(get_db)
) -> HealthCheckResponse:
    """Health check endpoint."""
    try:
        # Test database connection
        try:
            db.execute("SELECT 1")
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"
        
        # Test Celery connection (basic check)
        try:
            from ..common.celery_app import celery_app
            celery_status = "healthy" if celery_app else "unhealthy"
        except Exception:
            celery_status = "unhealthy"
        
        # Overall status
        overall_status = "healthy" if all([
            database_status == "healthy",
            celery_status == "healthy"
        ]) else "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            database=database_status,
            celery=celery_status,
            storage="healthy",  # Placeholder
            timestamp=datetime.utcnow(),
            version="1.0.0"
        )
        
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            database="unknown",
            celery="unknown",
            storage="unknown",
            timestamp=datetime.utcnow(),
            version="1.0.0"
        )
