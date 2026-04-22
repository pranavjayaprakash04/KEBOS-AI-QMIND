"""
Job Manager Simple Tests - Basic functionality validation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from .models import JobCreate, JobUpdate, JobStatus, JobPriority, JobType
from .services import JobManagerService
from .api import router

# Test configuration
TEST_USER_ID = "test_user_123"
TEST_ORG_ID = "test_org_456"

class MockSession:
    """Mock database session for testing"""
    def __init__(self):
        self.jobs = {}
        self.job_counter = 1
        
    async def execute(self, query):
        """Mock execute method"""
        return Mock(scalar_one_or_none=lambda: None, scalars=lambda: Mock(all=lambda: []))
    
    async def commit(self):
        """Mock commit method"""
        pass
    
    async def rollback(self):
        """Mock rollback method"""
        pass
    
    async def refresh(self, obj):
        """Mock refresh method"""
        pass


@pytest.fixture
def mock_session():
    """Provide mock database session"""
    return MockSession()


@pytest.fixture
def job_service():
    """Provide job manager service instance"""
    return JobManagerService()


@pytest.fixture
def test_client():
    """Provide test client for API testing"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestJobModels:
    """Test job models and validation"""
    
    def test_job_create_validation(self):
        """Test JobCreate model validation"""
        # Valid job creation
        job_data = JobCreate(
            job_name="Test Job",
            job_type=JobType.DATA_PROCESSING,
            priority=JobPriority.NORMAL,
            input_parameters={"input_file": "test.csv"},
            configuration={"batch_size": 100}
        )
        
        assert job_data.job_name == "Test Job"
        assert job_data.job_type == JobType.DATA_PROCESSING
        assert job_data.priority == JobPriority.NORMAL
        assert job_data.input_parameters["input_file"] == "test.csv"
        assert job_data.max_retries == 3  # Default value
    
    def test_job_create_with_scheduling(self):
        """Test job creation with future scheduling"""
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        job_data = JobCreate(
            job_type=JobType.ML_TRAINING,
            scheduled_at=future_time,
            estimated_duration_seconds=3600
        )
        
        assert job_data.scheduled_at == future_time
        assert job_data.estimated_duration_seconds == 3600
    
    def test_job_update_validation(self):
        """Test JobUpdate model validation"""
        job_update = JobUpdate(
            status=JobStatus.RUNNING,
            progress_percentage=50.0,
            current_step="Processing data",
            memory_usage_mb=256.5,
            cpu_usage_percent=75.2
        )
        
        assert job_update.status == JobStatus.RUNNING
        assert job_update.progress_percentage == 50.0
        assert job_update.current_step == "Processing data"
        assert job_update.memory_usage_mb == 256.5
        assert job_update.cpu_usage_percent == 75.2
    
    def test_invalid_progress_percentage(self):
        """Test that invalid progress percentage raises validation error"""
        with pytest.raises(ValueError):
            JobUpdate(progress_percentage=150.0)  # Should be <= 100
        
        with pytest.raises(ValueError):
            JobUpdate(progress_percentage=-10.0)  # Should be >= 0


