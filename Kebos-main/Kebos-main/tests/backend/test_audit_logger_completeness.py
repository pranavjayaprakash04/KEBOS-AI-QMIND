"""
Simple smoke tests for the Audit Logger module to verify completion.
"""
import pytest
import asyncio


def test_audit_logger_imports():
    """Test that all audit logger components can be imported."""
    from audit_logger import services, schemas, api, tasks
    from audit_logger.services import AuditLoggerService
    from audit_logger.schemas import (
        AuditLogCreateRequest, AuditLogResponse, 
        AuditLogSearchRequest, AuditLogSearchResponse
    )
    
    # Verify classes can be instantiated
    service = AuditLoggerService()
    assert service is not None
    
    # Verify schemas work
    search_request = AuditLogSearchRequest(limit=10, offset=0)
    assert search_request.limit == 10
    assert search_request.offset == 0


def test_audit_logger_service_methods():
    """Test that service methods exist and have correct signatures."""
    from audit_logger.services import AuditLoggerService
    import inspect
    
    service = AuditLoggerService()
    
    # Check core methods exist
    assert hasattr(service, 'log_event')
    assert hasattr(service, 'log_security_event')
    assert hasattr(service, 'log_threat_detection')
    assert hasattr(service, 'log_model_operation')
    assert hasattr(service, 'log_user_action')
    assert hasattr(service, 'search_audit_logs')
    assert hasattr(service, 'get_audit_statistics')
    assert hasattr(service, 'cleanup_old_logs')
    
    # Verify methods are async
    assert asyncio.iscoroutinefunction(service.log_event)
    assert asyncio.iscoroutinefunction(service.log_security_event)
    assert asyncio.iscoroutinefunction(service.search_audit_logs)


def test_audit_logger_schemas():
    """Test that schemas are properly defined with validation."""
    from audit_logger.schemas import (
        AuditLogCreateRequest, SecurityEventCreateRequest,
        ThreatDetectionLogRequest, ModelOperationLogRequest,
        SeverityLevel, AuditActionType, ResourceType
    )
    from datetime import datetime
    
    # Test enums
    assert SeverityLevel.HIGH == "high"
    assert AuditActionType.LOGIN == "login"
    assert ResourceType.USER == "user"
    
    # Test basic schema validation
    audit_request = AuditLogCreateRequest(action="test_action")
    assert audit_request.action == "test_action"
    assert audit_request.success is True  # default value
    
    security_event = SecurityEventCreateRequest(
        event_type="test_event",
        severity=SeverityLevel.HIGH,
        description="Test security event"
    )
    assert security_event.severity == SeverityLevel.HIGH


def test_audit_logger_api_endpoints():
    """Test that API endpoints are properly defined."""
    from audit_logger.api import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)
    
    # Check that routes are defined
    routes = [route.path for route in router.routes]
    
    # Should have key endpoints
    expected_paths = ["/health", "/logs", "/statistics", "/cleanup"]
    for path in expected_paths:
        assert any(path in route for route in routes), f"Missing route containing {path}"


def test_audit_logger_tasks():
    """Test that Celery tasks are properly defined."""
    from audit_logger import tasks
    
    # Check that task functions exist
    assert hasattr(tasks, 'log_audit_action_async')
    assert hasattr(tasks, 'cleanup_old_logs_task')
    assert hasattr(tasks, 'generate_audit_report_task')


def test_requirements_file_exists():
    """Test that requirements.txt exists and has basic dependencies."""
    import os
    from pathlib import Path
    
    audit_logger_dir = Path(__file__).parent
    requirements_file = audit_logger_dir / "requirements.txt"
    
    assert requirements_file.exists(), "requirements.txt should exist"
    
    # Read and check for key dependencies
    with open(requirements_file, 'r') as f:
        content = f.read()
    
    # Should have core dependencies
    assert "fastapi" in content.lower()
    assert "pydantic" in content.lower()
    assert "sqlalchemy" in content.lower()
    assert "celery" in content.lower()


def test_module_completeness():
    """Test that the audit logger module is feature-complete."""
    from audit_logger.services import AuditLoggerService
    from audit_logger.schemas import AuditLogSearchRequest
    import inspect
    
    service = AuditLoggerService()
    
    # Verify log_event has comprehensive parameters
    log_event_sig = inspect.signature(service.log_event)
    log_params = list(log_event_sig.parameters.keys())
    
    expected_params = ['user_id', 'action', 'resource', 'details', 'ip_address', 'user_agent', 'success']
    for param in expected_params:
        assert param in log_params, f"log_event missing parameter: {param}"
    
    # Verify search has proper filtering
    search_sig = inspect.signature(AuditLogSearchRequest)
    search_params = list(search_sig.parameters.keys())
    
    expected_search_params = ['user_id', 'action', 'resource', 'start_time', 'end_time', 'success', 'limit', 'offset']
    for param in expected_search_params:
        assert param in search_params, f"AuditLogSearchRequest missing parameter: {param}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
