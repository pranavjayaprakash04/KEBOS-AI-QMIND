"""
Comprehensive tests for the Audit Logger API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..common.models import Base, AuditLogORM, UserORM
from ..common.db import get_db
from .api import router
from .services import AuditLoggerService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audit_logger.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test app
app = FastAPI()
app.include_router(router, prefix="/audit_logger")


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = UserORM(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        role="operator"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.role = "operator"
    return user


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAuditLoggerAPI:
    """Test cases for audit logger API endpoints."""

    def test_create_audit_log_success(self, client, setup_database, mock_current_user):
        """Test successful audit log creation."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            response = client.post(
                "/audit_logger/log",
                json={
                    "action": "test_action",
                    "resource": "test_resource",
                    "details": {"key": "value"},
                    "success": True
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert "log_id" in data
            assert data["message"] == "Audit log created successfully"

    def test_create_audit_log_invalid_data(self, client, setup_database, mock_current_user):
        """Test audit log creation with invalid data."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            response = client.post(
                "/audit_logger/log",
                json={
                    "action": "",  # Empty action should fail
                    "resource": "test_resource"
                }
            )
            
            assert response.status_code == 422  # Validation error

    def test_create_audit_log_async(self, client, setup_database, mock_current_user):
        """Test asynchronous audit log creation."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            with patch("audit_logger.api.log_audit_action_async.delay") as mock_task:
                mock_task.return_value.id = "test-task-id"
                
                response = client.post(
                    "/audit_logger/log/async",
                    json={
                        "action": "test_action",
                        "resource": "test_resource",
                        "details": {"key": "value"}
                    }
                )
                
                assert response.status_code == 202
                data = response.json()
                assert data["status"] == "accepted"
                assert data["task_id"] == "test-task-id"

    def test_log_security_event(self, client, setup_database, mock_current_user):
        """Test security event logging."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            response = client.post(
                "/audit_logger/log/security",
                json={
                    "event_type": "threat_detected",
                    "severity": "high",
                    "description": "Suspicious network activity detected",
                    "source_ip": "192.168.1.100"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert "log_id" in data

    def test_log_threat_detection(self, client, setup_database, mock_current_user):
        """Test threat detection event logging."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            response = client.post(
                "/audit_logger/log/threat-detection",
                json={
                    "packet_info": {"src_ip": "192.168.1.100", "dst_ip": "10.0.0.1"},
                    "threat_level": "high",
                    "detection_result": {"confidence": 0.95, "type": "malware"}
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert "log_id" in data

    def test_log_model_operation(self, client, setup_database, mock_current_user):
        """Test model operation logging."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            response = client.post(
                "/audit_logger/log/model-operation",
                json={
                    "user_id": 1,
                    "operation": "upload",
                    "model_info": {"name": "test_model", "version": "1.0"},
                    "success": True
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert "log_id" in data

    def test_search_audit_logs(self, client, setup_database, test_user):
        """Test audit logs search functionality."""
        # Create some test audit logs
        db = TestingSessionLocal()
        try:
            for i in range(5):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type=f"test_action_{i}",
                    resource="test_resource",
                    success=True,
                    timestamp=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.add(log)
            db.commit()
        finally:
            db.close()

        mock_user = Mock()
        mock_user.id = test_user.id
        mock_user.permissions = ["audit:read"]
        
        with patch("audit_logger.api.require_permission", return_value=mock_user):
            response = client.get(
                "/audit_logger/logs",
                params={"user_id": test_user.id, "limit": 10}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "logs" in data
            assert data["total"] == 5
            assert len(data["logs"]) == 5

    def test_get_audit_log_by_id(self, client, setup_database, test_user):
        """Test retrieving specific audit log by ID."""
        # Create a test audit log
        db = TestingSessionLocal()
        try:
            log = AuditLogORM(
                user_id=test_user.id,
                action_type="test_action",
                resource="test_resource",
                success=True,
                timestamp=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            log_id = log.id
        finally:
            db.close()

        mock_user = Mock()
        mock_user.permissions = ["audit:read"]
        
        with patch("audit_logger.api.require_permission", return_value=mock_user):
            response = client.get(f"/audit_logger/logs/{log_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == log_id
            assert data["action_type"] == "test_action"

    def test_get_audit_log_not_found(self, client, setup_database):
        """Test retrieving non-existent audit log."""
        mock_user = Mock()
        mock_user.permissions = ["audit:read"]
        
        with patch("audit_logger.api.require_permission", return_value=mock_user):
            response = client.get("/audit_logger/logs/99999")
            
            assert response.status_code == 404

    def test_get_audit_statistics(self, client, setup_database, test_user):
        """Test audit statistics endpoint."""
        # Create some test audit logs
        db = TestingSessionLocal()
        try:
            for i in range(3):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type="test_action",
                    resource="test_resource",
                    success=i % 2 == 0,  # Mix of success/failure
                    timestamp=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.add(log)
            db.commit()
        finally:
            db.close()

        mock_user = Mock()
        mock_user.permissions = ["audit:read"]
        
        with patch("audit_logger.api.require_permission", return_value=mock_user):
            response = client.get("/audit_logger/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert "totals" in data
            assert "top_actions" in data

    def test_cleanup_audit_logs(self, client, setup_database):
        """Test audit logs cleanup endpoint."""
        mock_user = Mock()
        mock_user.permissions = ["audit:admin"]
        
        with patch("audit_logger.api.require_permission", return_value=mock_user):
            response = client.post(
                "/audit_logger/cleanup",
                params={"retention_days": 30}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "deleted_count" in data

    def test_cleanup_audit_logs_async(self, client, setup_database):
        """Test asynchronous audit logs cleanup."""
        mock_user = Mock()
        mock_user.permissions = ["audit:admin"]
        
        with patch("audit_logger.api.cleanup_old_logs_task.delay") as mock_task:
            mock_task.return_value.id = "cleanup-task-id"
            
            with patch("audit_logger.api.require_permission", return_value=mock_user):
                response = client.post(
                    "/audit_logger/cleanup",
                    params={"retention_days": 30, "async_cleanup": True}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "queued"
                assert data["task_id"] == "cleanup-task-id"

    def test_cleanup_invalid_retention(self, client, setup_database):
        """Test cleanup with invalid retention days."""
        mock_user = Mock()
        mock_user.permissions = ["audit:admin"]
        
        with patch("audit_logger.api.require_permission", return_value=mock_user):
            response = client.post(
                "/audit_logger/cleanup",
                params={"retention_days": 0}  # Invalid
            )
            
            assert response.status_code == 400

    def test_health_check(self, client, setup_database):
        """Test health check endpoint."""
        response = client.get("/audit_logger/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data

    def test_unauthorized_access(self, client, setup_database):
        """Test unauthorized access to protected endpoints."""
        # Test without authentication
        response = client.get("/audit_logger/logs")
        assert response.status_code == 401 or response.status_code == 403

    def test_input_validation(self, client, setup_database, mock_current_user):
        """Test input validation for various endpoints."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            # Test action too long
            response = client.post(
                "/audit_logger/log",
                json={
                    "action": "a" * 101,  # Exceeds max length
                    "resource": "test_resource"
                }
            )
            assert response.status_code == 422

            # Test invalid severity for security event
            response = client.post(
                "/audit_logger/log/security",
                json={
                    "event_type": "test",
                    "severity": "invalid_severity",
                    "description": "test description"
                }
            )
            assert response.status_code == 422

    def test_large_details_payload(self, client, setup_database, mock_current_user):
        """Test handling of large details payload."""
        with patch("audit_logger.api.get_current_user", return_value=mock_current_user):
            # Create a large details object
            large_details = {"data": "x" * 11000}  # Exceeds 10KB limit
            
            response = client.post(
                "/audit_logger/log",
                json={
                    "action": "test_action",
                    "resource": "test_resource",
                    "details": large_details
                }
            )
            
            # Should still succeed but details might be truncated
            assert response.status_code == 201