class TestJobService:
    """Test job manager service functionality"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, job_service):
        """Test service initialization"""
        assert job_service is not None
        assert job_service.celery_app is None  # No Celery app provided
        assert job_service.logger is not None
    
    @pytest.mark.asyncio
    async def test_job_orm_to_response_conversion(self, job_service):
        """Test conversion from ORM to response model"""
        # Mock job ORM
        mock_job_orm = Mock()
        mock_job_orm.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_job_orm.job_id = "data_processing_abc123"
        mock_job_orm.job_name = "Test Job"
        mock_job_orm.job_type = "data_processing"
        mock_job_orm.job_category = "analytics"
        mock_job_orm.priority = "normal"
        mock_job_orm.status = "pending"
        mock_job_orm.created_at = datetime.utcnow()
        mock_job_orm.scheduled_at = None
        mock_job_orm.started_at = None
        mock_job_orm.completed_at = None
        mock_job_orm.expires_at = None
        mock_job_orm.progress_percentage = 0.0
        mock_job_orm.current_step = None
        mock_job_orm.total_steps = None
        mock_job_orm.estimated_duration_seconds = 300
        mock_job_orm.actual_duration_seconds = None
        mock_job_orm.memory_usage_mb = None
        mock_job_orm.cpu_usage_percent = None
        mock_job_orm.input_parameters = {"input_file": "test.csv"}
        mock_job_orm.configuration = {"batch_size": 100}
        mock_job_orm.result_data = None
        mock_job_orm.output_files = None
        mock_job_orm.error_message = None
        mock_job_orm.retry_count = 0
        mock_job_orm.max_retries = 3
        mock_job_orm.created_by = TEST_USER_ID
        mock_job_orm.assigned_to = None
        mock_job_orm.tags = {"environment": "test"}
        mock_job_orm.job_metadata = {"source": "unit_test"}
        mock_job_orm.updated_at = datetime.utcnow()
        
        # Test conversion
        response = await job_service._job_orm_to_response(mock_job_orm)
        
        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.job_id == "data_processing_abc123"
        assert response.job_name == "Test Job"
        assert response.job_type == "data_processing"
        assert response.status == "pending"
        assert response.created_by == TEST_USER_ID
        assert response.input_parameters["input_file"] == "test.csv"
        assert response.tags["environment"] == "test"


class TestJobTasks:
    """Test Celery task functionality"""
    
    def test_task_configuration(self):
        """Test Celery task configuration"""
        from .tasks import celery_app
        
        # Test basic configuration
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True
    
    def test_task_routes(self):
        """Test task routing configuration"""
        from .tasks import celery_app
        
        routes = celery_app.conf.task_routes
        assert 'job_manager.tasks.execute_job' in routes
        assert routes['job_manager.tasks.execute_job']['queue'] == 'job_execution'
        assert routes['job_manager.tasks.send_notification']['queue'] == 'notifications'
        assert routes['job_manager.tasks.cleanup_jobs']['queue'] == 'maintenance'
    
    @patch('asyncio.run')
    def test_execute_job_task_structure(self, mock_asyncio_run):
        """Test execute_job task structure"""
        from .tasks import execute_job
        
        # Mock the async function to return success
        mock_asyncio_run.return_value = {"status": "completed"}
        
        # Create a mock task instance
        mock_task = Mock()
        mock_task.request.id = "task_123"
        mock_task.request.hostname = "worker_node_1"
        
        # Test task execution
        result = execute_job(mock_task, "test_job_id")
        
        assert mock_asyncio_run.called
        assert result["status"] == "completed"
    
    def test_notification_task_structure(self):
        """Test notification task structure"""
        from .tasks import send_notification
        
        # Test that the task is properly registered
        assert send_notification is not None
        assert hasattr(send_notification, 'delay')  # Celery task method
    
    def test_health_check_task(self):
        """Test health check task"""
        from .tasks import health_check
        
        # Create mock task instance
        mock_task = Mock()
        
        # Test health check execution
        result = health_check(mock_task)
        
        assert "timestamp" in result
        assert "system_health" in result
        assert "status" in result
        assert result["status"] in ["healthy", "degraded", "error"]


class TestJobAPI:
    """Test REST API endpoints"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_user = {
            "user_id": TEST_USER_ID,
            "organization_id": TEST_ORG_ID,
            "email": "test@example.com"
        }
    
    @patch('job_manager.api.get_current_user')
    @patch('job_manager.api.JobManagerService')
    def test_create_job_endpoint_structure(self, mock_service_class, mock_get_user):
        """Test job creation endpoint structure"""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock successful job creation
        mock_job_response = Mock()
        mock_job_response.job_id = "test_job_123"
        mock_service.create_job.return_value = mock_job_response
        
        # Test endpoint exists and has correct structure
        from .api import create_job
        assert create_job is not None
        assert hasattr(create_job, '__annotations__')  # Type annotations
    
    def test_api_router_configuration(self):
        """Test API router configuration"""
        from .api import router
        
        assert router.prefix == "/api/v1/jobs"
        assert "Job Management" in router.tags
        
        # Check that routes are registered
        route_paths = [route.path for route in router.routes]
        assert "/" in route_paths  # List/create jobs
        assert "/{job_id}" in route_paths  # Get/update job
        assert "/{job_id}/cancel" in route_paths  # Cancel job
        assert "/statistics" in route_paths  # Statistics
        assert "/health" in route_paths  # Health check


