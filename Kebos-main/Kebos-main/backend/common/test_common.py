"""
Test suite for the common module.
Comprehensive tests for models, services, utilities, and integrations.
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models import UserORM, ModelORM, AuditLogORM
from common.schemas import (
    UserCreate, UserUpdate, UserResponse, ModelMetadata,
    HealthCheckResponse, ValidationRequest, ValidationResponse,
    UtilityRequest, UtilityResponse, SystemInfo
)
from common.services import CommonService, common_service
from common.utils import (
    log_error, log_info, log_warning, validate_email, validate_uuid,
    sanitize_string, hash_password, verify_password, get_system_info,
    handle_error, CommonError, ValidationError, ConfigurationError,
    rate_limiter, cache, check_disk_space
)
from common.audit_logger import audit_logger


class TestCommonModels:
    """Test ORM models and Pydantic schemas."""
    
    def test_user_orm_creation(self):
        """Test UserORM model creation."""
        user = UserORM(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed123",
            is_active=True,
            role="operator"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.role == "operator"
    
    def test_model_orm_creation(self):
        """Test ModelORM model creation."""
        model = ModelORM(
            name="test_model",
            description="Test model",
            version="1.0.0",
            framework="scikit-learn",
            tags="test,ml"
        )
        
        assert model.name == "test_model"
        assert model.description == "Test model"
        assert model.version == "1.0.0"
        assert model.framework == "scikit-learn"
        assert model.tags == "test,ml"
    
    def test_audit_log_orm_creation(self):
        """Test AuditLogORM model creation."""
        log = AuditLogORM(
            action_type="login",
            user_id=1,
            resource="auth",
            details={"ip": "192.168.1.1"},
            success=True
        )
        
        assert log.action_type == "login"
        assert log.user_id == 1
        assert log.resource == "auth"
        assert log.details["ip"] == "192.168.1.1"
        assert log.success is True
    
    def test_user_create_schema(self):
        """Test UserCreate Pydantic schema."""
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "full_name": "New User",
            "password": "SecurePassword123!"
        }
        
        user = UserCreate(**user_data)
        
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert user.password == "SecurePassword123!"
    
    def test_user_create_email_validation(self):
        """Test email validation in UserCreate schema."""
        with pytest.raises(ValueError):
            UserCreate(
                username="user",
                email="invalid-email",
                full_name="User",
                password="password"
            )
    
    def test_validation_request_schema(self):
        """Test ValidationRequest schema."""
        request = ValidationRequest(
            data="test@example.com",
            data_type="email",
            validation_rules={"required": True},
            strict_mode=True
        )
        
        assert request.data == "test@example.com"
        assert request.data_type == "email"
        assert request.validation_rules["required"] is True
        assert request.strict_mode is True


class TestCommonUtils:
    """Test utility functions."""
    
    def test_validate_email(self):
        """Test email validation utility."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name+tag@domain.co.uk") is True
        assert validate_email("invalid-email") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False
    
    def test_validate_uuid(self):
        """Test UUID validation utility."""
        import uuid
        
        valid_uuid = str(uuid.uuid4())
        assert validate_uuid(valid_uuid) is True
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("123-456-789") is False
    
    def test_sanitize_string(self):
        """Test string sanitization utility."""
        # Basic sanitization
        result = sanitize_string("Hello World")
        assert result == "Hello World"
        
        # Script tag removal
        result = sanitize_string("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result
        
        # Length limiting
        long_string = "A" * 1000
        result = sanitize_string(long_string, max_length=10)
        assert len(result) == 10
        
        # HTML preservation
        html_content = "<p>Safe <strong>HTML</strong></p>"
        result = sanitize_string(html_content, allow_html=True)
        assert "<p>" in result
        assert "<strong>" in result
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed, salt = hash_password(password)
        
        assert hashed != password
        assert salt is not None
        assert len(hashed) > 0
        assert len(salt) > 0
        
        # Verify correct password
        assert verify_password(password, hashed, salt) is True
        
        # Verify incorrect password
        assert verify_password("wrongpassword", hashed, salt) is False
    
    def test_get_system_info(self):
        """Test system information gathering."""
        info = get_system_info()
        
        assert isinstance(info, dict)
        assert "platform" in info
        assert "python_version" in info
        assert "cpu_count" in info
        assert "memory_total" in info
        assert "timestamp" in info
    
    def test_handle_error(self):
        """Test error handling utility."""
        # Test with exception
        try:
            raise ValueError("Test error")
        except Exception as e:
            result = handle_error(e, "test_component", {"context": "test"})
            
            assert result["status"] == "error"
            assert result["error_type"] == "ValueError"
            assert result["message"] == "Test error"
            assert result["component"] == "test_component"
    
    @pytest.mark.asyncio
    async def test_rate_limiter(self):
        """Test rate limiting functionality."""
        # Test successful rate limit
        result1 = await rate_limiter.check_rate_limit("test_key", max_requests=2, window_seconds=60)
        assert result1 is True
        
        result2 = await rate_limiter.check_rate_limit("test_key", max_requests=2, window_seconds=60)
        assert result2 is True
        
        # Third request should be rate limited
        result3 = await rate_limiter.check_rate_limit("test_key", max_requests=2, window_seconds=60)
        assert result3 is False
    
    @pytest.mark.asyncio
    async def test_cache(self):
        """Test caching functionality."""
        # Set cache value
        await cache.set("test_key", "test_value", ttl=60)
        
        # Get cache value
        result = await cache.get("test_key")
        assert result == "test_value"
        
        # Test cache miss
        result = await cache.get("nonexistent_key")
        assert result is None
        
        # Test cache deletion
        await cache.delete("test_key")
        result = await cache.get("test_key")
        assert result is None
    
    def test_check_disk_space(self):
        """Test disk space checking."""
        result = check_disk_space("/", min_free_gb=0.1)
        
        assert isinstance(result, dict)
        assert "total_gb" in result
        assert "free_gb" in result
        assert "used_gb" in result
        assert "free_percent" in result
        assert "has_sufficient_space" in result


class TestCommonServices:
    """Test common services."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = CommonService()
    
    @pytest.mark.asyncio
    async def test_validate_data_email(self):
        """Test data validation for email."""
        request = ValidationRequest(
            data="test@example.com",
            data_type="email",
            validation_rules={"required": True},
            strict_mode=True
        )
        
        response = await self.service.validate_data(request)
        
        assert response.status == "success"
        assert response.is_valid is True
        assert len(response.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_data_invalid_email(self):
        """Test data validation for invalid email."""
        request = ValidationRequest(
            data="invalid-email",
            data_type="email",
            validation_rules={"required": True},
            strict_mode=True
        )
        
        response = await self.service.validate_data(request)
        
        assert response.status == "validation_failed"
        assert response.is_valid is False
        assert len(response.errors) > 0
        assert "Invalid email format" in response.errors
    
    @pytest.mark.asyncio
    async def test_validate_data_string_length(self):
        """Test string length validation."""
        request = ValidationRequest(
            data="short",
            data_type="string",
            validation_rules={"min_length": 10, "max_length": 50},
            strict_mode=True
        )
        
        response = await self.service.validate_data(request)
        
        assert response.status == "validation_failed"
        assert response.is_valid is False
        assert any("too short" in error for error in response.errors)
    
    @pytest.mark.asyncio
    async def test_validate_data_json(self):
        """Test JSON validation."""
        json_data = '{"key": "value", "number": 42}'
        request = ValidationRequest(
            data=json_data,
            data_type="json",
            validation_rules={"max_size": 1000},
            strict_mode=True
        )
        
        response = await self.service.validate_data(request)
        
        assert response.status == "success"
        assert response.is_valid is True
        assert "parsed_data" in response.metadata
        assert response.metadata["parsed_data"]["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_get_health_status(self):
        """Test health status check."""
        response = await self.service.get_health_status()
        
        assert isinstance(response, HealthCheckResponse)
        assert response.service == "common"
        assert response.version == "1.0.0"
        assert response.status in ["healthy", "degraded", "unhealthy", "error"]
        assert hasattr(response, "database")
        assert hasattr(response, "celery")
        assert hasattr(response, "dependencies")
    
    @pytest.mark.asyncio
    async def test_execute_utility_hash_password(self):
        """Test password hashing utility."""
        request = UtilityRequest(
            operation="hash_password",
            parameters={"password": "testpassword123"},
            options={}
        )
        
        response = await self.service.execute_utility(request)
        
        assert response.status == "success"
        assert "hashed_password" in response.result
        assert "salt" in response.result
        assert response.metadata["algorithm"] == "pbkdf2_hmac_sha256"
    
    @pytest.mark.asyncio
    async def test_execute_utility_verify_password(self):
        """Test password verification utility."""
        # First hash a password
        password = "testpassword123"
        hashed, salt = hash_password(password)
        
        request = UtilityRequest(
            operation="verify_password",
            parameters={
                "password": password,
                "hashed_password": hashed,
                "salt": salt
            },
            options={}
        )
        
        response = await self.service.execute_utility(request)
        
        assert response.status == "success"
        assert response.result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_execute_utility_sanitize_string(self):
        """Test string sanitization utility."""
        request = UtilityRequest(
            operation="sanitize_string",
            parameters={
                "text": "<script>alert('xss')</script>Hello World",
                "max_length": 100,
                "allow_html": False
            },
            options={}
        )
        
        response = await self.service.execute_utility(request)
        
        assert response.status == "success"
        assert "<script>" not in response.result["sanitized_text"]
        assert "Hello World" in response.result["sanitized_text"]
    
    @pytest.mark.asyncio
    async def test_execute_utility_generate_id(self):
        """Test ID generation utility."""
        request = UtilityRequest(
            operation="generate_id",
            parameters={"type": "uuid"},
            options={}
        )
        
        response = await self.service.execute_utility(request)
        
        assert response.status == "success"
        assert "id" in response.result
        assert validate_uuid(response.result["id"]) is True
    
    @pytest.mark.asyncio
    async def test_execute_utility_system_info(self):
        """Test system info utility."""
        request = UtilityRequest(
            operation="system_info",
            parameters={},
            options={}
        )
        
        response = await self.service.execute_utility(request)
        
        assert response.status == "success"
        assert "platform" in response.result
        assert "python_version" in response.result
        assert "cpu_count" in response.result
    
    @pytest.mark.asyncio
    async def test_execute_utility_invalid_operation(self):
        """Test invalid utility operation."""
        request = UtilityRequest(
            operation="invalid_operation",
            parameters={},
            options={}
        )
        
        response = await self.service.execute_utility(request)
        
        assert response.status == "validation_error"
        assert "Unknown operation" in response.message
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self):
        """Test system metrics gathering."""
        metrics = await self.service.get_system_metrics()
        
        assert isinstance(metrics, dict)
        assert "timestamp" in metrics
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "process" in metrics
        
        # Check CPU metrics
        assert "percent" in metrics["cpu"]
        assert "count" in metrics["cpu"]
        
        # Check memory metrics
        assert "total" in metrics["memory"]
        assert "available" in metrics["memory"]
        assert "percent" in metrics["memory"]
    
    @pytest.mark.asyncio
    async def test_cleanup_resources_dry_run(self):
        """Test resource cleanup in dry run mode."""
        results = await self.service.cleanup_resources(
            older_than_days=30,
            dry_run=True
        )
        
        assert isinstance(results, dict)
        assert "cutoff_date" in results
        assert results["dry_run"] is True
        assert "audit_logs" in results
        assert "temp_files" in results
        
        # In dry run mode, nothing should be deleted
        assert results["audit_logs"]["deleted"] == 0
        assert results["temp_files"]["deleted"] == 0


class TestAuditLogger:
    """Test audit logging functionality."""
    
    @pytest.mark.asyncio
    async def test_log_user_event(self):
        """Test user event logging."""
        with patch('common.audit_logger.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            await audit_logger.log_user_event(
                user_id="user123",
                action="login",
                component="auth",
                details={"ip": "192.168.1.1"},
                severity="info"
            )
            
            # Verify database call
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_system_event(self):
        """Test system event logging."""
        with patch('common.audit_logger.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            await audit_logger.log_system_event(
                event_type="system_startup",
                component="api",
                details={"version": "1.0.0"}
            )
            
            # Verify database call
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_security_event(self):
        """Test security event logging."""
        with patch('common.audit_logger.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            await audit_logger.log_security_event(
                event_type="failed_login",
                user_id="user123",
                component="auth",
                details={"attempts": 3, "ip": "192.168.1.1"},
                severity="warning"
            )
            
            # Verify database call
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()


class TestWorkflowAPI:
    """Test workflow API functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    def test_workflow_schemas(self):
        """Test workflow-related schemas."""
        # This would test workflow schemas when they're defined
        pass


# Fixtures for testing
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }


