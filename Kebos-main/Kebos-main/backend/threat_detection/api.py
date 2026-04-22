"""
Threat Detection API Endpoints

FastAPI endpoints for threat detection, alerts, and real-time monitoring.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import json
import asyncio
import logging
import uuid

from .models import ThreatAlert, NetworkPacket, AnomalyReport, ThreatLevel
# from .services import ThreatDetectionService
from .services import ThreatDetectionService
from .catboost_detector import catboost_detector
from auth.services import AuthService
from common.models import ThreatAlertORM
from common.db import get_db
from audit_logger.services import AuditLoggerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threats", tags=["threat-detection"])
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

# Global service instances
threat_service = ThreatDetectionService()
audit_service = AuditLoggerService()

# WebSocket connection manager for real-time alerts
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()


@router.on_event("startup")
async def startup_event():
    """Initialize threat detection service on startup"""
    await threat_service.initialize()
    logger.info("Threat detection API initialized")


# CRUD Endpoints for Frontend Integration
@router.get("/", response_model=List[Dict[str, Any]])
async def get_threats(
    severity: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    source: Optional[List[str]] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get threat alerts with filtering"""
    try:
        query = db.query(ThreatAlertORM)
        
        # Apply filters
        if severity:
            query = query.filter(ThreatAlertORM.severity.in_(severity))
        if status:
            query = query.filter(ThreatAlertORM.status.in_(status))
        if source:
            query = query.filter(ThreatAlertORM.source.in_(source))
        if search:
            query = query.filter(
                ThreatAlertORM.title.contains(search) |
                ThreatAlertORM.description.contains(search)
            )
        
        # Order by most recent
        threats = query.order_by(desc(ThreatAlertORM.created_at)).offset(offset).limit(limit).all()
        
        # Convert to API response format
        result = []
        for threat in threats:
            result.append({
                "id": threat.alert_id,
                "title": threat.title,
                "description": threat.description,
                "severity": threat.severity,
                "type": threat.threat_type,
                "source": threat.source,
                "status": threat.status,
                "timestamp": threat.created_at.isoformat(),
                "affectedSystems": threat.affected_systems or [],
                "indicators": threat.indicators or [],
                "mitigations": threat.mitigations or []
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get threats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threats")

@router.get("/stats", response_model=Dict[str, Any])
async def get_threat_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get threat statistics"""
    try:
        total = db.query(ThreatAlertORM).count()
        active = db.query(ThreatAlertORM).filter(ThreatAlertORM.status == "active").count()
        resolved = db.query(ThreatAlertORM).filter(ThreatAlertORM.status == "resolved").count()
        critical = db.query(ThreatAlertORM).filter(ThreatAlertORM.severity == "critical").count()
        high = db.query(ThreatAlertORM).filter(ThreatAlertORM.severity == "high").count()
        medium = db.query(ThreatAlertORM).filter(ThreatAlertORM.severity == "medium").count()
        low = db.query(ThreatAlertORM).filter(ThreatAlertORM.severity == "low").count()
        
        return {
            "total": total,
            "active": active,
            "resolved": resolved,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        }
        
    except Exception as e:
        logger.error(f"Failed to get threat stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threat statistics")

@router.get("/{threat_id}", response_model=Dict[str, Any])
async def get_threat_by_id(
    threat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get specific threat details"""
    try:
        threat = db.query(ThreatAlertORM).filter(ThreatAlertORM.alert_id == threat_id).first()
        
        if not threat:
            raise HTTPException(status_code=404, detail="Threat not found")
        
        return {
            "id": threat.alert_id,
            "title": threat.title,
            "description": threat.description,
            "severity": threat.severity,
            "type": threat.threat_type,
            "source": threat.source,
            "status": threat.status,
            "timestamp": threat.created_at.isoformat(),
            "affectedSystems": threat.affected_systems or [],
            "indicators": threat.indicators or [],
            "mitigations": threat.mitigations or [],
            "sourceIp": threat.source_ip,
            "destinationIp": threat.destination_ip,
            "attackVector": threat.attack_vector,
            "mitreAttackId": threat.mitre_attack_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get threat {threat_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threat")

@router.patch("/{threat_id}/status", response_model=Dict[str, Any])
async def update_threat_status(
    threat_id: str,
    status_update: Dict[str, str],
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update threat status"""
    try:
        threat = db.query(ThreatAlertORM).filter(ThreatAlertORM.alert_id == threat_id).first()
        
        if not threat:
            raise HTTPException(status_code=404, detail="Threat not found")
        
        new_status = status_update.get("status")
        if new_status not in ["active", "investigating", "resolved", "false_positive"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        threat.status = new_status
        threat.updated_at = datetime.utcnow()
        
        if new_status == "resolved":
            threat.resolved_at = datetime.utcnow()
            threat.resolved_by = int(user_id)
        
        db.commit()
        
        return {
            "id": threat.alert_id,
            "status": threat.status,
            "updated_at": threat.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update threat status {threat_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update threat status")


@router.post("/detect", response_model=Optional[ThreatAlert])
async def detect_threat(
    packet: NetworkPacket,
    user_id: str = Depends(get_current_user_id)
):
    """
    Process a single network packet for threat detection using CatBoost models.
    Returns threat alert if significant threat is detected.
    """
    try:
        # Process packet through CatBoost detection pipeline
        alert = await catboost_detector.detect_threat(packet)
        
        # If no threat detected by CatBoost, try the legacy detection
        if not alert:
            alert = await threat_service.detect_single_threat(packet)
        
        # Log the detection request
        await audit_service.log_event(
            user_id=user_id,
            action="threat_detection",
            resource="network_packet",
            details={
                "source_ip": packet.source_ip,
                "destination_ip": packet.destination_ip,
                "protocol": packet.protocol,
                "detection_method": "catboost" if alert and "CatBoost" in str(alert.detection_method) else "legacy",
                "alert_generated": alert is not None
            }
        )
        
        # Broadcast alert via WebSocket if generated
        if alert:
            await manager.broadcast({
                "type": "threat_alert",
                "data": alert.dict()
            })
        
        return alert
        
    except Exception as e:
        logger.error(f"Error in threat detection: {e}")
        raise HTTPException(status_code=500, detail="Threat detection failed")


@router.post("/detect-catboost", response_model=Optional[ThreatAlert])
async def detect_threat_catboost(
    packet: NetworkPacket,
    user_id: str = Depends(get_current_user_id)
):
    """
    Process a single network packet for threat detection using only CatBoost models.
    Returns threat alert if significant threat is detected.
    """
    try:
        # Process packet through CatBoost detection pipeline only
        alert = await catboost_detector.detect_threat(packet)
        
        # Log the detection request
        await audit_service.log_event(
            user_id=user_id,
            action="catboost_threat_detection",
            resource="network_packet",
            details={
                "source_ip": packet.source_ip,
                "destination_ip": packet.destination_ip,
                "protocol": packet.protocol,
                "detection_method": "catboost_only",
                "alert_generated": alert is not None
            }
        )
        
        # Broadcast alert via WebSocket if generated
        if alert:
            await manager.broadcast({
                "type": "threat_alert",
                "data": alert.dict()
            })
        
        return alert
        
    except Exception as e:
        logger.error(f"Error in CatBoost threat detection: {e}")
        raise HTTPException(status_code=500, detail="CatBoost threat detection failed")


@router.post("/batch-detect", response_model=List[ThreatAlert])
async def batch_detect_threats(
    packets: List[NetworkPacket],
    user_id: str = Depends(get_current_user_id)
):
    """
    Process multiple network packets for threat detection.
    Returns list of threat alerts.
    """
    try:
        alerts = []
        
        for packet in packets:
            alert = await threat_service.process_packet(packet)
            if alert:
                alerts.append(alert)
        
        # Log batch detection
        await audit_service.log_event(
            user_id=user_id,
            action="batch_threat_detection",
            resource="network_packets",
            details={
                "packet_count": len(packets),
                "alerts_generated": len(alerts)
            }
        )
        
        # Broadcast alerts
        for alert in alerts:
            await manager.broadcast({
                "type": "threat_alert",
                "data": alert.dict()
            })
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error in batch threat detection: {e}")
        raise HTTPException(status_code=500, detail="Batch threat detection failed")


@router.get("/alerts", response_model=List[ThreatAlert])
async def get_alerts(
    limit: int = 100,
    threat_level: Optional[ThreatLevel] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id)
):
    """
    Retrieve historical threat alerts with filtering options.
    """
    try:
        # TODO: Implement database query for historical alerts
        # For now, return empty list as this would require database implementation
        
        await audit_service.log_event(
            user_id=user_id,
            action="view_alerts",
            resource="threat_alerts",
            details={
                "limit": limit,
                "threat_level": threat_level.value if threat_level else None,
                "time_range": {
                    "start": start_time.isoformat() if start_time else None,
                    "end": end_time.isoformat() if end_time else None
                }
            }
        )
        
        return []
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/stats")
async def get_detection_stats(
    user_id: str = Depends(get_current_user_id)
):
    """
    Get threat detection statistics and metrics.
    """
    try:
        # Mock statistics - would be from database in real implementation
        stats = {
            "total_packets_processed": 15423,
            "total_alerts": 45,
            "alerts_by_level": {
                "critical": 5,
                "high": 12,
                "medium": 18,
                "low": 10
            },
            "detection_accuracy": 0.94,
            "false_positive_rate": 0.06,
            "average_processing_time_ms": 23.5,
            "last_24h_activity": {
                "packets": 3421,
                "alerts": 8,
                "unique_sources": 234,
                "unique_destinations": 567
            }
        }
        
        await audit_service.log_event(
            user_id=user_id,
            action="view_stats",
            resource="detection_statistics",
            details={}
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/catboost-status", response_model=Dict[str, Any])
async def get_catboost_status(
    user_id: str = Depends(get_current_user_id)
):
    """
    Get CatBoost threat detector status and health information.
    """
    try:
        status = await catboost_detector.get_health_status()
        
        await audit_service.log_event(
            user_id=user_id,
            action="view_catboost_status",
            resource="catboost_detector",
            details={}
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Error retrieving CatBoost status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve CatBoost status")


@router.websocket("/alerts/stream")
async def stream_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time threat alert streaming.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for threat detection service.
    """
    try:
        # Check service health
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "anomaly_detection": "running",
                "threat_analysis": "running",
                "websocket_manager": f"{len(manager.active_connections)} connections"
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
