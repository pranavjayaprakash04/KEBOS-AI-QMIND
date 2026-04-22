"""
Comprehensive tests for the Audit Logger Service layer.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any

from ..common.models import Base, AuditLogORM, UserORM
from .services import AuditLoggerService
from .schemas import AuditLogSearchRequest

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audit_service.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    # Check if user already exists
    existing_user = db_session.query(UserORM).filter(UserORM.email == "test@example.com").first()
    if existing_user:
        return existing_user
        
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
def audit_service():
    """Create audit logger service instance."""
    return AuditLoggerService()


class TestAuditLoggerService:
    """Test cases for audit logger service methods."""

    @pytest.mark.asyncio
    async def test_log_event_success(self, audit_service, setup_database, test_user):
        """Test successful event logging."""
        db = TestingSessionLocal()
        try:
            log_id = await audit_service.log_event(
                user_id=test_user.id,
                action="test_action",
                resource="test_resource",
                details={"key": "value"},
                ip_address="192.168.1.100",
                user_agent="test-agent",
                success=True,
                db=db
            )
            
            assert log_id is not None
            
            # Verify log was created
            log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
            assert log is not None
            assert log.action_type == "test_action"
            assert log.resource == "test_resource"
            assert log.user_id == test_user.id
            assert log.success is True
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_log_event_validation(self, audit_service, setup_database):
        """Test event logging with validation."""
        db = TestingSessionLocal()
        try:
            # Test empty action
            log_id = await audit_service.log_event(
                action="",
                db=db
            )
            assert log_id is None
            
            # Test action truncation
            long_action = "a" * 150  # Exceeds 100 char limit
            log_id = await audit_service.log_event(
                action=long_action,
                db=db
            )
            assert log_id is not None
            
            # Verify action was truncated
            log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
            assert len(log.action_type) == 100
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_log_event_large_details(self, audit_service, setup_database):
        """Test event logging with large details payload."""
        db = TestingSessionLocal()
        try:
            # Create large details object
            large_details = {"data": "x" * 11000}  # Exceeds 10KB limit
            
            log_id = await audit_service.log_event(
                action="test_action",
                details=large_details,
                db=db
            )
            
            assert log_id is not None
            
            # Verify details were truncated
            log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
            assert "error" in log.details
            assert "Details truncated" in log.details["error"]
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_log_security_event(self, audit_service, setup_database, test_user):
        """Test security event logging."""
        db = TestingSessionLocal()
        try:
            log_id = await audit_service.log_security_event(
                event_type="threat_detected",
                severity="high",
                description="Suspicious activity detected",
                source_ip="192.168.1.100",
                user_id=test_user.id,
                additional_data={"confidence": 0.95}
            )
            
            assert log_id is not None
            
            # Verify security event was logged
            log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
            assert log.action_type == "security_threat_detected"
            assert log.resource == "security_system"
            assert log.details["severity"] == "high"
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_log_threat_detection(self, audit_service, setup_database, test_user):
        """Test threat detection event logging."""
        db = TestingSessionLocal()
        try:
            packet_info = {"src_ip": "192.168.1.100", "dst_ip": "10.0.0.1"}
            detection_result = {"confidence": 0.95, "type": "malware"}
            
            log_id = await audit_service.log_threat_detection(
                user_id=test_user.id,
                packet_info=packet_info,
                threat_level="high",
                detection_result=detection_result
            )
            
            assert log_id is not None
            
            # Verify threat detection was logged
            log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
            assert log.action_type == "threat_detection"
            assert log.resource == "network_packet"
            assert log.details["packet_info"] == packet_info
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_log_model_operation(self, audit_service, setup_database, test_user):
        """Test model operation logging."""
        db = TestingSessionLocal()
        try:
            model_info = {"name": "test_model", "version": "1.0"}
            
            log_id = await audit_service.log_model_operation(
                user_id=test_user.id,
                operation="upload",
                model_info=model_info,
                success=True
            )
            
            assert log_id is not None
            
            # Verify model operation was logged
            log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
            assert log.action_type == "model_upload"
            assert log.resource == "model"
            assert log.details == model_info
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_log_user_action(self, audit_service, setup_database, test_user):
        """Test user action logging."""
        db = TestingSessionLocal()
        try:
            log_id = await audit_service.log_user_action(
                user_id=test_user.id,
                action="login",
                target_user_id=test_user.id,
                details={"login_method": "password"},
                ip_address="192.168.1.100",
                success=True
            )
            
            assert log_id is not None
            
            # Verify user action was logged
            log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
            assert log.action_type == "login"
            assert log.resource == f"user/{test_user.id}"
            assert log.ip_address == "192.168.1.100"
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_search_audit_logs(self, audit_service, setup_database, test_user):
        """Test audit logs search functionality."""
        db = TestingSessionLocal()
        try:
            # Create test audit logs
            now = datetime.utcnow()
            for i in range(5):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type=f"action_{i}",
                    resource="test_resource",
                    success=i % 2 == 0,
                    timestamp=now - timedelta(hours=i),
                    created_at=now
                )
                db.add(log)
            db.commit()
            
            # Test basic search
            search_params = AuditLogSearchRequest(
                user_id=test_user.id,
                limit=10,
                offset=0
            )
            
            result = await audit_service.search_audit_logs(search_params, db)
            
            assert len(result.logs) == 5
            assert result.total == 5
            assert result.limit == 10
            assert result.offset == 0
            
            # Test filtered search
            search_params = AuditLogSearchRequest(
                user_id=test_user.id,
                action="action_1",
                success=True,
                limit=10,
                offset=0
            )
            
            result = await audit_service.search_audit_logs(search_params, db)
            
            # Should find action_1 which has success=False, so no results
            assert len(result.logs) == 0
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_get_audit_log_by_id(self, audit_service, setup_database, test_user):
        """Test retrieving audit log by ID."""
        db = TestingSessionLocal()
        try:
            # Create test audit log
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
            
            # Test successful retrieval
            result = await audit_service.get_audit_log_by_id(log.id, db)
            
            assert result is not None
            assert result.id == log.id
            assert result.action_type == "test_action"
            assert result.user_id == test_user.id
            
            # Test non-existent log
            result = await audit_service.get_audit_log_by_id(99999, db)
            assert result is None
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_get_audit_statistics(self, audit_service, setup_database, test_user):
        """Test audit statistics generation."""
        db = TestingSessionLocal()
        try:
            # Create test audit logs
            now = datetime.utcnow()
            for i in range(10):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type="login" if i < 5 else "logout",
                    resource="user",
                    success=i % 3 != 0,  # Mix of success/failure
                    timestamp=now - timedelta(hours=i),
                    created_at=now
                )
                db.add(log)
            db.commit()
            
            # Test statistics generation
            start_time = now - timedelta(hours=12)
            end_time = now
            
            stats = await audit_service.get_audit_statistics(start_time, end_time, db)
            
            assert "totals" in stats
            assert "top_actions" in stats
            assert "top_users" in stats
            assert stats["totals"]["total_events"] == 10
            assert stats["totals"]["successful_events"] == 7  # 10 - 3 failures
            assert stats["totals"]["failed_events"] == 3
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, audit_service, setup_database, test_user):
        """Test cleanup of old audit logs."""
        db = TestingSessionLocal()
        try:
            # Create old and new audit logs
            now = datetime.utcnow()
            old_date = now - timedelta(days=100)
            
            # Old logs (should be deleted)
            for i in range(3):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type=f"old_action_{i}",
                    resource="test_resource",
                    success=True,
                    timestamp=old_date,
                    created_at=old_date
                )
                db.add(log)
            
            # New logs (should be kept)
            for i in range(2):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type=f"new_action_{i}",
                    resource="test_resource",
                    success=True,
                    timestamp=now,
                    created_at=now
                )
                db.add(log)
            
            db.commit()
            
            # Verify initial count
            total_logs = db.query(AuditLogORM).count()
            assert total_logs == 5
            
            # Cleanup logs older than 90 days
            deleted_count = await audit_service.cleanup_old_logs(90, db)
            
            assert deleted_count == 3
            
            # Verify remaining logs
            remaining_logs = db.query(AuditLogORM).count()
            assert remaining_logs == 2
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_error_handling(self, audit_service):
        """Test error handling in service methods."""
        # Test with invalid database session
        with patch("backend.audit_logger.services.get_db") as mock_get_db:
            mock_get_db.return_value = Mock(side_effect=Exception("DB Error"))
            
            # Should handle database errors gracefully
            log_id = await audit_service.log_event(
                action="test_action",
                resource="test_resource"
            )
            
            assert log_id is None

    @pytest.mark.asyncio
    async def test_search_with_time_filters(self, audit_service, setup_database, test_user):
        """Test search with time-based filters."""
        db = TestingSessionLocal()
        try:
            # Create logs at different times
            base_time = datetime.utcnow()
            times = [
                base_time - timedelta(hours=2),  # 2 hours ago
                base_time - timedelta(hours=1),  # 1 hour ago
                base_time  # now
            ]
            
            for i, timestamp in enumerate(times):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type=f"action_{i}",
                    resource="test_resource",
                    success=True,
                    timestamp=timestamp,
                    created_at=timestamp
                )
                db.add(log)
            db.commit()
            
            # Search for logs in the last hour
            search_params = AuditLogSearchRequest(
                start_time=base_time - timedelta(hours=1, minutes=30),
                end_time=base_time + timedelta(minutes=10),
                limit=10,
                offset=0
            )
            
            result = await audit_service.search_audit_logs(search_params, db)
            
            # Should find the last 2 logs
            assert len(result.logs) == 2
            assert result.total == 2
            
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_pagination(self, audit_service, setup_database, test_user):
        """Test search pagination."""
        db = TestingSessionLocal()
        try:
            # Create 15 test logs
            for i in range(15):
                log = AuditLogORM(
                    user_id=test_user.id,
                    action_type=f"action_{i:02d}",
                    resource="test_resource",
                    success=True,
                    timestamp=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.add(log)
            db.commit()
            
            # Test first page
            search_params = AuditLogSearchRequest(
                limit=5,
                offset=0
            )
            
            result = await audit_service.search_audit_logs(search_params, db)
            
            assert len(result.logs) == 5
            assert result.total == 15
            assert result.offset == 0
            
            # Test second page
            search_params.offset = 5
            
            result = await audit_service.search_audit_logs(search_params, db)
            
            assert len(result.logs) == 5
            assert result.total == 15
            assert result.offset == 5
            
        finally:
            db.close()
