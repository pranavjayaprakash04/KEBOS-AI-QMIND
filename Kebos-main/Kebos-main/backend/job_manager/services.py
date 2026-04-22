"""
Job Manager Services - Comprehensive Async Service Layer
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload
from celery import Celery
from celery.result import AsyncResult
import logging
import json
import uuid
from contextlib import asynccontextmanager

from .models import (
    JobORM, JobDependencyORM, JobQueueORM, JobNotificationORM, JobLogORM,
    JobCreate, JobUpdate, JobResponse, JobSummaryResponse, JobQuery,
    JobStatistics, JobLogResponse, JobNotificationCreate, JobHealthResponse,
    JobStatus, JobPriority, JobType, NotificationType
)
from common.db import get_async_session
from common.exceptions import (
    ResourceNotFoundError, ValidationError, ExternalServiceError,
    ResourceAlreadyExistsError, AuthorizationError
)

logger = logging.getLogger(__name__)


class JobManagerService:
    """Comprehensive job management service with async operations"""
    
    def __init__(self, celery_app: Optional[Celery] = None):
        """Initialize the job manager service"""
        self.celery_app = celery_app
        self.logger = logger
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        async with get_async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    # =============================================================================
    # JOB CREATION AND MANAGEMENT
    # =============================================================================
    
    async def create_job(
        self,
        job_data: JobCreate,
        created_by: str,
        organization_id: Optional[str] = None
    ) -> JobResponse:
        """Create a new job with validation and dependency handling"""
        try:
            async with self.get_session() as session:
                # Generate unique job ID
                job_id = f"{job_data.job_type}_{uuid.uuid4().hex[:12]}"
                
                # Validate dependencies
                if job_data.depends_on:
                    await self._validate_job_dependencies(session, job_data.depends_on)
                
                # Create job record
                job_orm = JobORM(
                    job_id=job_id,
                    job_name=job_data.job_name or f"{job_data.job_type.value} Job",
                    job_type=job_data.job_type.value,
                    job_category=job_data.job_category,
                    priority=job_data.priority.value,
                    status=JobStatus.PENDING.value,
                    created_by=created_by,
                    organization_id=organization_id,
                    scheduled_at=job_data.scheduled_at,
                    expires_at=job_data.expires_at,
                    input_parameters=job_data.input_parameters,
                    configuration=job_data.configuration,
                    environment_variables=job_data.environment_variables,
                    estimated_duration_seconds=job_data.estimated_duration_seconds,
                    max_retries=job_data.max_retries,
                    retry_delay_seconds=job_data.retry_delay_seconds,
                    tags=job_data.tags,
                    job_metadata=job_data.job_metadata
                )
                
                session.add(job_orm)
                await session.flush()  # Get the ID
                
                # Create dependencies
                if job_data.depends_on:
                    await self._create_job_dependencies(session, job_orm.id, job_data.depends_on)
                
                # Log job creation
                await self._log_job_event(
                    session, job_orm.id, "INFO",
                    f"Job created by {created_by}",
                    {"job_type": job_data.job_type.value, "priority": job_data.priority.value}
                )
                
                await session.commit()
                
                # Schedule job execution if not scheduled for later
                if not job_data.scheduled_at or job_data.scheduled_at <= datetime.utcnow():
                    await self._schedule_job_execution(job_orm.id, job_id)
                
                self.logger.info(f"Created job {job_id} by {created_by}")
                return await self._job_orm_to_response(job_orm)
                
        except Exception as e:
            self.logger.error(f"Error creating job: {str(e)}")
            raise ExternalServiceError(f"Failed to create job: {str(e)}")
    
    async def get_job(self, job_id: str, user_id: str) -> JobResponse:
        """Get job by ID with access control"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(JobORM).where(
                        and_(
                            JobORM.job_id == job_id,
                            or_(
                                JobORM.created_by == user_id,
                                JobORM.assigned_to == user_id
                            )
                        )
                    )
                )
                job_orm = result.scalar_one_or_none()
                
                if not job_orm:
                    raise ResourceNotFoundError(f"Job {job_id} not found or access denied")
                
                return await self._job_orm_to_response(job_orm)
                
        except ResourceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting job {job_id}: {str(e)}")
            raise ExternalServiceError(f"Failed to get job: {str(e)}")
    
    async def update_job(
        self,
        job_id: str,
        job_update: JobUpdate,
        updated_by: str
    ) -> JobResponse:
        """Update job status and metadata"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(JobORM).where(JobORM.job_id == job_id)
                )
                job_orm = result.scalar_one_or_none()
                
                if not job_orm:
                    raise ResourceNotFoundError(f"Job {job_id} not found")
                
                # Update fields
                update_data = {}
                if job_update.status:
                    update_data['status'] = job_update.status.value
                    if job_update.status == JobStatus.RUNNING and not job_orm.started_at:
                        update_data['started_at'] = datetime.utcnow()
                    elif job_update.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        update_data['completed_at'] = datetime.utcnow()
                        if job_orm.started_at:
                            duration = (datetime.utcnow() - job_orm.started_at).total_seconds()
                            update_data['actual_duration_seconds'] = duration
                
                if job_update.progress_percentage is not None:
                    update_data['progress_percentage'] = job_update.progress_percentage
                
                if job_update.current_step:
                    update_data['current_step'] = job_update.current_step
                
                if job_update.result_data:
                    update_data['result_data'] = job_update.result_data
                
                if job_update.output_files:
                    update_data['output_files'] = job_update.output_files
                
                if job_update.error_message:
                    update_data['error_message'] = job_update.error_message
                
                if job_update.error_traceback:
                    update_data['error_traceback'] = job_update.error_traceback
                
                if job_update.memory_usage_mb:
                    update_data['memory_usage_mb'] = job_update.memory_usage_mb
                
                if job_update.cpu_usage_percent:
                    update_data['cpu_usage_percent'] = job_update.cpu_usage_percent
                
                if job_update.tags:
                    current_tags = job_orm.tags or {}
                    current_tags.update(job_update.tags)
                    update_data['tags'] = current_tags
                
                if job_update.job_metadata:
                    current_metadata = job_orm.job_metadata or {}
                    current_metadata.update(job_update.job_metadata)
                    update_data['job_metadata'] = current_metadata
                
                update_data['updated_at'] = datetime.utcnow()
                
                # Apply updates
                await session.execute(
                    update(JobORM)
                    .where(JobORM.job_id == job_id)
                    .values(**update_data)
                )
                
                # Log the update
                await self._log_job_event(
                    session, job_orm.id, "INFO",
                    f"Job updated by {updated_by}",
                    {"updates": list(update_data.keys())}
                )
                
                await session.commit()
                
                # Refresh the object
                await session.refresh(job_orm)
                
                # Handle notifications
                if job_update.status:
                    await self._trigger_job_notifications(job_orm.id, job_update.status.value)
                
                self.logger.info(f"Updated job {job_id} by {updated_by}")
                return await self._job_orm_to_response(job_orm)
                
        except ResourceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating job {job_id}: {str(e)}")
            raise ExternalServiceError(f"Failed to update job: {str(e)}")
    
    async def cancel_job(self, job_id: str, cancelled_by: str) -> JobResponse:
        """Cancel a running or pending job"""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    select(JobORM).where(JobORM.job_id == job_id)
                )
                job_orm = result.scalar_one_or_none()
                
                if not job_orm:
                    raise ResourceNotFoundError(f"Job {job_id} not found")
                
                if job_orm.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
                    raise ValidationError(f"Cannot cancel job in {job_orm.status} status")
                
                # Cancel Celery task if exists
                if job_orm.celery_task_id and self.celery_app:
                    self.celery_app.control.revoke(job_orm.celery_task_id, terminate=True)
                
                # Update job status
                await session.execute(
                    update(JobORM)
                    .where(JobORM.job_id == job_id)
                    .values(
                        status=JobStatus.CANCELLED.value,
                        completed_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                
                # Log cancellation
                await self._log_job_event(
                    session, job_orm.id, "WARNING",
                    f"Job cancelled by {cancelled_by}",
                    {"cancelled_by": cancelled_by}
                )
                
                await session.commit()
                
                # Refresh the object
                await session.refresh(job_orm)
                
                # Trigger notifications
                await self._trigger_job_notifications(job_orm.id, JobStatus.CANCELLED.value)
                
                self.logger.info(f"Cancelled job {job_id} by {cancelled_by}")
                return await self._job_orm_to_response(job_orm)
                
        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error cancelling job {job_id}: {str(e)}")
            raise ExternalServiceError(f"Failed to cancel job: {str(e)}")
    
    # =============================================================================
    # JOB QUERYING AND LISTING
    # =============================================================================
    
    async def list_jobs(
        self,
        query: JobQuery,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Tuple[List[JobSummaryResponse], int]:
        """List jobs with filtering, pagination, and sorting"""
        try:
            async with self.get_session() as session:
                # Build query conditions
                conditions = [
                    or_(
                        JobORM.created_by == user_id,
                        JobORM.assigned_to == user_id
                    )
                ]
                
                if organization_id:
                    conditions.append(JobORM.organization_id == organization_id)
                
                if query.job_type:
                    conditions.append(JobORM.job_type == query.job_type.value)
                
                if query.status:
                    conditions.append(JobORM.status == query.status.value)
                
                if query.priority:
                    conditions.append(JobORM.priority == query.priority.value)
                
                if query.created_by:
                    conditions.append(JobORM.created_by == query.created_by)
                
                if query.created_after:
                    conditions.append(JobORM.created_at >= query.created_after)
                
                if query.created_before:
                    conditions.append(JobORM.created_at <= query.created_before)
                
                if query.completed_after:
                    conditions.append(JobORM.completed_at >= query.completed_after)
                
                if query.completed_before:
                    conditions.append(JobORM.completed_at <= query.completed_before)
                
                if query.search_term:
                    search_conditions = [
                        JobORM.job_name.ilike(f"%{query.search_term}%"),
                        JobORM.job_id.ilike(f"%{query.search_term}%"),
                        JobORM.current_step.ilike(f"%{query.search_term}%")
                    ]
                    conditions.append(or_(*search_conditions))
                
                if query.tags:
                    for key, value in query.tags.items():
                        conditions.append(
                            JobORM.tags[key].astext == value
                        )
                
                # Count total records
                count_result = await session.execute(
                    select(func.count(JobORM.id)).where(and_(*conditions))
                )
                total_count = count_result.scalar()
                
                # Build main query with sorting
                sort_column = getattr(JobORM, query.sort_by)
                order_func = desc if query.sort_order == "desc" else asc
                
                # Get paginated results
                offset = (query.page - 1) * query.page_size
                result = await session.execute(
                    select(JobORM)
                    .where(and_(*conditions))
                    .order_by(order_func(sort_column))
                    .offset(offset)
                    .limit(query.page_size)
                )
                
                jobs = result.scalars().all()
                
                # Convert to response models
                job_responses = []
                for job in jobs:
                    job_responses.append(JobSummaryResponse(
                        id=str(job.id),
                        job_id=job.job_id,
                        job_name=job.job_name,
                        job_type=job.job_type,
                        status=job.status,
                        priority=job.priority,
                        progress_percentage=job.progress_percentage,
                        created_at=job.created_at,
                        started_at=job.started_at,
                        completed_at=job.completed_at,
                        created_by=job.created_by,
                        estimated_duration_seconds=job.estimated_duration_seconds,
                        actual_duration_seconds=job.actual_duration_seconds
                    ))
                
                return job_responses, total_count
                
        except Exception as e:
            self.logger.error(f"Error listing jobs: {str(e)}")
            raise ExternalServiceError(f"Failed to list jobs: {str(e)}")
    
    async def get_job_statistics(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        days_back: int = 30
    ) -> JobStatistics:
        """Get comprehensive job statistics"""
        try:
            async with self.get_session() as session:
                # Base conditions
                conditions = [
                    or_(
                        JobORM.created_by == user_id,
                        JobORM.assigned_to == user_id
                    )
                ]
                
                if organization_id:
                    conditions.append(JobORM.organization_id == organization_id)
                
                date_cutoff = datetime.utcnow() - timedelta(days=days_back)
                conditions.append(JobORM.created_at >= date_cutoff)
                
                # Get basic counts
                counts_result = await session.execute(
                    select(
                        func.count(JobORM.id).label('total'),
                        func.sum(func.case((JobORM.status == JobStatus.PENDING.value, 1), else_=0)).label('pending'),
                        func.sum(func.case((JobORM.status == JobStatus.RUNNING.value, 1), else_=0)).label('running'),
                        func.sum(func.case((JobORM.status == JobStatus.COMPLETED.value, 1), else_=0)).label('completed'),
                        func.sum(func.case((JobORM.status == JobStatus.FAILED.value, 1), else_=0)).label('failed'),
                        func.sum(func.case((JobORM.status == JobStatus.CANCELLED.value, 1), else_=0)).label('cancelled'),
                        func.avg(JobORM.actual_duration_seconds).label('avg_duration')
                    ).where(and_(*conditions))
                )
                counts = counts_result.first()
                
                # Get jobs by type
                type_result = await session.execute(
                    select(JobORM.job_type, func.count(JobORM.id))
                    .where(and_(*conditions))
                    .group_by(JobORM.job_type)
                )
                jobs_by_type = dict(type_result.all())
                
                # Get jobs by priority
                priority_result = await session.execute(
                    select(JobORM.priority, func.count(JobORM.id))
                    .where(and_(*conditions))
                    .group_by(JobORM.priority)
                )
                jobs_by_priority = dict(priority_result.all())
                
                # Get jobs by status
                status_result = await session.execute(
                    select(JobORM.status, func.count(JobORM.id))
                    .where(and_(*conditions))
                    .group_by(JobORM.status)
                )
                jobs_by_status = dict(status_result.all())
                
                # Get last 24h statistics
                last_24h = datetime.utcnow() - timedelta(hours=24)
                last_24h_conditions = conditions + [JobORM.created_at >= last_24h]
                
                last_24h_result = await session.execute(
                    select(
                        func.count(JobORM.id).label('created'),
                        func.sum(func.case((JobORM.status == JobStatus.COMPLETED.value, 1), else_=0)).label('completed'),
                        func.sum(func.case((JobORM.status == JobStatus.FAILED.value, 1), else_=0)).label('failed')
                    ).where(and_(*last_24h_conditions))
                )
                last_24h_stats = last_24h_result.first()
                
                # Calculate success rate
                total_finished = (counts.completed or 0) + (counts.failed or 0) + (counts.cancelled or 0)
                success_rate = (counts.completed / total_finished * 100) if total_finished > 0 else 0.0
                
                return JobStatistics(
                    total_jobs=counts.total or 0,
                    pending_jobs=counts.pending or 0,
                    running_jobs=counts.running or 0,
                    completed_jobs=counts.completed or 0,
                    failed_jobs=counts.failed or 0,
                    cancelled_jobs=counts.cancelled or 0,
                    average_execution_time_seconds=counts.avg_duration,
                    success_rate_percentage=success_rate,
                    jobs_by_type=jobs_by_type,
                    jobs_by_priority=jobs_by_priority,
                    jobs_by_status=jobs_by_status,
                    jobs_created_last_24h=last_24h_stats.created or 0,
                    jobs_completed_last_24h=last_24h_stats.completed or 0,
                    jobs_failed_last_24h=last_24h_stats.failed or 0
                )
                
        except Exception as e:
            self.logger.error(f"Error getting job statistics: {str(e)}")
            raise ExternalServiceError(f"Failed to get job statistics: {str(e)}")
    
    # =============================================================================
    # INTERNAL HELPER METHODS
    # =============================================================================
    
    async def _validate_job_dependencies(self, session: AsyncSession, depends_on: List[str]):
        """Validate that dependency jobs exist and are valid"""
        for dep_job_id in depends_on:
            result = await session.execute(
                select(JobORM.id).where(JobORM.job_id == dep_job_id)
            )
            if not result.scalar_one_or_none():
                raise ValidationError(f"Dependency job {dep_job_id} not found")
    
    async def _create_job_dependencies(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        depends_on: List[str]
    ):
        """Create job dependency relationships"""
        for dep_job_id in depends_on:
            # Get parent job ID
            result = await session.execute(
                select(JobORM.id).where(JobORM.job_id == dep_job_id)
            )
            parent_id = result.scalar_one()
            
            # Create dependency
            dep_orm = JobDependencyORM(
                parent_job_id=parent_id,
                child_job_id=job_id,
                dependency_type="sequential"
            )
            session.add(dep_orm)
    
    async def _log_job_event(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
        level: str,
        message: str,
        structured_data: Optional[Dict[str, Any]] = None
    ):
        """Log a job event"""
        log_orm = JobLogORM(
            job_id=job_id,
            log_level=level,
            message=message,
            structured_data=structured_data
        )
        session.add(log_orm)
    
    async def _schedule_job_execution(self, job_id: uuid.UUID, job_job_id: str):
        """Schedule job for execution with Celery"""
        if self.celery_app:
            try:
                # Schedule the job execution task
                result = self.celery_app.send_task(
                    'job_manager.tasks.execute_job',
                    args=[str(job_id)],
                    task_id=f"job_{job_job_id}"
                )
                
                # Update job with Celery task ID
                async with self.get_session() as session:
                    await session.execute(
                        update(JobORM)
                        .where(JobORM.id == job_id)
                        .values(celery_task_id=result.id)
                    )
                    await session.commit()
                
                self.logger.info(f"Scheduled job {job_job_id} with task ID {result.id}")
                
            except Exception as e:
                self.logger.error(f"Failed to schedule job {job_job_id}: {str(e)}")
                # Update job status to failed
                async with self.get_session() as session:
                    await session.execute(
                        update(JobORM)
                        .where(JobORM.id == job_id)
                        .values(
                            status=JobStatus.FAILED.value,
                            error_message=f"Failed to schedule: {str(e)}"
                        )
                    )
                    await session.commit()
    
    async def _trigger_job_notifications(self, job_id: uuid.UUID, status: str):
        """Trigger notifications for job status changes"""
        try:
            async with self.get_session() as session:
                # Get notifications that should be triggered
                result = await session.execute(
                    select(JobNotificationORM)
                    .where(
                        and_(
                            JobNotificationORM.job_id == job_id,
                            JobNotificationORM.trigger_events.contains([status]),
                            JobNotificationORM.is_sent == False
                        )
                    )
                )
                notifications = result.scalars().all()
                
                for notification in notifications:
                    # Schedule notification delivery
                    if self.celery_app:
                        self.celery_app.send_task(
                            'job_manager.tasks.send_notification',
                            args=[str(notification.id)]
                        )
                        
        except Exception as e:
            self.logger.error(f"Error triggering notifications: {str(e)}")
    
    async def _job_orm_to_response(self, job_orm: JobORM) -> JobResponse:
        """Convert JobORM to JobResponse"""
        return JobResponse(
            id=str(job_orm.id),
            job_id=job_orm.job_id,
            job_name=job_orm.job_name,
            job_type=job_orm.job_type,
            job_category=job_orm.job_category,
            priority=job_orm.priority,
            status=job_orm.status,
            created_at=job_orm.created_at,
            scheduled_at=job_orm.scheduled_at,
            started_at=job_orm.started_at,
            completed_at=job_orm.completed_at,
            expires_at=job_orm.expires_at,
            progress_percentage=job_orm.progress_percentage,
            current_step=job_orm.current_step,
            total_steps=job_orm.total_steps,
            estimated_duration_seconds=job_orm.estimated_duration_seconds,
            actual_duration_seconds=job_orm.actual_duration_seconds,
            memory_usage_mb=job_orm.memory_usage_mb,
            cpu_usage_percent=job_orm.cpu_usage_percent,
            input_parameters=job_orm.input_parameters or {},
            configuration=job_orm.configuration or {},
            result_data=job_orm.result_data,
            output_files=job_orm.output_files,
            error_message=job_orm.error_message,
            retry_count=job_orm.retry_count,
            max_retries=job_orm.max_retries,
            created_by=job_orm.created_by,
            assigned_to=job_orm.assigned_to,
            tags=job_orm.tags,
            job_metadata=job_orm.job_metadata,
            updated_at=job_orm.updated_at
        )
