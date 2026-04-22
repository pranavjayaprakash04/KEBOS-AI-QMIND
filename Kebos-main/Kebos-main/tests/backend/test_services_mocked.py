"""
Mock-based tests for the Audit Logger Service layer.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from audit_logger.services import AuditLoggerService
from audit_logger.schemas import (
    AuditLogSearchRequest, AuditLogSearchResponse,
    AuditLogResponse
)


class TestAuditLoggerServiceMocked:
    """Test the AuditLoggerService using mocks to avoid database issues."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        mock = Mock()
        mock.commit.return_value = None
        mock.rollback.return_value = None
        mock.add.return_value = None
        mock.query.return_value = Mock()
        return mock

    @pytest.fixture
    def audit_service(self, mock_db):
        """Create audit service with mocked database."""
        with patch('audit_logger.services.get_db', return_value=mock_db):
            service = AuditLoggerService()
            service.db = mock_db
            return service

    def test_log_event_success(self, audit_service, mock_db):
        """Test successful audit event logging."""
        # Mock database operations
        mock_audit_log = Mock()
        mock_audit_log.id = 1
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # Mock the AuditLogORM constructor
        with patch('audit_logger.services.AuditLogORM') as mock_orm:
            mock_orm.return_value = mock_audit_log
            
            # Test data
            test_data = {
                "user_id": 1,
                "action_type": "test_action",
                "resource": "test_resource",
                "details": {"key": "value"},
                "ip_address": "192.168.1.100",
                "user_agent": "test-agent",
                "success": True
            }
            
            # Call the method
            result = audit_service.log_event(**test_data)
            
            # Verify
            assert result == 1
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_log_event_failure(self, audit_service, mock_db):
        """Test audit event logging with database error."""
        # Mock database exception
        mock_db.commit.side_effect = Exception("Database error")
        
        # Test data
        test_data = {
            "user_id": 1,
            "action_type": "test_action",
            "resource": "test_resource",
            "success": False
        }
        
        # Mock the AuditLogORM constructor
        with patch('audit_logger.services.AuditLogORM') as mock_orm:
            mock_orm.return_value = Mock(id=1)
            
            # Call the method
            result = audit_service.log_event(**test_data)
            
            # Verify error handling
            assert result is None
            mock_db.rollback.assert_called_once()

    def test_search_audit_logs(self, audit_service, mock_db):
        """Test audit log search functionality."""
        # Mock query results
        mock_logs = [
            Mock(id=1, user_id=1, action_type="login", resource="user",
                 details=None, ip_address=None, user_agent=None,
                 success=True, timestamp=datetime.now(), created_at=datetime.now()),
            Mock(id=2, user_id=1, action_type="logout", resource="user",
                 details=None, ip_address=None, user_agent=None,
                 success=True, timestamp=datetime.now(), created_at=datetime.now())
        ]
        
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_logs
        mock_query.count.return_value = 2
        
        mock_db.query.return_value = mock_query
        
        # Test search
        search_params = AuditLogSearchRequest(
            user_id=1,
            limit=10,
            offset=0
        )
        
        result = audit_service.search_audit_logs(search_params)
        
        # Verify
        assert isinstance(result, AuditLogSearchResponse)
        assert len(result.logs) == 2
        assert result.total == 2

    def test_get_audit_statistics(self, audit_service, mock_db):
        """Test audit statistics retrieval."""
        # Mock statistics data
        mock_stats = [
            Mock(action_type="login", count=5),
            Mock(action_type="logout", count=3),
        ]
        mock_total = Mock()
        mock_total.scalar.return_value = 8
        
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_stats
        
        mock_db.query.return_value = mock_query
        mock_db.query().filter().count.return_value.scalar.return_value = 8
        
        # Test statistics
        result = audit_service.get_audit_statistics()
        
        # Verify
        assert isinstance(result, dict)
        assert "totals" in result

    def test_cleanup_old_logs(self, audit_service, mock_db):
        """Test cleanup of old audit logs."""
        # Mock delete operation
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 5  # 5 logs deleted
        
        mock_db.query.return_value = mock_query
        
        # Test cleanup
        days_to_keep = 30
        result = audit_service.cleanup_old_logs(days_to_keep)
        
        # Verify
        assert result == 5
        mock_db.commit.assert_called_once()

    def test_log_security_event(self, audit_service, mock_db):
        """Test security event logging."""
        with patch.object(audit_service, 'log_event', return_value=1) as mock_log:
            result = audit_service.log_security_event(
                user_id=1,
                event_type="unauthorized_access",
                resource="admin_panel",
                details={"ip": "192.168.1.100"},
                severity="high"
            )
            
            assert result == 1
            mock_log.assert_called_once()

    def test_log_threat_detection(self, audit_service, mock_db):
        """Test threat detection logging."""
        with patch.object(audit_service, 'log_event', return_value=1) as mock_log:
            result = audit_service.log_threat_detection(
                threat_type="malware",
                source_ip="192.168.1.100",
                details={"file": "suspicious.exe"},
                severity="critical"
            )
            
            assert result == 1
            mock_log.assert_called_once()

    def test_log_model_operation(self, audit_service, mock_db):
        """Test model operation logging."""
        with patch.object(audit_service, 'log_event', return_value=1) as mock_log:
            result = audit_service.log_model_operation(
                user_id=1,
                model_id="model_123",
                operation="inference",
                details={"input_size": 1024}
            )
            
            assert result == 1
            mock_log.assert_called_once()

    def test_log_user_action(self, audit_service, mock_db):
        """Test user action logging."""
        with patch.object(audit_service, 'log_event', return_value=1) as mock_log:
            result = audit_service.log_user_action(
                user_id=1,
                action="profile_update",
                resource="user_profile",
                details={"field": "email"}
            )
            
            assert result == 1
            mock_log.assert_called_once()
