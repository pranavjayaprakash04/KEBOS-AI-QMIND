"""
Common Module Services
Business logic for shared functionality across all modules.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

try:
    from .db import get_db
    from .models import UserORM, ModelORM, AuditLogORM
    from .schemas import (
        UserCreate, UserUpdate, UserResponse, ModelMetadata,
        HealthCheckResponse, ValidationRequest, ValidationResponse,
        UtilityRequest, UtilityResponse, SystemInfo
    )
    from .utils import (
        log_error, log_info, log_warning, validate_email, validate_uuid,
        sanitize_string, hash_password, verify_password, get_system_info,
        handle_error, CommonError, ValidationError, ConfigurationError
    )
    from .audit_logger import audit_logger
    DB_AVAILABLE = True
except ImportError:
    # Fallback for testing
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


class CommonService:
    """
    Service class for common functionality shared across modules.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CommonService")
    
    async def validate_data(
        self,
        request: ValidationRequest,
        db: Optional[Session] = None
    ) -> ValidationResponse:
        """
        Validate data according to specified rules.
        
        Args:
            request: Validation request containing data and rules
            db: Database session (optional)
            
        Returns:
            ValidationResponse with validation results
        """
        try:
            errors = []
            warnings = []
            metadata = {}
            
            data_type = request.data_type.lower()
            data = request.data
            rules = request.validation_rules
            strict_mode = request.strict_mode
            
            # Validate based on data type
            if data_type == "email":
                if not validate_email(str(data)):
                    errors.append("Invalid email format")
            
            elif data_type == "uuid":
                if not validate_uuid(str(data)):
                    errors.append("Invalid UUID format")
            
            elif data_type == "string":
                if not isinstance(data, str):
                    if strict_mode:
                        errors.append("Data must be a string")
                    else:
                        data = str(data)
                        warnings.append("Data converted to string")
                
                # Check string rules
                if "min_length" in rules and len(data) < rules["min_length"]:
                    errors.append(f"String too short (minimum {rules['min_length']} characters)")
                
                if "max_length" in rules and len(data) > rules["max_length"]:
                    if strict_mode:
                        errors.append(f"String too long (maximum {rules['max_length']} characters)")
                    else:
                        data = data[:rules["max_length"]]
                        warnings.append(f"String truncated to {rules['max_length']} characters")
                
                if "pattern" in rules:
                    import re
                    if not re.match(rules["pattern"], data):
                        errors.append("String does not match required pattern")
            
            elif data_type == "number":
                try:
                    num = float(data)
                    if "min_value" in rules and num < rules["min_value"]:
                        errors.append(f"Number too small (minimum {rules['min_value']})")
                    if "max_value" in rules and num > rules["max_value"]:
                        errors.append(f"Number too large (maximum {rules['max_value']})")
                except (ValueError, TypeError):
                    errors.append("Invalid number format")
            
            elif data_type == "json":
                try:
                    import json
                    if isinstance(data, str):
                        parsed_data = json.loads(data)
                    else:
                        parsed_data = data
                    
                    if "max_size" in rules:
                        json_str = json.dumps(parsed_data)
                        if len(json_str) > rules["max_size"]:
                            errors.append(f"JSON too large (maximum {rules['max_size']} bytes)")
                    
                    metadata["parsed_data"] = parsed_data
                    
                except (json.JSONDecodeError, TypeError):
                    errors.append("Invalid JSON format")
            
            # Custom validation rules
            if "custom_validator" in rules and callable(rules["custom_validator"]):
                try:
                    custom_result = rules["custom_validator"](data)
                    if not custom_result:
                        errors.append("Custom validation failed")
                except Exception as e:
                    errors.append(f"Custom validation error: {str(e)}")
            
            # Check required field
            if rules.get("required", False) and (data is None or data == ""):
                errors.append("Field is required")
            
            is_valid = len(errors) == 0
            
            return ValidationResponse(
                status="success" if is_valid else "validation_failed",
                message=f"Validation {'passed' if is_valid else 'failed'}",
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return ValidationResponse(
                status="error",
                message="Validation service error",
                is_valid=False,
                errors=[str(e)],
                warnings=[],
                metadata={}
            )
    
    async def get_health_status(self) -> HealthCheckResponse:
        """
        Get comprehensive health status of the common module and dependencies.
        
        Returns:
            HealthCheckResponse with service health information
        """
        try:
            # Check database connectivity
            database_status = "healthy"
            try:
                if DB_AVAILABLE:
                    db = next(get_db())
                    db.execute("SELECT 1")
                    db.close()
                else:
                    database_status = "unavailable"
            except Exception as e:
                database_status = f"error: {str(e)}"
            
            # Check Celery worker status
            celery_status = "healthy"
            try:
                from .celery_app import celery_app
                inspector = celery_app.control.inspect()
                active_workers = inspector.active()
                if not active_workers:
                    celery_status = "no_workers"
            except Exception as e:
                celery_status = f"error: {str(e)}"
            
            # Check external dependencies
            dependencies = {}
            
            # Redis check (if configured)
            try:
                import redis
                import os
                redis_url = os.getenv("REDIS_URL")
                if redis_url:
                    r = redis.from_url(redis_url)
                    r.ping()
                    dependencies["redis"] = "healthy"
                else:
                    dependencies["redis"] = "not_configured"
            except Exception as e:
                dependencies["redis"] = f"error: {str(e)}"
            
            # Get system information
            system_info = get_system_info()
            uptime = system_info.get("uptime", 0)
            
            # Determine overall status
            overall_status = "healthy"
            if database_status != "healthy" or celery_status == "error":
                overall_status = "degraded"
            if database_status.startswith("error"):
                overall_status = "unhealthy"
            
            return HealthCheckResponse(
                service="common",
                status=overall_status,
                version="1.0.0",
                database=database_status,
                celery=celery_status,
                dependencies=dependencies,
                uptime=uptime
            )
            
        except Exception as e:
            self.logger.error(f"Error checking health status: {e}")
            return HealthCheckResponse(
                service="common",
                status="error",
                version="1.0.0",
                database="unknown",
                celery="unknown",
                dependencies={"error": str(e)},
                uptime=0
            )
    
    async def execute_utility(
        self,
        request: UtilityRequest,
        db: Optional[Session] = None
    ) -> UtilityResponse:
        """
        Execute a utility operation.
        
        Args:
            request: Utility request with operation and parameters
            db: Database session (optional)
            
        Returns:
            UtilityResponse with operation results
        """
        try:
            operation = request.operation.lower()
            parameters = request.parameters
            options = request.options
            
            result = None
            metadata = {}
            
            if operation == "hash_password":
                password = parameters.get("password")
                if not password:
                    raise ValidationError("Password is required")
                
                hashed, salt = hash_password(password)
                result = {"hashed_password": hashed, "salt": salt}
                metadata["algorithm"] = "pbkdf2_hmac_sha256"
            
            elif operation == "verify_password":
                password = parameters.get("password")
                hashed_password = parameters.get("hashed_password")
                salt = parameters.get("salt")
                
                if not all([password, hashed_password, salt]):
                    raise ValidationError("Password, hashed_password, and salt are required")
                
                is_valid = verify_password(password, hashed_password, salt)
                result = {"valid": is_valid}
            
            elif operation == "sanitize_string":
                text = parameters.get("text", "")
                max_length = parameters.get("max_length", 1000)
                allow_html = parameters.get("allow_html", False)
                
                sanitized = sanitize_string(text, max_length, allow_html)
                result = {"sanitized_text": sanitized}
                metadata = {"original_length": len(text), "final_length": len(sanitized)}
            
            elif operation == "generate_id":
                id_type = parameters.get("type", "uuid")
                
                if id_type == "uuid":
                    import uuid
                    result = {"id": str(uuid.uuid4())}
                elif id_type == "trace_id":
                    from .utils import generate_trace_id
                    result = {"id": generate_trace_id()}
                elif id_type == "session_id":
                    from .utils import generate_session_id
                    result = {"id": generate_session_id()}
                else:
                    raise ValidationError(f"Unknown ID type: {id_type}")
            
            elif operation == "system_info":
                info = get_system_info()
                result = info
            
            elif operation == "check_disk_space":
                from .utils import check_disk_space
                path = parameters.get("path", "/")
                min_free_gb = parameters.get("min_free_gb", 1.0)
                
                result = check_disk_space(path, min_free_gb)
            
            else:
                raise ValidationError(f"Unknown operation: {operation}")
            
            return UtilityResponse(
                status="success",
                message=f"Operation '{operation}' completed successfully",
                result=result,
                metadata=metadata
            )
            
        except ValidationError as e:
            return UtilityResponse(
                status="validation_error",
                message=str(e),
                result=None,
                metadata={"error_type": "validation"}
            )
        except Exception as e:
            self.logger.error(f"Error executing utility operation: {e}")
            return UtilityResponse(
                status="error",
                message="Utility operation failed",
                result=None,
                metadata={"error": str(e)}
            )
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive system metrics.
        
        Returns:
            Dictionary containing system metrics
        """
        try:
            from .utils import check_disk_space
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk_info = check_disk_space("/")
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            except:
                network_stats = {"error": "Network stats unavailable"}
            
            # Process metrics
            process = psutil.Process()
            process_info = {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": disk_info,
                "network": network_stats,
                "process": process_info
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    async def cleanup_resources(
        self,
        older_than_days: int = 30,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up old resources and data.
        
        Args:
            older_than_days: Delete resources older than this many days
            dry_run: If True, only report what would be deleted
            
        Returns:
            Cleanup results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            results = {
                "cutoff_date": cutoff_date.isoformat(),
                "dry_run": dry_run,
                "audit_logs": {"total": 0, "deleted": 0},
                "temp_files": {"total": 0, "deleted": 0}
            }
            
            if DB_AVAILABLE:
                db = next(get_db())
                try:
                    # Count old audit logs
                    old_logs_query = db.query(AuditLogORM).filter(
                        AuditLogORM.timestamp < cutoff_date
                    )
                    old_logs_count = old_logs_query.count()
                    results["audit_logs"]["total"] = old_logs_count
                    
                    if not dry_run and old_logs_count > 0:
                        deleted_count = old_logs_query.delete()
                        db.commit()
                        results["audit_logs"]["deleted"] = deleted_count
                        
                        # Log cleanup action
                        await audit_logger.log_system_event(
                            event_type="cleanup",
                            component="audit_logs",
                            details={"deleted_count": deleted_count, "cutoff_date": cutoff_date.isoformat()}
                        )
                    
                finally:
                    db.close()
            
            # Clean up temporary files
            import tempfile
            import os
            
            temp_dir = tempfile.gettempdir()
            temp_files = []
            
            try:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.startswith("ctp_") or file.startswith("tmp_"):
                            file_path = os.path.join(root, file)
                            try:
                                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                                if file_time < cutoff_date:
                                    temp_files.append(file_path)
                            except:
                                continue
                
                results["temp_files"]["total"] = len(temp_files)
                
                if not dry_run:
                    deleted_files = 0
                    for file_path in temp_files:
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                        except:
                            continue
                    
                    results["temp_files"]["deleted"] = deleted_files
            
            except Exception as e:
                results["temp_files"]["error"] = str(e)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}


# Global service instance
common_service = CommonService()