class TestIntegration:
    """Integration tests for job management functionality"""
    
    @pytest.mark.asyncio
    async def test_job_lifecycle_simulation(self):
        """Test complete job lifecycle simulation"""
        # This is a simplified simulation since we don't have full DB setup
        
        # 1. Create job
        job_create = JobCreate(
            job_name="Integration Test Job",
            job_type=JobType.DATA_PROCESSING,
            priority=JobPriority.HIGH,
            input_parameters={"test_param": "value"},
            configuration={"test_config": True}
        )
        
        assert job_create.job_name == "Integration Test Job"
        assert job_create.job_type == JobType.DATA_PROCESSING
        
        # 2. Update job progress
        job_update = JobUpdate(
            status=JobStatus.RUNNING,
            progress_percentage=50.0,
            current_step="Processing test data"
        )
        
        assert job_update.status == JobStatus.RUNNING
        assert job_update.progress_percentage == 50.0
        
        # 3. Complete job
        job_completion = JobUpdate(
            status=JobStatus.COMPLETED,
            progress_percentage=100.0,
            result_data={"processed_items": 1000, "success": True}
        )
        
        assert job_completion.status == JobStatus.COMPLETED
        assert job_completion.result_data["success"] is True
    
    def test_error_handling_simulation(self):
        """Test error handling in job processing"""
        # Test validation error
        with pytest.raises(ValueError):
            JobCreate(
                job_type=JobType.ML_TRAINING,
                scheduled_at=datetime.utcnow() - timedelta(hours=1)  # Past time
            )
        
        # Test invalid progress values
        with pytest.raises(ValueError):
            JobUpdate(progress_percentage=150.0)  # Over 100%
    
    def test_enum_validations(self):
        """Test enum validations work correctly"""
        # Valid enums
        assert JobStatus.PENDING in JobStatus
        assert JobPriority.HIGH in JobPriority
        assert JobType.ML_TRAINING in JobType
        
        # Test enum values
        assert JobStatus.COMPLETED.value == "completed"
        assert JobPriority.CRITICAL.value == "critical"
        assert JobType.THREAT_ANALYSIS.value == "threat_analysis"


# Test fixtures and utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def test_module_imports():
    """Test that all modules import correctly"""
    # Test model imports
    from .models import JobORM, JobCreate, JobResponse
    assert JobORM is not None
    assert JobCreate is not None
    assert JobResponse is not None
    
    # Test service imports
    from .services import JobManagerService
    assert JobManagerService is not None
    
    # Test API imports
    from .api import router
    assert router is not None
    
    # Test task imports
    from .tasks import execute_job, send_notification
    assert execute_job is not None
    assert send_notification is not None


def test_constants_and_enums():
    """Test that constants and enums are properly defined"""
    from .models import JobStatus, JobPriority, JobType
    
    # Test JobStatus enum
    assert len(JobStatus) >= 6  # At least 6 statuses
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"
    
    # Test JobPriority enum
    assert len(JobPriority) >= 4  # At least 4 priorities
    assert JobPriority.LOW.value == "low"
    assert JobPriority.NORMAL.value == "normal"
    assert JobPriority.HIGH.value == "high"
    assert JobPriority.CRITICAL.value == "critical"
    
    # Test JobType enum
    assert len(JobType) >= 10  # At least 10 job types
    assert JobType.DATA_PROCESSING.value == "data_processing"
    assert JobType.ML_TRAINING.value == "ml_training"
    assert JobType.THREAT_ANALYSIS.value == "threat_analysis"


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
