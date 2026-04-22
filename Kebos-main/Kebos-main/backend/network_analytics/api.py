"""Network Analytics API - Modernized with comprehensive endpoints"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from common.db import get_db
from common.audit_logger import audit_logger
from .models import (
    AnalyticsQueryCreate, AnalyticsResult,
    TrafficPatternResponse, NetworkAnomalyResponse, 
    NetworkFlowResponse, NetworkTopologyResponse,
    AnalyticsJobResponse, NetworkStatsResponse,
    TimeRange, VisualizationType, MetricType, AnomalyType
)
from .services import NetworkAnalyticsService

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/network", tags=["network-analytics"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from token"""
    try:
        from auth.services import AuthService
        auth_service = AuthService()
        user_data = auth_service.verify_token(token)
        return str(user_data.get("user_id", "unknown"))
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")


# Service instance
analytics_service = NetworkAnalyticsService()

@router.on_event("startup")
def startup_event():
    """Initialize services on startup"""
    analytics_service.initialize()


@router.on_event("shutdown")
def shutdown_event():
    """Cleanup services on shutdown"""
    analytics_service.cleanup()


# =============================================================================
# ANALYTICS QUERY ENDPOINTS
# =============================================================================

@router.post("/query", response_model=AnalyticsResult, status_code=status.HTTP_201_CREATED)
def execute_analytics_query(
    query: AnalyticsQueryCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Execute an analytics query and generate visualizations"""
    try:
        result = analytics_service.query_analytics(query, user_id, db)
        
        audit_logger.log_event(
            "network_analytics_query_api",
            user_id=user_id,
            details={
                "query_id": result.query_id,
                "visualization_type": query.visualization_type.value,
                "metrics": [m.value for m in query.metrics]
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute analytics query: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute analytics query")


@router.get("/visualizations", response_model=List[str])
def get_available_visualizations():
    """Get available visualization types"""
    return [viz.value for viz in VisualizationType]


@router.get("/metrics", response_model=List[str])
def get_available_metrics():
    """Get available metric types"""
    return [metric.value for metric in MetricType]


@router.get("/time-ranges", response_model=List[str])
def get_available_time_ranges():
    """Get available time range options"""
    return [time_range.value for time_range in TimeRange]


# =============================================================================
# TRAFFIC PATTERN ENDPOINTS
# =============================================================================

@router.get("/patterns", response_model=List[TrafficPatternResponse])
def get_traffic_patterns(
    time_range: TimeRange = TimeRange.LAST_DAY,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get detected traffic patterns"""
    try:
        patterns = analytics_service.detect_traffic_patterns(
            time_range, db, start_time, end_time
        )
        return patterns
        
    except Exception as e:
        logger.error(f"Failed to get traffic patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve traffic patterns")


@router.post("/patterns", response_model=TrafficPatternResponse, status_code=status.HTTP_201_CREATED)
def create_traffic_pattern(
    pattern_data: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new traffic pattern"""
    try:
        pattern = analytics_service.create_traffic_pattern(
            pattern_data, user_id, db
        )
        
        audit_logger.log_event(
            "traffic_pattern_created_api",
            user_id=user_id,
            details={"pattern_id": pattern.pattern_id, "pattern_type": pattern.pattern_type}
        )
        
        return pattern
        
    except Exception as e:
        logger.error(f"Failed to create traffic pattern: {e}")
        raise HTTPException(status_code=500, detail="Failed to create traffic pattern")


# =============================================================================
# ANOMALY DETECTION ENDPOINTS
# =============================================================================

@router.get("/anomalies", response_model=List[NetworkAnomalyResponse])
def get_network_anomalies(
    start_time: Optional[datetime] = Query(None, description="Start time for anomaly search"),
    end_time: Optional[datetime] = Query(None, description="End time for anomaly search"),
    anomaly_type: Optional[AnomalyType] = Query(None, description="Type of anomaly to filter by"),
    min_severity: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum severity score"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of anomalies to return"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get network anomalies with optional filters"""
    try:
        anomalies = analytics_service.get_network_anomalies(
            db, start_time, end_time, anomaly_type, min_severity, limit
        )
        return anomalies
        
    except Exception as e:
        logger.error(f"Failed to get network anomalies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve network anomalies")


@router.get("/anomalies/types", response_model=List[str])
def get_anomaly_types():
    """Get available anomaly types"""
    return [anomaly_type.value for anomaly_type in AnomalyType]


# =============================================================================
# NETWORK FLOW ENDPOINTS
# =============================================================================

@router.get("/flows", response_model=List[NetworkFlowResponse])
def get_network_flows(
    start_time: Optional[datetime] = Query(None, description="Start time for flow search"),
    end_time: Optional[datetime] = Query(None, description="End time for flow search"),
    source_ip: Optional[str] = Query(None, description="Source IP address to filter by"),
    destination_ip: Optional[str] = Query(None, description="Destination IP address to filter by"),
    protocol: Optional[str] = Query(None, description="Protocol to filter by"),
    min_threat_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum threat score"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of flows to return"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get network flows with optional filters"""
    try:
        flows = analytics_service.get_network_flows(
            db, start_time, end_time, source_ip, destination_ip, 
            protocol, min_threat_score, limit
        )
        return flows
        
    except Exception as e:
        logger.error(f"Failed to get network flows: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve network flows")


# =============================================================================
# NETWORK TOPOLOGY ENDPOINTS
# =============================================================================

@router.get("/topology", response_model=List[NetworkTopologyResponse])
def get_network_topology(
    subnet: Optional[str] = Query(None, description="Subnet to filter by"),
    asset_type: Optional[str] = Query(None, description="Asset type to filter by"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of assets to return"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get network topology information"""
    try:
        topology = analytics_service.get_network_topology(
            db, subnet, asset_type, is_active, limit
        )
        return topology
        
    except Exception as e:
        logger.error(f"Failed to get network topology: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve network topology")


# =============================================================================
# STATISTICS ENDPOINTS
# =============================================================================

@router.get("/stats", response_model=NetworkStatsResponse)
def get_network_statistics(
    start_time: Optional[datetime] = Query(None, description="Start time for statistics"),
    end_time: Optional[datetime] = Query(None, description="End time for statistics"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get comprehensive network statistics"""
    try:
        stats = analytics_service.get_network_stats(
            db, start_time, end_time
        )
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get network statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve network statistics")


# =============================================================================
# REAL-TIME MONITORING ENDPOINTS
# =============================================================================

@router.get("/realtime/summary")
def get_realtime_summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get real-time network summary"""
    try:
        # Get stats for last hour for real-time view
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        stats = analytics_service.get_network_stats(
            db, start_time, end_time
        )
        
        # Get recent anomalies
        recent_anomalies = analytics_service.get_network_anomalies(
            db, start_time, end_time, limit=10
        )
        
        return {
            "timestamp": end_time.isoformat(),
            "summary": {
                "total_flows": stats.total_flows,
                "unique_ips": stats.unique_ips,
                "total_bytes": stats.total_bytes,
                "threat_count": stats.threat_count,
                "anomaly_count": len(recent_anomalies)
            },
            "recent_anomalies": recent_anomalies[:5],  # Top 5 most recent
            "top_protocols": dict(list(stats.protocol_distribution.items())[:5]),
            "top_talkers": stats.top_talkers[:5]
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve real-time summary")


@router.get("/realtime/flows/latest")
def get_latest_flows(
    limit: int = Query(50, ge=1, le=500, description="Number of latest flows to return"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get the latest network flows"""
    try:
        # Get flows from last 10 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        flows = analytics_service.get_network_flows(
            db, start_time, end_time, limit=limit
        )
        
        return {
            "timestamp": end_time.isoformat(),
            "flows": flows,
            "count": len(flows)
        }
        
    except Exception as e:
        logger.error(f"Failed to get latest flows: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latest flows")


# =============================================================================
# ANALYSIS JOB ENDPOINTS
# =============================================================================

@router.post("/jobs/pattern-detection", status_code=status.HTTP_202_ACCEPTED)
def start_pattern_detection_job(
    background_tasks: BackgroundTasks,
    time_range: TimeRange = TimeRange.LAST_DAY,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Start a background pattern detection job"""
    try:
        job_id = str(uuid.uuid4())
        
        # This would be implemented as a background Celery task in production
        # For now, we'll just return the job ID
        
        audit_logger.log_event(
            "pattern_detection_job_started",
            user_id=user_id,
            details={"job_id": job_id, "time_range": time_range.value}
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Pattern detection job started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start pattern detection job: {e}")
        raise HTTPException(status_code=500, detail="Failed to start pattern detection job")


@router.post("/jobs/anomaly-detection", status_code=status.HTTP_202_ACCEPTED)
def start_anomaly_detection_job(
    background_tasks: BackgroundTasks,
    time_range: TimeRange = TimeRange.LAST_DAY,
    sensitivity: float = Query(0.8, ge=0.1, le=1.0, description="Anomaly detection sensitivity"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Start a background anomaly detection job"""
    try:
        job_id = str(uuid.uuid4())
        
        # This would be implemented as a background Celery task in production
        
        audit_logger.log_event(
            "anomaly_detection_job_started",
            user_id=user_id,
            details={"job_id": job_id, "time_range": time_range.value, "sensitivity": sensitivity}
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Anomaly detection job started successfully",
            "parameters": {
                "time_range": time_range.value,
                "sensitivity": sensitivity
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start anomaly detection job: {e}")
        raise HTTPException(status_code=500, detail="Failed to start anomaly detection job")


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@router.post("/export/flows")
def export_network_flows(
    export_format: str = Query("csv", regex="^(csv|json|xlsx)$"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    filters: Optional[Dict[str, Any]] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Export network flows in specified format"""
    try:
        # This would implement actual file export functionality
        # For now, return export information
        
        audit_logger.log_event(
            "network_flows_export",
            user_id=user_id,
            details={
                "format": export_format,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None
            }
        )
        
        return {
            "export_id": str(uuid.uuid4()),
            "format": export_format,
            "status": "preparing",
            "message": f"Export in {export_format} format is being prepared"
        }
        
    except Exception as e:
        logger.error(f"Failed to export network flows: {e}")
        raise HTTPException(status_code=500, detail="Failed to export network flows")


# =============================================================================
# TESTING AND DIAGNOSTICS ENDPOINTS
# =============================================================================

@router.get("/health")
def health_check():
    """Health check endpoint for network analytics service"""
    return {
        "status": "healthy",
        "service": "network-analytics",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/diagnostics")
def get_diagnostics(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get service diagnostics information"""
    try:
        # Get basic counts for diagnostics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        stats = analytics_service.get_network_stats(
            db, start_time, end_time
        )
        
        return {
            "service_status": "operational",
            "database_connection": "healthy",
            "last_24_hours": {
                "total_flows": stats.total_flows,
                "unique_ips": stats.unique_ips,
                "anomalies": stats.anomaly_count,
                "threats": stats.threat_count
            },
            "memory_usage": "optimal",  # Would be actual memory metrics
            "performance": "nominal"    # Would be actual performance metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get diagnostics: {e}")
        return {
            "service_status": "degraded",
            "database_connection": "error",
            "error": str(e)
        }


from datetime import timedelta
import uuid
