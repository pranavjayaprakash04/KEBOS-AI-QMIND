"""
Audit Logger Services
Business logic for comprehensive audit logging with database persistence.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import json

try:
    from ..common.db import get_db
    from ..common.models import AuditLogORM, UserORM
except ImportError:
    # Fallback for testing
    from common.db import get_db
    from common.models import AuditLogORM, UserORM
from .schemas import (
    AuditLogResponse, AuditLogSearchRequest, AuditLogSearchResponse,
    SeverityLevel, AuditActionType, ResourceType
)

logger = logging.getLogger(__name__)


class AuditLoggerService:
    """
    Enhanced service for comprehensive audit logging with database persistence.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AuditLoggerService")
    
    async def log_event(
        self,
        user_id: Optional[int] = None,
        action: str = "",
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        db: Optional[Session] = None
    ) -> Optional[int]:
        """
        Log an audit event with database persistence.
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed
            resource: Resource being accessed
            details: Additional details about the action
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether the action was successful
            db: Database session (optional)
            
        Returns:
            Optional[int]: Log entry ID if successful, None otherwise
        """
        try:
            # Input validation
            if not action:
                raise ValueError("Action is required")
            
            if action and len(action) > 100:
                action = action[:100]
            
            if resource and len(resource) > 200:
                resource = resource[:200]
            
            if user_agent and len(user_agent) > 500:
                user_agent = user_agent[:500]
            
            # Validate details size
            if details:
                details_json = json.dumps(details)
                if len(details_json) > 10000:  # 10KB limit
                    self.logger.warning(f"Audit details too large, truncating: {len(details_json)} bytes")
                    details = {"error": "Details truncated due to size limit", "original_size": len(details_json)}
            
            # Use provided database session or create new one
            if db is None:
                db = next(get_db())
                close_db = True
            else:
                close_db = False
            
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
                
                # Log to application logger
                self.logger.info(
                    f"Audit event logged: {action} on {resource} by user {user_id} "
                    f"(success: {success}, log_id: {audit_log.id})"
                )
                
                return audit_log.id
                
            finally:
                if close_db:
                    db.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}", exc_info=True)
            return None
    
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        source_ip: Optional[str] = None,
        user_id: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log a security-related event.
        
        Args:
            event_type: Type of security event
            severity: Severity level
            description: Human-readable description
            source_ip: Source IP address
            user_id: User ID if applicable
            additional_data: Additional event data
            
        Returns:
            Optional[int]: Log entry ID if successful
        """
        return await self.log_event(
            user_id=user_id,
            action=f"security_{event_type}",
            resource=ResourceType.SECURITY_SYSTEM.value,
            details={
                "event_type": event_type,
                "severity": severity,
                "description": description,
                "source_ip": source_ip,
                "additional_data": additional_data or {}
            },
            ip_address=source_ip,
            success=True  # Security events are always logged as successful
        )
    
    async def log_threat_detection(
        self,
        user_id: Optional[int],
        packet_info: Dict[str, Any],
        threat_level: str,
        detection_result: Dict[str, Any]
    ) -> Optional[int]:
        """
        Log a threat detection event.
        
        Args:
            user_id: ID of user who initiated the detection
            packet_info: Information about the analyzed packet
            threat_level: Detected threat level
            detection_result: Results from the detection system
            
        Returns:
            Optional[int]: Log entry ID if successful
        """
        return await self.log_event(
            user_id=user_id,
            action=AuditActionType.THREAT_DETECTION.value,
            resource=ResourceType.NETWORK_PACKET.value,
            details={
                "packet_info": packet_info,
                "threat_level": threat_level,
                "detection_result": detection_result
            }
        )
    
    async def log_model_operation(
        self,
        user_id: int,
        operation: str,
        model_info: Dict[str, Any],
        success: bool = True
    ) -> Optional[int]:
        """
        Log a machine learning model operation.
        
        Args:
            user_id: ID of user performing the operation
            operation: Type of operation
            model_info: Information about the model
            success: Whether the operation was successful
            
        Returns:
            Optional[int]: Log entry ID if successful
        """
        return await self.log_event(
            user_id=user_id,
            action=f"model_{operation}",
            resource=ResourceType.MODEL.value,
            details=model_info,
            success=success
        )
    
    async def log_user_action(
        self,
        user_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ) -> Optional[int]:
        """
        Log a user management action.
        
        Args:
            user_id: ID of user performing the action
            action: Action being performed
            target_user_id: ID of target user (for user management actions)
            details: Additional action details
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether the action was successful
            
        Returns:
            Optional[int]: Log entry ID if successful
        """
        resource = f"user/{target_user_id}" if target_user_id else ResourceType.USER.value
        
        return await self.log_event(
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
    
    async def search_audit_logs(
        self,
        search_params: AuditLogSearchRequest,
        db: Optional[Session] = None
    ) -> AuditLogSearchResponse:
        """
        Search audit logs with filtering and pagination.
        
        Args:
            search_params: Search parameters
            db: Database session (optional)
            
        Returns:
            AuditLogSearchResponse: Search results with pagination
        """
        try:
            # Use provided database session or create new one
            if db is None:
                db = next(get_db())
                close_db = True
            else:
                close_db = False
            
            try:
                # Build query filters
                query = db.query(AuditLogORM)
                
                if search_params.user_id:
                    query = query.filter(AuditLogORM.user_id == search_params.user_id)
                
                if search_params.action:
                    query = query.filter(AuditLogORM.action_type.ilike(f"%{search_params.action}%"))
                
                if search_params.resource:
                    query = query.filter(AuditLogORM.resource.ilike(f"%{search_params.resource}%"))
                
                if search_params.start_time:
                    query = query.filter(AuditLogORM.timestamp >= search_params.start_time)
                
                if search_params.end_time:
                    query = query.filter(AuditLogORM.timestamp <= search_params.end_time)
                
                if search_params.success is not None:
                    query = query.filter(AuditLogORM.success == search_params.success)
                
                # Count total results
                total = query.count()
                
                # Apply ordering and pagination
                query = query.order_by(desc(AuditLogORM.timestamp))
                query = query.offset(search_params.offset).limit(search_params.limit)
                
                # Execute query
                audit_logs = query.all()
                
                # Convert to response models
                log_responses = [
                    AuditLogResponse(
                        id=log.id,
                        user_id=log.user_id,
                        action_type=log.action_type,
                        resource=log.resource,
                        details=log.details,
                        ip_address=log.ip_address,
                        user_agent=log.user_agent,
                        success=log.success,
                        timestamp=log.timestamp,
                        created_at=log.created_at
                    )
                    for log in audit_logs
                ]
                
                self.logger.info(f"Retrieved {len(log_responses)} audit logs (total: {total})")
                
                return AuditLogSearchResponse(
                    logs=log_responses,
                    total=total,
                    limit=search_params.limit,
                    offset=search_params.offset
                )
                
            finally:
                if close_db:
                    db.close()
                    
        except Exception as e:
            self.logger.error(f"Failed to search audit logs: {e}", exc_info=True)
            return AuditLogSearchResponse(
                logs=[],
                total=0,
                limit=search_params.limit,
                offset=search_params.offset
            )
    
    async def get_audit_log_by_id(
        self,
        log_id: int,
        db: Optional[Session] = None
    ) -> Optional[AuditLogResponse]:
        """
        Retrieve a specific audit log by ID.
        
        Args:
            log_id: ID of the audit log
            db: Database session (optional)
            
        Returns:
            Optional[AuditLogResponse]: Audit log if found
        """
        try:
            # Use provided database session or create new one
            if db is None:
                db = next(get_db())
                close_db = True
            else:
                close_db = False
            
            try:
                audit_log = db.query(AuditLogORM).filter(AuditLogORM.id == log_id).first()
                
                if not audit_log:
                    return None
                
                return AuditLogResponse(
                    id=audit_log.id,
                    user_id=audit_log.user_id,
                    action_type=audit_log.action_type,
                    resource=audit_log.resource,
                    details=audit_log.details,
                    ip_address=audit_log.ip_address,
                    user_agent=audit_log.user_agent,
                    success=audit_log.success,
                    timestamp=audit_log.timestamp,
                    created_at=audit_log.created_at
                )
                
            finally:
                if close_db:
                    db.close()
                    
        except Exception as e:
            self.logger.error(f"Failed to get audit log {log_id}: {e}", exc_info=True)
            return None
    
    async def get_audit_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get audit log statistics for monitoring and reporting.
        
        Args:
            start_time: Start time for statistics
            end_time: End time for statistics
            db: Database session (optional)
            
        Returns:
            Dict[str, Any]: Statistics data
        """
        try:
            # Use provided database session or create new one
            if db is None:
                db = next(get_db())
                close_db = True
            else:
                close_db = False
            
            try:
                # Default to last 24 hours if no time range specified
                if not start_time:
                    start_time = datetime.utcnow() - timedelta(hours=24)
                if not end_time:
                    end_time = datetime.utcnow()
                
                # Base query with time filter
                base_query = db.query(AuditLogORM).filter(
                    and_(
                        AuditLogORM.timestamp >= start_time,
                        AuditLogORM.timestamp <= end_time
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
                        AuditLogORM.timestamp >= start_time,
                        AuditLogORM.timestamp <= end_time
                    )
                ).group_by(AuditLogORM.action_type).order_by(desc('count')).limit(10).all()
                
                # Top users
                top_users = db.query(
                    AuditLogORM.user_id,
                    func.count(AuditLogORM.id).label('count')
                ).filter(
                    and_(
                        AuditLogORM.timestamp >= start_time,
                        AuditLogORM.timestamp <= end_time,
                        AuditLogORM.user_id.isnot(None)
                    )
                ).group_by(AuditLogORM.user_id).order_by(desc('count')).limit(10).all()
                
                return {
                    "time_range": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat()
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
                    ],
                    "top_users": [
                        {"user_id": user_id, "count": count}
                        for user_id, count in top_users
                    ]
                }
                
            finally:
                if close_db:
                    db.close()
                    
        except Exception as e:
            self.logger.error(f"Failed to get audit statistics: {e}", exc_info=True)
            return {
                "error": str(e),
                "time_range": {
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                },
                "totals": {
                    "total_events": 0,
                    "successful_events": 0,
                    "failed_events": 0,
                    "success_rate": 0
                }
            }
    
    async def cleanup_old_logs(
        self,
        retention_days: int = 90,
        db: Optional[Session] = None
    ) -> int:
        """
        Clean up old audit logs based on retention policy.
        
        Args:
            retention_days: Number of days to retain logs
            db: Database session (optional)
            
        Returns:
            int: Number of logs deleted
        """
        try:
            # Use provided database session or create new one
            if db is None:
                db = next(get_db())
                close_db = True
            else:
                close_db = False
            
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
                    
                    self.logger.info(f"Cleaned up {delete_count} audit logs older than {retention_days} days")
                else:
                    self.logger.info("No old audit logs to clean up")
                
                return delete_count
                
            finally:
                if close_db:
                    db.close()
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old audit logs: {e}", exc_info=True)
            if db:
                db.rollback()
            return 0
