"""
Tests for QMind consumer - critical load-bearing code.
Tests verify update_threat_with_qmind_result() is fully implemented (no stubs).
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from uuid import uuid4
from app.threat_detection.qmind_consumer import (
    update_threat_with_qmind_result,
    TENANT_THRESHOLDS,
    set_qmind_dependencies,
    handle_task_error,
    SYSTEM_ACTOR_ID
)


class TestUpdateThreatWithQMindResult:
    """Tests for update_threat_with_qmind_result - CRITICAL load-bearing function"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool."""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire = MagicMock(return_value=conn)
        pool.__aenter__ = AsyncMock(return_value=conn)
        pool.__aexit__ = AsyncMock()
        return pool
    
    @pytest.fixture
    def mock_case_manager(self):
        """Mock case manager."""
        manager = AsyncMock()
        manager.create_case = AsyncMock(return_value={"id": str(uuid4())})
        return manager
    
    @pytest.fixture
    def mock_audit_chain(self):
        """Mock audit chain."""
        chain = AsyncMock()
        chain.append = AsyncMock()
        return chain
    
    @pytest.fixture
    def setup_dependencies(self, mock_db_pool, mock_case_manager, mock_audit_chain):
        """Set up global dependencies for testing."""
        set_qmind_dependencies(mock_db_pool, mock_case_manager, mock_audit_chain)
        yield
        # Reset globals after test
        from app.threat_detection.qmind_consumer import _db_pool, _case_manager, _audit_chain
        import app.threat_detection.qmind_consumer as qm
        qm._db_pool = None
        qm._case_manager = None
        qm._audit_chain = None
    
    @pytest.mark.asyncio
    async def test_confirmed_threat_at_threshold(self, setup_dependencies):
        """Test that update_threat_with_qmind_result() sets CONFIRMED_THREAT at threshold"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "enterprise",
            "indicator_value": "malicious-domain.com",
            "confidence": 0.75,  # Exactly at enterprise confirmed_threat threshold
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.75},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify DB was updated with CONFIRMED_THREAT status
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0][0]
        assert "CONFIRMED_THREAT" in call_args
    
    @pytest.mark.asyncio
    async def test_benign_below_monitoring_threshold(self, setup_dependencies):
        """Test that update_threat_with_qmind_result() sets BENIGN below monitoring threshold"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "enterprise",
            "indicator_value": "benign-domain.com",
            "confidence": 0.30,  # Below enterprise monitoring threshold (0.45)
            "lead_category": "Benign",
            "category_scores": {"Benign": 0.30},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify DB was updated with BENIGN status
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0][0]
        assert "BENIGN" in call_args
    
    @pytest.mark.asyncio
    async def test_not_a_pass_stub(self, setup_dependencies):
        """Test that update_threat_with_qmind_result() is NOT a pass stub (inspect it)"""
        import inspect
        source = inspect.getsource(update_threat_with_qmind_result)
        
        # Verify no 'pass' statements
        assert "pass" not in source or "# TODO" in source, "Function contains 'pass' without TODO"
        
        # Verify function has actual implementation
        assert len(source) > 50, "Function is too short - likely a stub"
        
        # Verify it contains key operations
        assert "tenant_id" in source
        assert "confidence" in source
        assert "status" in source
        assert "CONFIRMED_THREAT" in source or "ELEVATED" in source or "MONITORING" in source
    
    @pytest.mark.asyncio
    async def test_government_uses_0_70_threshold_not_0_75(self, setup_dependencies):
        """Test that government tenant uses 0.70 threshold not 0.75"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "government",
            "indicator_value": "gov-target.com",
            "confidence": 0.70,  # At government threshold (0.70), below enterprise (0.75)
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.70},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify DB was updated with CONFIRMED_THREAT status (government uses 0.70)
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0][0]
        assert "CONFIRMED_THREAT" in call_args
    
    @pytest.mark.asyncio
    async def test_government_0_69_is_elevated_not_confirmed(self, setup_dependencies):
        """Test that government with 0.69 is ELEVATED not CONFIRMED_THREAT"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "government",
            "indicator_value": "gov-target.com",
            "confidence": 0.69,  # Below government confirmed threshold (0.70), above elevated (0.55)
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.69},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify DB was updated with ELEVATED status
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0][0]
        assert "ELEVATED" in call_args
        assert "CONFIRMED_THREAT" not in call_args
    
    @pytest.mark.asyncio
    async def test_confirmed_threat_triggers_case_creation(self, setup_dependencies):
        """Test that CONFIRMED_THREAT triggers case creation task"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "enterprise",
            "indicator_value": "malicious-domain.com",
            "confidence": 0.80,  # Above confirmed threat threshold
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.80},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify case_manager.create_case was called
        from app.threat_detection.qmind_consumer import _case_manager
        _case_manager.create_case.assert_called_once()
        call_args = _case_manager.create_case.call_args
        assert call_args[1]["ioc_value"] == "malicious-domain.com"
        assert call_args[1]["lead_category"] == "Phishing"
        assert call_args[1]["qmind_confidence"] == 0.80
    
    @pytest.mark.asyncio
    async def test_confirmed_threat_triggers_audit_logging(self, setup_dependencies):
        """Test that CONFIRMED_THREAT triggers audit chain logging"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "enterprise",
            "indicator_value": "malicious-domain.com",
            "confidence": 0.80,
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.80},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify audit_chain.append was called
        from app.threat_detection.qmind_consumer import _audit_chain
        _audit_chain.append.assert_called_once()
        call_args = _audit_chain.append.call_args
        assert call_args[1]["action"] == "CONFIRMED_THREAT_DETECTED"
        assert call_args[1]["resource"] == "malicious-domain.com"
        assert call_args[1]["actor_id"] == SYSTEM_ACTOR_ID
    
    @pytest.mark.asyncio
    async def test_bfsi_uses_0_72_threshold(self, setup_dependencies):
        """Test that BFSI tenant uses 0.72 threshold"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "bfsi",
            "indicator_value": "bank-phish.com",
            "confidence": 0.72,  # At BFSI confirmed threshold (0.72)
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.72},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify DB was updated with CONFIRMED_THREAT status
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0][0]
        assert "CONFIRMED_THREAT" in call_args
    
    @pytest.mark.asyncio
    async def test_elevated_status_between_thresholds(self, setup_dependencies):
        """Test ELEVATED status between monitoring and confirmed thresholds"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "enterprise",
            "indicator_value": "suspicious-domain.com",
            "confidence": 0.65,  # Between monitoring (0.45) and confirmed (0.75)
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.65},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify DB was updated with ELEVATED status
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0][0]
        assert "ELEVATED" in call_args
    
    @pytest.mark.asyncio
    async def test_monitoring_status_at_threshold(self, setup_dependencies):
        """Test MONITORING status at monitoring threshold"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "enterprise",
            "indicator_value": "low-risk-domain.com",
            "confidence": 0.45,  # At enterprise monitoring threshold (0.45)
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.45},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify DB was updated with MONITORING status
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0][0]
        assert "MONITORING" in call_args
    
    @pytest.mark.asyncio
    async def test_non_confirmed_does_not_trigger_case(self, setup_dependencies):
        """Test that non-CONFIRMED_THREAT does NOT trigger case creation"""
        result = {
            "tenant_id": str(uuid4()),
            "tenant_type": "enterprise",
            "indicator_value": "low-risk-domain.com",
            "confidence": 0.40,  # Below monitoring threshold
            "lead_category": "Phishing",
            "category_scores": {"Phishing": 0.40},
            "reversibility": "REVERSIBLE"
        }
        
        await update_threat_with_qmind_result(result)
        
        # Verify case_manager.create_case was NOT called
        from app.threat_detection.qmind_consumer import _case_manager
        _case_manager.create_case.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(self, setup_dependencies):
        """Test that function handles missing optional fields gracefully"""
        result = {
            "tenant_id": str(uuid4()),
            # tenant_type missing - should default to enterprise
            "indicator_value": "test-domain.com",
            "confidence": 0.50,
            "lead_category": "Phishing",
            # category_scores missing - should default to {}
            # reversibility missing - should default to "REVERSIBLE"
        }
        
        # Should not raise exception
        await update_threat_with_qmind_result(result)
        
        # Verify DB was called
        from app.threat_detection.qmind_consumer import _db_pool
        conn = await _db_pool.acquire()
        conn.execute.assert_called_once()


class TestTenantThresholds:
    """Tests for tenant-specific thresholds"""
    
    def test_government_thresholds(self):
        """Verify government tenant thresholds"""
        assert TENANT_THRESHOLDS["government"]["confirmed_threat"] == 0.70
        assert TENANT_THRESHOLDS["government"]["elevated"] == 0.55
        assert TENANT_THRESHOLDS["government"]["monitoring"] == 0.40
    
    def test_bfsi_thresholds(self):
        """Verify BFSI tenant thresholds"""
        assert TENANT_THRESHOLDS["bfsi"]["confirmed_threat"] == 0.72
        assert TENANT_THRESHOLDS["bfsi"]["elevated"] == 0.58
        assert TENANT_THRESHOLDS["bfsi"]["monitoring"] == 0.42
    
    def test_enterprise_thresholds(self):
        """Verify enterprise tenant thresholds"""
        assert TENANT_THRESHOLDS["enterprise"]["confirmed_threat"] == 0.75
        assert TENANT_THRESHOLDS["enterprise"]["elevated"] == 0.60
        assert TENANT_THRESHOLDS["enterprise"]["monitoring"] == 0.45


class TestHandleTaskError:
    """Tests for handle_task_error function"""
    
    def test_handle_task_error_logs_exception(self):
        """Test that handle_task_error logs exceptions"""
        task = Mock()
        task.cancelled.return_value = False
        task.exception.return_value = Exception("Test error")
        task.get_name.return_value = "test-task"
        
        with patch('app.threat_detection.qmind_consumer.logger') as mock_logger:
            handle_task_error(task)
            mock_logger.error.assert_called_once()
    
    def test_handle_task_error_ignores_cancelled_tasks(self):
        """Test that handle_task_error ignores cancelled tasks"""
        task = Mock()
        task.cancelled.return_value = True
        
        with patch('app.threat_detection.qmind_consumer.logger') as mock_logger:
            handle_task_error(task)
            mock_logger.error.assert_not_called()
    
    def test_handle_task_error_auto_restarts_qmind_consumer(self):
        """Test that handle_task_error auto-restarts qmind consumer after 5s"""
        task = Mock()
        task.cancelled.return_value = False
        task.exception.return_value = Exception("Test error")
        task.get_name.return_value = "qmind-results-consumer"
        
        with patch('app.threat_detection.qmind_consumer.logger') as mock_logger:
            with patch('asyncio.get_event_loop') as mock_loop:
                handle_task_error(task)
                # Verify call_later was called for auto-restart
                mock_loop.return_value.call_later.assert_called_once()
    
    def test_handle_task_error_no_restart_for_non_qmind_tasks(self):
        """Test that handle_task_error does NOT restart non-qmind tasks"""
        task = Mock()
        task.cancelled.return_value = False
        task.exception.return_value = Exception("Test error")
        task.get_name.return_value = "other-task"
        
        with patch('app.threat_detection.qmind_consumer.logger') as mock_logger:
            with patch('asyncio.get_event_loop') as mock_loop:
                handle_task_error(task)
                # Verify call_later was NOT called
                mock_loop.return_value.call_later.assert_not_called()


class TestSetQMindDependencies:
    """Tests for set_qmind_dependencies function"""
    
    def test_set_dependencies_sets_globals(self):
        """Test that set_qmind_dependencies sets global variables"""
        mock_db = Mock()
        mock_case = Mock()
        mock_audit = Mock()
        
        set_qmind_dependencies(mock_db, mock_case, mock_audit)
        
        from app.threat_detection.qmind_consumer import _db_pool, _case_manager, _audit_chain
        assert _db_pool == mock_db
        assert _case_manager == mock_case
        assert _audit_chain == mock_audit
        
        # Reset globals
        import app.threat_detection.qmind_consumer as qm
        qm._db_pool = None
        qm._case_manager = None
        qm._audit_chain = None