@pytest.fixture
def sample_model_data():
    """Sample model data for testing."""
    return {
        "name": "test_model",
        "model_type": "ml",
        "version": "1.0.0",
        "description": "Test model for unit testing",
        "metadata": {"accuracy": 0.95, "framework": "scikit-learn"}
    }


# Integration tests
class TestCommonIntegration:
    """Integration tests for common module components."""
    
    @pytest.mark.asyncio
    async def test_service_validation_integration(self):
        """Test integration between service and validation utilities."""
        service = CommonService()
        
        # Test email validation through service
        request = ValidationRequest(
            data="test@example.com",
            data_type="email",
            validation_rules={"required": True},
            strict_mode=True
        )
        
        response = await service.validate_data(request)
        assert response.is_valid is True
        
        # Test with utility function directly
        direct_result = validate_email("test@example.com")
        assert direct_result is True
    
    @pytest.mark.asyncio
    async def test_service_utility_integration(self):
        """Test integration between service and utility functions."""
        service = CommonService()
        
        # Test password operations through service
        hash_request = UtilityRequest(
            operation="hash_password",
            parameters={"password": "testpassword"},
            options={}
        )
        
        hash_response = await service.execute_utility(hash_request)
        assert hash_response.status == "success"
        
        hashed = hash_response.result["hashed_password"]
        salt = hash_response.result["salt"]
        
        # Verify through service
        verify_request = UtilityRequest(
            operation="verify_password",
            parameters={
                "password": "testpassword",
                "hashed_password": hashed,
                "salt": salt
            },
            options={}
        )
        
        verify_response = await service.execute_utility(verify_request)
        assert verify_response.status == "success"
        assert verify_response.result["valid"] is True
        
        # Test with utility functions directly
        direct_hashed, direct_salt = hash_password("testpassword")
        direct_verify = verify_password("testpassword", direct_hashed, direct_salt)
        assert direct_verify is True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
