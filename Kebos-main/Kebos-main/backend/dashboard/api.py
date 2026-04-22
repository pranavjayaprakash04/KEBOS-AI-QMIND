"""
Dashboard API endpoints for CTP Platform
Provides aggregated metrics and real-time data for the dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from common.db import get_db
from common.models import AuditLogORM, UserORM, ThreatAlertORM
from auth.services import AuthService
from job_manager.models import JobORM

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from token"""
    try:
        auth_service = AuthService()
        user_data = auth_service.verify_token(token)
        return str(user_data.get("user_id", "unknown"))
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

@router.get("/metrics")
def get_dashboard_metrics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get aggregated dashboard metrics"""
    try:
        # Get current datetime for filtering
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Count active threats (last 24 hours)
        active_threats = db.query(ThreatAlertORM).filter(
            ThreatAlertORM.created_at >= last_24h
        ).count()
        
        # Count active jobs
        active_jobs = db.query(JobORM).filter(
            JobORM.status.in_(["pending", "running"])
        ).count()
        
        # Threats by type (last 7 days)
        threat_type_counts = db.query(
            ThreatAlertORM.threat_type,
            func.count(ThreatAlertORM.id).label('count')
        ).filter(
            ThreatAlertORM.created_at >= last_7d
        ).group_by(ThreatAlertORM.threat_type).all()
        
        threats_by_type = {}
        for threat_type, count in threat_type_counts:
            threats_by_type[threat_type] = count
            
        # Threats by severity (last 7 days)  
        threat_severity_counts = db.query(
            ThreatAlertORM.severity,
            func.count(ThreatAlertORM.id).label('count')
        ).filter(
            ThreatAlertORM.created_at >= last_7d
        ).group_by(ThreatAlertORM.severity).all()
        
        threats_by_severity = {}
        for severity, count in threat_severity_counts:
            threats_by_severity[severity] = count
        
        return {
            "activeThreats": active_threats,
            "activeJobs": active_jobs,
            "threatsByType": threats_by_type,
            "threatsBySeverity": threats_by_severity
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics")

@router.get("/threat-activity")
def get_threat_activity(
    timeRange: str = "7d",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get threat activity data for charts"""
    try:
        # Parse time range
        if timeRange == "24h":
            start_time = datetime.utcnow() - timedelta(hours=24)
            interval_hours = 1
            labels = [f"{i:02d}:00" for i in range(24)]
        elif timeRange == "7d":
            start_time = datetime.utcnow() - timedelta(days=7)
            interval_hours = 24
            labels = [(datetime.utcnow() - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
        elif timeRange == "30d":
            start_time = datetime.utcnow() - timedelta(days=30)
            interval_hours = 24 * 7  # Weekly intervals
            labels = [f"Week {i+1}" for i in range(4)]
        else:
            start_time = datetime.utcnow() - timedelta(days=7)
            interval_hours = 24
            labels = [(datetime.utcnow() - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
        
        # Get threat data grouped by time intervals
        critical_data = []
        high_data = []
        
        for i, label in enumerate(labels):
            period_start = start_time + timedelta(hours=interval_hours * i)
            period_end = start_time + timedelta(hours=interval_hours * (i + 1))
            
            critical_count = db.query(ThreatAlertORM).filter(
                ThreatAlertORM.created_at >= period_start,
                ThreatAlertORM.created_at < period_end,
                ThreatAlertORM.severity == "critical"
            ).count()
            
            high_count = db.query(ThreatAlertORM).filter(
                ThreatAlertORM.created_at >= period_start,
                ThreatAlertORM.created_at < period_end,
                ThreatAlertORM.severity == "high"
            ).count()
            
            critical_data.append(critical_count)
            high_data.append(high_count)
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Critical Threats",
                    "data": critical_data,
                    "borderColor": "#ef4444",
                    "backgroundColor": "rgba(239, 68, 68, 0.2)"
                },
                {
                    "label": "High Threats",
                    "data": high_data,
                    "borderColor": "#f97316",
                    "backgroundColor": "rgba(249, 115, 22, 0.2)"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get threat activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threat activity")

@router.get("/network-metrics")
def get_network_metrics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get network metrics and statistics"""
    try:
        # This would integrate with network analytics service
        # Get real network metrics from database
        try:
            from network_analytics.services import NetworkAnalyticsService
            analytics_service = NetworkAnalyticsService()
            
            # Get real network metrics
            network_stats = analytics_service.get_network_statistics()
            top_sources = analytics_service.get_top_traffic_sources(limit=3)
            
            return {
                "totalBandwidth": network_stats.get("total_bandwidth", 0),
                "activeConnections": network_stats.get("active_connections", 0),
                "packetsProcessed": network_stats.get("packets_processed", 0),
                "anomaliesDetected": network_stats.get("anomalies_detected", 0),
                "topSources": top_sources
            }
        except Exception as e:
            logger.error(f"Failed to get real network metrics: {e}")
            # Return empty/zero values instead of mock data
            return {
                "totalBandwidth": 0,
                "activeConnections": 0,
                "packetsProcessed": 0,
                "anomaliesDetected": 0,
                "topSources": []
            }
        
    except Exception as e:
        logger.error(f"Failed to get network metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve network metrics")

@router.get("/recent-activity")
def get_recent_activity(
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get recent system activity"""
    try:
        # Get recent audit logs
        recent_logs = db.query(AuditLogORM).order_by(
            desc(AuditLogORM.timestamp)
        ).limit(limit).all()
        
        activities = []
        for log in recent_logs:
            activities.append({
                "id": str(log.id),
                "type": "audit",
                "message": f"{log.action} on {log.resource}",
                "timestamp": log.timestamp.isoformat(),
                "userId": str(log.user_id) if log.user_id else None,
                "details": log.details
            })
        
        return activities
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent activity")

@router.get("/system-health")
def get_system_health(
    user_id: str = Depends(get_current_user_id)
):
    """Get system health metrics"""
    try:
        import psutil
        
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get uptime (approximate)
        import time
        uptime_seconds = time.time() - psutil.boot_time()
        
        return {
            "uptime": int(uptime_seconds),
            "cpuUsage": cpu_usage,
            "memoryUsage": memory.percent,
            "diskUsage": disk.percent,
            "status": "healthy" if cpu_usage < 80 and memory.percent < 80 else "warning"
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        # Return empty data instead of mock values
        return {
            "uptime": 0,
            "cpuUsage": 0,
            "memoryUsage": 0,
            "diskUsage": 0,
            "status": "unavailable",
            "error": "System health monitoring unavailable"
        }
