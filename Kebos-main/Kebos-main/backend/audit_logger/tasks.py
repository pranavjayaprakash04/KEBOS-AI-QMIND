"""
Audit Logger Celery Tasks
Background tasks for audit logging with database persistence.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from celery import current_task

try:
    from ..common.celery_app import celery_app
    from ..common.db import get_db
    from ..common.models import AuditLogORM
except ImportError:
    # Fallback for testing
    from common.celery_app import celery_app
    from common.db import get_db
    from common.models import AuditLogORM

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def log_audit_action_async(
    self,
    action: str,
    user_id: Optional[int] = None,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True
) -> Dict[str, Any]:
    """
    Asynchronously log an audit action to the database.
    
    Args:
        action: Action being performed
        user_id: ID of user performing action
        resource: Resource being acted upon
        details: Additional action details
        ip_address: Client IP address
        user_agent: Client user agent
        success: Whether the action was successful
        
    Returns:
        Dict with operation result
    """
    try:
        # Get database session
        db = next(get_db())
        
        try:
            # Create audit log entry
            audit_log = AuditLogORM(
                user_id=user_id,
                action_type=action,
                resource=resource,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                timestamp=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(
                f"Audit action logged asynchronously: {action} on {resource} "
                f"by user {user_id} (log_id: {audit_log.id})"
            )
            
            return {
                "status": "success",
                "log_id": audit_log.id,
                "action": action,
                "user_id": user_id,
                "timestamp": audit_log.timestamp.isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to log audit action asynchronously: {e}", exc_info=True)
        
        # Retry on failure
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying audit log task (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "status": "error",
            "error": str(e),
            "action": action,
            "user_id": user_id,
            "retries": self.request.retries
        }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def cleanup_old_logs_task(self, retention_days: int = 90) -> Dict[str, Any]:
    """
    Background task to clean up old audit logs.
    
    Args:
        retention_days: Number of days to retain logs
        
    Returns:
        Dict with cleanup result
    """
    try:
        from datetime import timedelta
        from sqlalchemy import and_
        
        # Get database session
        db = next(get_db())
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count logs to be deleted
            count_query = db.query(AuditLogORM).filter(
                AuditLogORM.created_at < cutoff_date
            )
            delete_count = count_query.count()
            
            if delete_count > 0:
                # Delete old logs
                count_query.delete()
                db.commit()
                
                logger.info(f"Cleaned up {delete_count} audit logs older than {retention_days} days")
            else:
                logger.info("No old audit logs to clean up")
            
            return {
                "status": "success",
                "deleted_count": delete_count,
                "retention_days": retention_days,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to cleanup audit logs: {e}", exc_info=True)
        
        # Retry on failure
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying cleanup task (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            "status": "error",
            "error": str(e),
            "retention_days": retention_days,
            "retries": self.request.retries
        }


@celery_app.task(bind=True)
def generate_audit_report_task(
    self,
    start_time: str,
    end_time: str,
    user_id: Optional[int] = None,
    report_format: str = "json"
) -> Dict[str, Any]:
    """
    Background task to generate audit reports.
    
    Args:
        start_time: Report start time (ISO format)
        end_time: Report end time (ISO format)
        user_id: Optional user ID filter
        report_format: Report format (json, csv, pdf)
        
    Returns:
        Dict with report generation result
    """
    try:
        from datetime import timedelta
        from sqlalchemy import and_, func, desc
        
        # Parse datetime strings
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Get database session
        db = next(get_db())
        
        try:
            # Generate statistics directly in the task
            base_query = db.query(AuditLogORM).filter(
                and_(
                    AuditLogORM.timestamp >= start_dt,
                    AuditLogORM.timestamp <= end_dt
                )
            )
            
            # Total events
            total_events = base_query.count()
            
            # Success/failure counts
            successful_events = base_query.filter(AuditLogORM.success == True).count()
            failed_events = base_query.filter(AuditLogORM.success == False).count()
            
            # Top actions
            top_actions = db.query(
                AuditLogORM.action_type,
                func.count(AuditLogORM.id).label('count')
            ).filter(
                and_(
                    AuditLogORM.timestamp >= start_dt,
                    AuditLogORM.timestamp <= end_dt
                )
            ).group_by(AuditLogORM.action_type).order_by(desc('count')).limit(10).all()
            
            stats = {
                "time_range": {
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat()
                },
                "totals": {
                    "total_events": total_events,
                    "successful_events": successful_events,
                    "failed_events": failed_events,
                    "success_rate": successful_events / total_events if total_events > 0 else 0
                },
                "top_actions": [
                    {"action": action, "count": count}
                    for action, count in top_actions
                ]
            }
            
            # TODO: Implement actual report generation based on format
            report_data = {
                "report_type": "audit_summary",
                "time_range": {
                    "start": start_time,
                    "end": end_time
                },
                "user_filter": user_id,
                "statistics": stats,
                "generated_at": datetime.utcnow().isoformat(),
                "format": report_format
            }
            
            logger.info(f"Audit report generated for period {start_time} to {end_time}")
            
            return {
                "status": "success",
                "report_data": report_data,
                "format": report_format
            }
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to generate audit report: {e}", exc_info=True)
        
        return {
            "status": "error",
            "error": str(e),
            "start_time": start_time,
            "end_time": end_time
        }


@celery_app.task
def batch_log_events_task(events: list) -> Dict[str, Any]:
    """
    Background task to batch process multiple audit events.
    
    Args:
        events: List of audit events to log
        
    Returns:
        Dict with batch processing result
    """
    try:
        db = next(get_db())
        successful_logs = 0
        failed_logs = 0
        
        try:
            for event in events:
                try:
                    audit_log = AuditLogORM(
                        user_id=event.get('user_id'),
                        action_type=event.get('action', ''),
                        resource=event.get('resource'),
                        details=event.get('details'),
                        ip_address=event.get('ip_address'),
                        user_agent=event.get('user_agent'),
                        success=event.get('success', True),
                        timestamp=datetime.fromisoformat(event.get('timestamp', datetime.utcnow().isoformat())),
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(audit_log)
                    successful_logs += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to process audit event: {e}")
                    failed_logs += 1
                    continue
            
            # Commit all successful logs
            db.commit()
            
            logger.info(f"Batch audit logging completed: {successful_logs} success, {failed_logs} failed")
            
            return {
                "status": "completed",
                "successful_logs": successful_logs,
                "failed_logs": failed_logs,
                "total_events": len(events)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to batch process audit events: {e}", exc_info=True)
        
        return {
            "status": "error",
            "error": str(e),
            "total_events": len(events)
        }


# Legacy task for backward compatibility
@celery_app.task
def log_audit_action(action: str, user_id: int, details: dict) -> bool:
    """
    Legacy audit logging task (deprecated - use log_audit_action_async).
    
    Args:
        action: Action being performed
        user_id: ID of user performing action
        details: Additional action details
        
    Returns:
        bool: Success status
    """
    logger.warning("Using deprecated log_audit_action task, please use log_audit_action_async")
    
    try:
        result = log_audit_action_async.apply_async(
            args=[action, user_id, None, details]
        ).get()
        
        return result.get('status') == 'success'
        
    except Exception as e:
        logger.error(f"Legacy audit log task failed: {e}")
        return False
