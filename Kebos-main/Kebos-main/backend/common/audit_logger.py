"""
Enhanced Audit Logger Utility
Async audit logging with comprehensive tracking and security features.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .db import get_db
    from .models import AuditLogORM
    from .utils import log_error, log_warning, sanitize_string, generate_trace_id
    DB_AVAILABLE = True
except ImportError:
    # Fallback for testing
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


class AuditLogger:
    """Enhanced audit logger with async support and security features."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AuditLogger")
    
    async def log_action(
        self,
        user_id: Optional[Union[int, str]] = None,
        action_type: str = "",
        model_id: Optional[Union[int, str]] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        db: Optional[Session] = None
    ) -> Optional[int]:
        """
        Log an audit action asynchronously.
        
        Args:
            user_id: ID of user performing action
            action_type: Type of action performed
            model_id: ID of model if applicable
            resource: Resource identifier
            details: Additional action details
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether action was successful
            db: Database session (optional)
            
        Returns:
            Audit log entry ID if successful, None otherwise
        """
        if not DB_AVAILABLE:
            self.logger.warning("Database not available, audit logging disabled")
            return None
        
        try:
            # Sanitize inputs
            action_type = sanitize_string(action_type, max_length=100) if action_type else "unknown"
            resource = sanitize_string(resource, max_length=200) if resource else None
            ip_address = sanitize_string(ip_address, max_length=45) if ip_address else None
            user_agent = sanitize_string(user_agent, max_length=500) if user_agent else None
            
            # Validate user_id and model_id
            if user_id and not isinstance(user_id, (int, str)):
                user_id = str(user_id)
            if model_id and not isinstance(model_id, (int, str)):
                model_id = str(model_id)
            
            # Limit details size for security
            if details:
                import json
                details_str = json.dumps(details)
                if len(details_str) > 10000:  # 10KB limit
                    details = {"error": "Details too large", "original_size": len(details_str)}
            
            # Get database session
            if db is None:
                db = next(get_db())
            
            try:
                # Create audit log entry
                entry = AuditLogORM(
                    user_id=int(user_id) if user_id and str(user_id).isdigit() else None,
                    action_type=action_type,
                    resource=resource,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    timestamp=datetime.utcnow()
                )
                
                db.add(entry)
                db.commit()
                db.refresh(entry)
                
                self.logger.info(f"Audit log created: {entry.id} - {action_type}")
                return entry.id
                
            finally:
                if db:
                    db.close()
                    
        except Exception as e:
            self.logger.error(f"Failed to log audit action: {e}")
            if db:
                try:
                    db.rollback()
                except:
                    pass
            return None
    
    async def log_security_event(
        self,
        event_type: str,
        severity: str = "medium",
        description: str = "",
        user_id: Optional[int] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log a security-related event.
        
        Args:
            event_type: Type of security event
            severity: Event severity (low, medium, high, critical)
            description: Event description
            user_id: Associated user ID
            source_ip: Source IP address
            details: Additional event details
            
        Returns:
            Audit log entry ID if successful
        """
        security_details = {
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "source_ip": source_ip,
            "trace_id": generate_trace_id()
        }
        
        if details:
            security_details.update(details)
        
        return await self.log_action(
            user_id=user_id,
            action_type=f"security_{event_type}",
            resource="security_system",
            details=security_details,
            ip_address=source_ip,
            success=True  # Security events are always logged as successful
        )
    
    async def log_model_operation(
        self,
        user_id: int,
        model_id: Union[int, str],
        operation: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> Optional[int]:
        """
        Log a model-related operation.
        
        Args:
            user_id: User performing operation
            model_id: Model identifier
            operation: Type of operation
            success: Whether operation was successful
            details: Additional operation details
            ip_address: Client IP address
            
        Returns:
            Audit log entry ID if successful
        """
        return await self.log_action(
            user_id=user_id,
            action_type=f"model_{operation}",
            model_id=model_id,
            resource=f"model/{model_id}",
            details=details,
            ip_address=ip_address,
            success=success
        )
    
    async def log_user_action(
        self,
        user_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ) -> Optional[int]:
        """
        Log a user management action.
        
        Args:
            user_id: User performing action
            action: Action being performed
            target_user_id: Target user ID (for user management)
            details: Additional action details
            ip_address: Client IP address
            success: Whether action was successful
            
        Returns:
            Audit log entry ID if successful
        """
        resource = f"user/{target_user_id}" if target_user_id else "user_system"
        
        user_details = details or {}
        if target_user_id:
            user_details["target_user_id"] = target_user_id
        
        return await self.log_action(
            user_id=user_id,
            action_type=action,
            resource=resource,
            details=user_details,
            ip_address=ip_address,
            success=success
        )
    
    async def log_system_event(
        self,
        event_type: str,
        component: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> Optional[int]:
        """
        Log a system-level event.
        
        Args:
            event_type: Type of system event
            component: System component
            details: Event details
            success: Whether event was successful
            
        Returns:
            Audit log entry ID if successful
        """
        system_details = {
            "component": component,
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": generate_trace_id()
        }
        
        if details:
            system_details.update(details)
        
        return await self.log_action(
            user_id=None,  # System events have no user
            action_type=f"system_{event_type}",
            resource=f"system/{component}",
            details=system_details,
            success=success
        )


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for backward compatibility
async def log_action(
    user_id: Optional[Union[int, str]],
    action_type: str,
    model_id: Optional[Union[int, str]] = None,
    result_path: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Optional[int]:
    """
    Legacy async audit logging function.
    
    Args:
        user_id: User ID
        action_type: Action type
        model_id: Model ID
        result_path: Result file path (deprecated, use details instead)
        details: Action details
        **kwargs: Additional parameters
        
    Returns:
        Audit log entry ID
    """
    # Handle legacy result_path parameter
    if result_path and details is None:
        details = {"result_path": result_path}
    elif result_path and details:
        details["result_path"] = result_path
    
    return await audit_logger.log_action(
        user_id=user_id,
        action_type=action_type,
        model_id=model_id,
        details=details,
        **kwargs
    )


def log_action_sync(
    user_id: Union[int, str],
    action_type: str,
    model_id: Optional[Union[int, str]] = None,
    result_path: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Synchronous audit logging function for backward compatibility.
    
    Args:
        user_id: User ID
        action_type: Action type
        model_id: Model ID
        result_path: Result file path
        details: Action details
        
    Returns:
        Audit log entry ID
    """
    if not DB_AVAILABLE:
        logger.warning("Database not available, audit logging disabled")
        return None
    
    try:
        from .db import SessionLocal
        
        # Handle legacy result_path parameter
        if result_path and details is None:
            details = {"result_path": result_path}
        elif result_path and details:
            details["result_path"] = result_path
        
        db = SessionLocal()
        try:
            entry = AuditLogORM(
                user_id=int(user_id) if str(user_id).isdigit() else None,
                action_type=sanitize_string(action_type, max_length=100),
                model_id=int(model_id) if model_id and str(model_id).isdigit() else None,
                timestamp=datetime.utcnow(),
                details=details
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry.id
        finally:
            db.close()
            
    except Exception as e:
        log_error(f"Failed to log audit action: {e}")
        return None
