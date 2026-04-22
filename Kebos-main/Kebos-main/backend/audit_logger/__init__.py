"""
Audit Logger Module

Comprehensive audit logging system for the AI Governance Platform.
Handles logging of all critical operations, user actions, and system events
for traceability, compliance, and security monitoring.

Features:
- Comprehensive audit event logging with database persistence
- Security event and threat detection logging
- User action and model operation tracking
- Asynchronous processing with Celery
- Advanced search and filtering capabilities
- Audit statistics and reporting
- Compliance features (data retention, cleanup)
- Health monitoring and error handling

Components:
- api.py: RESTful API endpoints for audit logging
- services.py: Business logic and database operations
- schemas.py: Pydantic models for validation
- tasks.py: Celery background tasks
- models.py: Database models (in common.models)

Usage:
    from audit_logger.services import AuditLoggerService
    
    service = AuditLoggerService()
    await service.log_event(
        user_id=1,
        action="user_login",
        resource="authentication",
        details={"method": "password"},
        success=True
    )
"""

from .services import AuditLoggerService
from .schemas import (
    AuditLogCreateRequest,
    AuditLogCreateResponse,
    AuditLogSearchRequest,
    AuditLogSearchResponse,
    AuditLogResponse,
    SecurityEventCreateRequest,
    ThreatDetectionLogRequest,
    ModelOperationLogRequest,
    HealthCheckResponse,
    ErrorResponse,
    SeverityLevel,
    AuditActionType,
    ResourceType
)
from .api import router

__all__ = [
    "AuditLoggerService",
    "AuditLogCreateRequest",
    "AuditLogCreateResponse", 
    "AuditLogSearchRequest",
    "AuditLogSearchResponse",
    "AuditLogResponse",
    "SecurityEventCreateRequest",
    "ThreatDetectionLogRequest",
    "ModelOperationLogRequest",
    "HealthCheckResponse",
    "ErrorResponse",
    "SeverityLevel",
    "AuditActionType",
    "ResourceType",
    "router"
]
