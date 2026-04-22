"""SIEM Integration API - Modernized async version"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import get_async_session
from common.audit_logger import audit_logger
from .models import (
    SIEMConfigCreate, SIEMConfigUpdate, SIEMConfigResponse,
    SIEMEventCreate, SIEMEventResponse,
    SIEMQueryRequest, SIEMQueryResponse,
    SIEMHealthStatus, SIEMWebhookPayload, SIEMStatsResponse,
    SIEMType, SIEMAuthType, SIEMEventSeverity
)
from .services import siem_service

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/siem", tags=["siem-integration"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from token - simplified for demo"""
    # TODO: Implement proper token validation and user extraction
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return "demo_user_id"  # Replace with actual user ID extraction


@router.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await siem_service.initialize()


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    await siem_service.cleanup()


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================

@router.post("/config", response_model=SIEMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_siem_config(
    config: SIEMConfigCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new SIEM configuration"""
    try:
        result = await siem_service.create_siem_config(config, user_id, db)
        
        await audit_logger.log_event(
            "siem_config_api_create",
            user_id=user_id,
            details={"config_id": str(result.id), "name": config.name}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to create SIEM config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create SIEM configuration")


@router.get("/config/{config_id}", response_model=SIEMConfigResponse)
async def get_siem_config(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Get SIEM configuration by ID"""
    try:
        config = await siem_service.get_siem_config(config_id, db)
        if not config:
            raise HTTPException(status_code=404, detail="SIEM configuration not found")
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SIEM config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve SIEM configuration")


@router.get("/configs", response_model=List[SIEMConfigResponse])
async def list_siem_configs(
    is_active: Optional[bool] = None,
    siem_type: Optional[SIEMType] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """List SIEM configurations with optional filters"""
    try:
        configs = await siem_service.list_siem_configs(db, is_active, siem_type)
        return configs
        
    except Exception as e:
        logger.error(f"Failed to list SIEM configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve SIEM configurations")


@router.put("/config/{config_id}", response_model=SIEMConfigResponse)
async def update_siem_config(
    config_id: str,
    config_update: SIEMConfigUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Update SIEM configuration"""
    try:
        config = await siem_service.update_siem_config(config_id, config_update, user_id, db)
        if not config:
            raise HTTPException(status_code=404, detail="SIEM configuration not found")
        
        await audit_logger.log_event(
            "siem_config_api_update",
            user_id=user_id,
            details={"config_id": config_id}
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update SIEM config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update SIEM configuration")


@router.delete("/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_siem_config(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete SIEM configuration"""
    try:
        success = await siem_service.delete_siem_config(config_id, user_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="SIEM configuration not found")
        
        await audit_logger.log_event(
            "siem_config_api_delete",
            user_id=user_id,
            details={"config_id": config_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete SIEM config: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete SIEM configuration")


# =============================================================================
# HEALTH MONITORING ENDPOINTS
# =============================================================================

@router.get("/config/{config_id}/health", response_model=SIEMHealthStatus)
async def check_siem_health(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Check health status of a SIEM configuration"""
    try:
        health_status = await siem_service.check_siem_health(config_id, db)
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to check SIEM health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check SIEM health")


# =============================================================================
# EVENT INGESTION ENDPOINTS
# =============================================================================

@router.post("/events", response_model=SIEMEventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    event: SIEMEventCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Ingest a single SIEM event"""
    try:
        result = await siem_service.ingest_event(event, db)
        
        await audit_logger.log_event(
            "siem_event_ingested",
            user_id=user_id,
            details={"event_id": event.event_id, "config_id": event.siem_config_id}
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to ingest event: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest event")


@router.post("/events/batch", response_model=List[SIEMEventResponse], status_code=status.HTTP_201_CREATED)
async def ingest_events_batch(
    events: List[SIEMEventCreate],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Ingest multiple SIEM events in batch"""
    try:
        results = await siem_service.ingest_events_batch(events, db)
        
        await audit_logger.log_event(
            "siem_events_batch_ingested",
            user_id=user_id,
            details={"event_count": len(events), "successful_count": len(results)}
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to ingest events batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest events batch")


@router.get("/events", response_model=List[SIEMEventResponse])
async def get_events(
    siem_config_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    severity: Optional[SIEMEventSeverity] = None,
    event_type: Optional[str] = None,
    source_ip: Optional[str] = None,
    user: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Query SIEM events with filters"""
    try:
        events = await siem_service.get_events(
            db, siem_config_id, start_time, end_time, severity,
            event_type, source_ip, user, skip, limit
        )
        return events
        
    except Exception as e:
        logger.error(f"Failed to get events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve events")


# =============================================================================
# QUERY EXECUTION ENDPOINTS
# =============================================================================

@router.post("/config/{config_id}/query", response_model=SIEMQueryResponse)
async def execute_query(
    config_id: str,
    query_request: SIEMQueryRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Execute a query against a SIEM system"""
    try:
        result = await siem_service.execute_query(config_id, query_request, user_id, db)
        
        await audit_logger.log_event(
            "siem_query_executed",
            user_id=user_id,
            details={
                "config_id": config_id,
                "query_type": query_request.query_type,
                "execution_time": result.execution_time_seconds
            }
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute query")


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@router.post("/webhook", response_model=Dict[str, Any])
async def receive_webhook(
    payload: SIEMWebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Receive webhook from SIEM system"""
    try:
        # Process webhook in background to quickly respond to the SIEM system
        background_tasks.add_task(siem_service.process_webhook, payload, db)
        
        return {
            "status": "accepted",
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": str(payload.dict().get("webhook_id", "unknown"))
        }
        
    except Exception as e:
        logger.error(f"Failed to receive webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/webhook/raw")
async def receive_raw_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Receive raw webhook data from SIEM system"""
    try:
        # Get raw JSON data
        raw_data = await request.json()
        
        # Extract SIEM source from headers or query params
        siem_source = (
            request.headers.get("X-SIEM-Source") or 
            request.query_params.get("siem_source") or
            "unknown"
        )
        
        # Create webhook payload
        payload = SIEMWebhookPayload(
            siem_source=siem_source,
            event_type="raw_webhook",
            event_data=raw_data,
            signature=request.headers.get("X-Signature"),
            received_at=datetime.utcnow()
        )
        
        # Process webhook in background
        background_tasks.add_task(siem_service.process_webhook, payload, db)
        
        return {
            "status": "accepted",
            "timestamp": datetime.utcnow().isoformat(),
            "siem_source": siem_source
        }
        
    except Exception as e:
        logger.error(f"Failed to receive raw webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process raw webhook")


# =============================================================================
# STATISTICS ENDPOINTS
# =============================================================================

@router.get("/stats", response_model=SIEMStatsResponse)
async def get_siem_stats(
    config_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Get SIEM integration statistics"""
    try:
        stats = await siem_service.get_stats(db, config_id, start_time, end_time)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get SIEM stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


# =============================================================================
# METADATA ENDPOINTS
# =============================================================================

@router.get("/types", response_model=List[str])
async def get_siem_types():
    """Get available SIEM types"""
    return [siem_type.value for siem_type in SIEMType]


@router.get("/auth-types", response_model=List[str])
async def get_auth_types():
    """Get available SIEM authentication types"""
    return [auth_type.value for auth_type in SIEMAuthType]


@router.get("/severities", response_model=List[str])
async def get_event_severities():
    """Get available event severity levels"""
    return [severity.value for severity in SIEMEventSeverity]


# =============================================================================
# TESTING ENDPOINTS (Development only)
# =============================================================================

@router.post("/test/connection/{config_id}")
async def test_connection(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Test connection to a SIEM system (development endpoint)"""
    try:
        health_status = await siem_service.check_siem_health(config_id, db)
        
        return {
            "config_id": config_id,
            "connection_status": health_status.status.value,
            "auth_success": health_status.auth_success,
            "api_success": health_status.api_success,
            "last_check": health_status.last_check.isoformat(),
            "error": health_status.error
        }
        
    except Exception as e:
        logger.error(f"Failed to test connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to test connection")
