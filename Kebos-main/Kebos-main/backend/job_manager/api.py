"""
Job Manager API - Comprehensive REST API with FastAPI
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    JobCreate, JobUpdate, JobResponse, JobSummaryResponse, JobQuery,
    JobStatistics, JobLogResponse, JobNotificationCreate, JobHealthResponse,
    JobStatus, JobPriority, JobType
)
from .services import JobManagerService
from common.db import get_async_session
from auth.dependencies import get_current_user, require_permission

router = APIRouter(prefix="/api/v1/jobs", tags=["Job Management"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Dependency injection
def get_job_service() -> JobManagerService:
    """Get job manager service instance"""
    return JobManagerService()


# =============================================================================
# JOB CRUD OPERATIONS
# =============================================================================

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    job_service: JobManagerService = Depends(get_job_service)
):
    """
    Create a new job
    
    Creates a new job with the specified configuration and schedules it for execution.
    Jobs can be scheduled for immediate execution or for a future time.
    
    Args:
        job_data: Job creation parameters
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        job_service: Job manager service
        
    Returns:
        Created job information
        
    Raises:
        HTTPException: If job creation fails
    """
    try:
        user_id = current_user.get("user_id")
        organization_id = current_user.get("organization_id")
        
        job = await job_service.create_job(
            job_data=job_data,
            created_by=user_id,
            organization_id=organization_id
        )
        
        logger.info(f"Created job {job.job_id} for user {user_id}")
        return job
        
    except ValueError as e:
        logger.warning(f"Validation error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobManagerService = Depends(get_job_service)
):
    """
    Get job details by ID
    
    Retrieves detailed information about a specific job, including its current
    status, progress, configuration, and results.
    
    Args:
        job_id: Unique job identifier
        current_user: Current authenticated user
        job_service: Job manager service
        
    Returns:
        Job details
        
    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        user_id = current_user.get("user_id")
        job = await job_service.get_job(job_id, user_id)
        return job
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or access denied"
            )
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    current_user: dict = Depends(get_current_user),
    job_service: JobManagerService = Depends(get_job_service)
):
    """
    Update job status and metadata
    
    Updates a job's status, progress, results, or other metadata. This endpoint
    is typically used by job execution workers to report progress and results.
    
    Args:
        job_id: Unique job identifier
        job_update: Job update parameters
        current_user: Current authenticated user
        job_service: Job manager service
        
    Returns:
        Updated job information
        
    Raises:
        HTTPException: If job not found or update fails
    """
    try:
        user_id = current_user.get("user_id")
        job = await job_service.update_job(job_id, job_update, user_id)
        
        logger.info(f"Updated job {job_id} by user {user_id}")
        return job
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        logger.error(f"Error updating job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobManagerService = Depends(get_job_service)
):
    """
    Cancel a running or pending job
    
    Cancels a job that is currently running or pending execution. The job
    will be marked as cancelled and any running processes will be terminated.
    
    Args:
        job_id: Unique job identifier
        current_user: Current authenticated user
        job_service: Job manager service
        
    Returns:
        Cancelled job information
        
    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    try:
        user_id = current_user.get("user_id")
        job = await job_service.cancel_job(job_id, user_id)
        
        logger.info(f"Cancelled job {job_id} by user {user_id}")
        return job
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_jobs(
    job_type: Optional[JobType] = None,
    status: Optional[JobStatus] = None,
    priority: Optional[JobPriority] = None,
    created_by: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    completed_after: Optional[datetime] = None,
    completed_before: Optional[datetime] = None,
    search_term: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|started_at|completed_at|priority|status|job_type)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user),
    job_service: JobManagerService = Depends(get_job_service)
):
    """
    List jobs with filtering and pagination
    
    Retrieves a paginated list of jobs with optional filtering by type, status,
    priority, dates, and search terms. Supports sorting by various fields.
    
    Args:
        job_type: Filter by job type
        status: Filter by job status
        priority: Filter by job priority
        created_by: Filter by creator user ID
        created_after: Filter jobs created after this date
        created_before: Filter jobs created before this date
        completed_after: Filter jobs completed after this date
        completed_before: Filter jobs completed before this date
        search_term: Search in job names and IDs
        page: Page number (1-based)
        page_size: Number of items per page
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        current_user: Current authenticated user
        job_service: Job manager service
        
    Returns:
        Paginated list of jobs with metadata
    """
    try:
        user_id = current_user.get("user_id")
        organization_id = current_user.get("organization_id")
        
        # Build query object
        query = JobQuery(
            job_type=job_type,
            status=status,
            priority=priority,
            created_by=created_by,
            created_after=created_after,
            created_before=created_before,
            completed_after=completed_after,
            completed_before=completed_before,
            search_term=search_term,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        jobs, total_count = await job_service.list_jobs(query, user_id, organization_id)
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "items": jobs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs"
        )


@router.get("/statistics", response_model=JobStatistics)
async def get_job_statistics(
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    job_service: JobManagerService = Depends(get_job_service)
):
    """
    Get job execution statistics
    
    Retrieves comprehensive statistics about job execution including counts
    by status, type, and priority, as well as performance metrics.
    
    Args:
        days_back: Number of days to include in statistics
        current_user: Current authenticated user
        job_service: Job manager service
        
    Returns:
        Job execution statistics
    """
    try:
        user_id = current_user.get("user_id")
        organization_id = current_user.get("organization_id")
        
        statistics = await job_service.get_job_statistics(
            user_id=user_id,
            organization_id=organization_id,
            days_back=days_back
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting job statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job statistics"
        )


@router.get("/health", response_model=JobHealthResponse)
async def get_health(
    job_service: JobManagerService = Depends(get_job_service)
):
    """
    Get job manager health status
    
    Retrieves the current health status of the job management system,
    including metrics about running jobs, queue status, and worker nodes.
    
    Args:
        job_service: Job manager service
        
    Returns:
        Health status information
    """
    try:
        health_status = await job_service.get_health_status()
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}")
        # Return a basic error status instead of raising exception
        return JobHealthResponse(
            status="error",
            timestamp=datetime.utcnow(),
            total_jobs=0,
            running_jobs=0,
            failed_jobs_last_hour=0,
            average_queue_time_seconds=None,
            worker_nodes=[],
            queue_status={"error": str(e)}
        )
