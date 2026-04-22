"""
Tests for audit logger Celery tasks.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..common.models import Base, AuditLogORM, UserORM
from .tasks import (
    log_audit_action_async, cleanup_old_logs_task,
    generate_audit_report_task, batch_log_events_task,
    log_audit_action
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audit_tasks.db"
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


class TestAuditLoggerTasks:
    """Test cases for audit logger Celery tasks."""

    def test_log_audit_action_async_success(self, setup_database, test_user):
        """Test successful asynchronous audit logging."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            mock_db = TestingSessionLocal()
            mock_get_db.return_value = mock_db
            
            # Create mock task
            mock_task = Mock()
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            
            try:
                result = log_audit_action_async(
                    mock_task,
                    action="test_action",
                    user_id=test_user.id,
                    resource="test_resource",
                    details={"key": "value"},
                    ip_address="192.168.1.100",
                    success=True
                )
                
                assert result["status"] == "success"
                assert "log_id" in result
                assert result["action"] == "test_action"
                assert result["user_id"] == test_user.id
                
                # Verify log was created in database
                log = mock_db.query(AuditLogORM).filter(
                    AuditLogORM.id == result["log_id"]
                ).first()
                assert log is not None
                assert log.action_type == "test_action"
                assert log.user_id == test_user.id
                
            finally:
                mock_db.close()

    def test_log_audit_action_async_retry(self, setup_database):
        """Test retry mechanism for failed audit logging."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            # Mock database failure
            mock_get_db.side_effect = Exception("Database connection failed")
            
            # Create mock task with retry capability
            mock_task = Mock()
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            mock_task.retry = Mock(side_effect=Exception("Retry called"))
            
            with pytest.raises(Exception, match="Retry called"):
                log_audit_action_async(
                    mock_task,
                    action="test_action",
                    user_id=1,
                    resource="test_resource"
                )
            
            # Verify retry was called
            mock_task.retry.assert_called_once()

    def test_log_audit_action_async_max_retries(self, setup_database):
        """Test handling of max retries exceeded."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            # Mock database failure
            mock_get_db.side_effect = Exception("Database connection failed")
            
            # Create mock task that has exceeded max retries
            mock_task = Mock()
            mock_task.request.retries = 3
            mock_task.max_retries = 3
            
            result = log_audit_action_async(
                mock_task,
                action="test_action",
                user_id=1,
                resource="test_resource"
            )
            
            assert result["status"] == "error"
            assert "Database connection failed" in result["error"]
            assert result["retries"] == 3

    def test_cleanup_old_logs_task_success(self, setup_database, test_user):
        """Test successful cleanup of old logs."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            mock_db = TestingSessionLocal()
            mock_get_db.return_value = mock_db
            
            try:
                # Create old and new logs
                now = datetime.utcnow()
                old_date = now - timedelta(days=100)
                
                # Old logs
                for i in range(3):
                    log = AuditLogORM(
                        user_id=test_user.id,
                        action_type=f"old_action_{i}",
                        resource="test_resource",
                        success=True,
                        timestamp=old_date,
                        created_at=old_date
                    )
                    mock_db.add(log)
                
                # New logs
                for i in range(2):
                    log = AuditLogORM(
                        user_id=test_user.id,
                        action_type=f"new_action_{i}",
                        resource="test_resource",
                        success=True,
                        timestamp=now,
                        created_at=now
                    )
                    mock_db.add(log)
                
                mock_db.commit()
                
                # Create mock task
                mock_task = Mock()
                mock_task.request.retries = 0
                mock_task.max_retries = 2
                
                result = cleanup_old_logs_task(mock_task, retention_days=90)
                
                assert result["status"] == "success"
                assert result["deleted_count"] == 3
                assert result["retention_days"] == 90
                
                # Verify old logs were deleted
                remaining_logs = mock_db.query(AuditLogORM).count()
                assert remaining_logs == 2
                
            finally:
                mock_db.close()

    def test_cleanup_old_logs_task_failure(self, setup_database):
        """Test cleanup task failure and retry."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            # Mock database failure
            mock_get_db.side_effect = Exception("Database error")
            
            # Create mock task with retry capability
            mock_task = Mock()
            mock_task.request.retries = 0
            mock_task.max_retries = 2
            mock_task.retry = Mock(side_effect=Exception("Retry called"))
            
            with pytest.raises(Exception, match="Retry called"):
                cleanup_old_logs_task(mock_task, retention_days=90)
            
            mock_task.retry.assert_called_once()

    def test_generate_audit_report_task_success(self, setup_database, test_user):
        """Test successful audit report generation."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            mock_db = TestingSessionLocal()
            mock_get_db.return_value = mock_db
            
            try:
                # Create test logs
                now = datetime.utcnow()
                for i in range(5):
                    log = AuditLogORM(
                        user_id=test_user.id,
                        action_type="login" if i < 3 else "logout",
                        resource="user",
                        success=i % 2 == 0,
                        timestamp=now - timedelta(hours=i),
                        created_at=now
                    )
                    mock_db.add(log)
                mock_db.commit()
                
                # Create mock task
                mock_task = Mock()
                
                start_time = (now - timedelta(hours=6)).isoformat()
                end_time = now.isoformat()
                
                result = generate_audit_report_task(
                    mock_task,
                    start_time=start_time,
                    end_time=end_time,
                    user_id=test_user.id,
                    report_format="json"
                )
                
                assert result["status"] == "success"
                assert "report_data" in result
                assert result["format"] == "json"
                
                report_data = result["report_data"]
                assert report_data["report_type"] == "audit_summary"
                assert "statistics" in report_data
                assert "totals" in report_data["statistics"]
                
            finally:
                mock_db.close()

    def test_generate_audit_report_task_failure(self, setup_database):
        """Test audit report generation failure."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            # Mock database failure
            mock_get_db.side_effect = Exception("Database error")
            
            mock_task = Mock()
            
            start_time = datetime.utcnow().isoformat()
            end_time = datetime.utcnow().isoformat()
            
            result = generate_audit_report_task(
                mock_task,
                start_time=start_time,
                end_time=end_time
            )
            
            assert result["status"] == "error"
            assert "Database error" in result["error"]

    def test_batch_log_events_task_success(self, setup_database, test_user):
        """Test successful batch event logging."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            mock_db = TestingSessionLocal()
            mock_get_db.return_value = mock_db
            
            try:
                # Create batch of events
                events = [
                    {
                        "user_id": test_user.id,
                        "action": f"batch_action_{i}",
                        "resource": "test_resource",
                        "success": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    for i in range(5)
                ]
                
                result = batch_log_events_task(events)
                
                assert result["status"] == "completed"
                assert result["successful_logs"] == 5
                assert result["failed_logs"] == 0
                assert result["total_events"] == 5
                
                # Verify logs were created
                logs = mock_db.query(AuditLogORM).filter(
                    AuditLogORM.action_type.like("batch_action_%")
                ).all()
                assert len(logs) == 5
                
            finally:
                mock_db.close()

    def test_batch_log_events_task_partial_failure(self, setup_database, test_user):
        """Test batch event logging with some failures."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            mock_db = TestingSessionLocal()
            mock_get_db.return_value = mock_db
            
            try:
                # Create batch with valid and invalid events
                events = [
                    {
                        "user_id": test_user.id,
                        "action": "valid_action",
                        "resource": "test_resource",
                        "success": True,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    {
                        # Missing required fields - should fail
                        "invalid": "event"
                    },
                    {
                        "user_id": test_user.id,
                        "action": "another_valid_action",
                        "resource": "test_resource",
                        "success": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
                
                result = batch_log_events_task(events)
                
                assert result["status"] == "completed"
                assert result["successful_logs"] == 2
                assert result["failed_logs"] == 1
                assert result["total_events"] == 3
                
            finally:
                mock_db.close()

    def test_batch_log_events_task_database_failure(self, setup_database):
        """Test batch event logging with database failure."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            # Mock database failure
            mock_get_db.side_effect = Exception("Database connection failed")
            
            events = [{"action": "test", "user_id": 1}]
            
            result = batch_log_events_task(events)
            
            assert result["status"] == "error"
            assert "Database connection failed" in result["error"]

    def test_legacy_log_audit_action(self, setup_database):
        """Test legacy audit action logging task."""
        with patch("audit_logger.tasks.log_audit_action_async.apply_async") as mock_async:
            # Mock the async task result
            mock_result = Mock()
            mock_result.get.return_value = {"status": "success"}
            mock_async.return_value = mock_result
            
            result = log_audit_action(
                action="test_action",
                user_id=1,
                details={"key": "value"}
            )
            
            assert result is True
            
            # Verify the async task was called
            mock_async.assert_called_once_with(
                args=["test_action", 1, None, {"key": "value"}]
            )

    def test_legacy_log_audit_action_failure(self, setup_database):
        """Test legacy audit action logging task failure."""
        with patch("audit_logger.tasks.log_audit_action_async.apply_async") as mock_async:
            # Mock the async task failure
            mock_async.side_effect = Exception("Task failed")
            
            result = log_audit_action(
                action="test_action",
                user_id=1,
                details={"key": "value"}
            )
            
            assert result is False

    def test_task_parameter_validation(self, setup_database):
        """Test task parameter validation and edge cases."""
        # Test with None values
        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3
        
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            mock_db = TestingSessionLocal()
            mock_get_db.return_value = mock_db
            
            try:
                result = log_audit_action_async(
                    mock_task,
                    action=None,  # Will be converted to empty string
                    user_id=None,
                    resource=None,
                    details=None
                )
                
                # Should still succeed with None values
                assert result["status"] == "success"
                
            finally:
                mock_db.close()

    def test_cleanup_with_zero_retention(self, setup_database):
        """Test cleanup task with edge case parameters."""
        with patch("audit_logger.tasks.get_db") as mock_get_db:
            mock_db = TestingSessionLocal()
            mock_get_db.return_value = mock_db
            
            try:
                mock_task = Mock()
                mock_task.request.retries = 0
                mock_task.max_retries = 2
                
                # Test with zero retention days (should delete all logs)
                result = cleanup_old_logs_task(mock_task, retention_days=0)
                
                assert result["status"] == "success"
                assert result["retention_days"] == 0
                
            finally:
                mock_db.close()
