"""
SIEM Integration API

API endpoints for SIEM integration, configuration, and querying.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from .models import (
    SIEMConfigCreate,
    SIEMConfigUpdate,
    SIEMConfigResponse,
    SIEMEventResponse,
    SIEMQueryResponse,
    SIEMWebhookPayload,
    SIEMQuery,
    SIEMHealthStatus,
    SIEMType,
    SIEMAuthType
)
from .services import SIEMIntegrationService

router = APIRouter(prefix="/siem", tags=["siem-integration"])

# Service instance
siem_service = SIEMIntegrationService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from token"""
    try:
        from auth.services import AuthService
        auth_service = AuthService()
        user_data = auth_service.verify_token(token)
        return str(user_data.get("user_id", "unknown"))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")


@router.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await siem_service.initialize()


@router.post("/config", response_model=Dict[str, str])
async def add_siem_config(config: SIEMConfigCreate, user_id: str = Depends(get_current_user_id)):
    """
    Add a new SIEM configuration. Requires authentication.
    """
    try:
        siem_id = await siem_service.add_siem_config(config)
        return {"siem_id": siem_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/{siem_id}", response_model=Dict[str, bool])
async def update_siem_config(siem_id: str, config: SIEMConfigUpdate, user_id: str = Depends(get_current_user_id)):
    """
    Update an existing SIEM configuration. Requires authentication.
    """
    config.siem_id = siem_id
    try:
        success = await siem_service.update_siem_config(config)
        if not success:
            raise HTTPException(status_code=404, detail=f"SIEM configuration with ID {siem_id} not found")
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/config/{siem_id}", response_model=Dict[str, bool])
async def delete_siem_config(siem_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Delete a SIEM configuration. Requires authentication.
    """
    try:
        success = await siem_service.delete_siem_config(siem_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"SIEM configuration with ID {siem_id} not found")
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{siem_id}", response_model=SIEMConfigResponse)
async def get_siem_config(siem_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Get a SIEM configuration by ID. Requires authentication.
    """
    try:
        config = await siem_service.get_siem_config(siem_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"SIEM configuration with ID {siem_id} not found")
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs", response_model=List[SIEMConfigResponse])
async def list_siem_configs(user_id: str = Depends(get_current_user_id)):
    """
    List all SIEM configurations. Requires authentication.
    """
    try:
        configs = await siem_service.list_siem_configs()
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{siem_id}", response_model=SIEMHealthStatus)
async def get_siem_health(siem_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Get health status for a SIEM integration. Requires authentication.
    """
    try:
        status = await siem_service.get_siem_health(siem_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"SIEM with ID {siem_id} not found")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/{siem_id}", response_model=SIEMQueryResponse)
async def query_siem(siem_id: str, query: SIEMQuery, user_id: str = Depends(get_current_user_id)):
    """
    Query a SIEM system with the provided query parameters. Requires authentication.
    """
    try:
        response = await siem_service.query_siem(siem_id, query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook", response_model=Dict[str, Any])
async def receive_webhook(payload: SIEMWebhookPayload, background_tasks: BackgroundTasks):
    """
    Receive webhook from SIEM system. No authentication required (external SIEM systems).
    """
    try:
        # Process webhook in background to quickly respond to the SIEM system
        background_tasks.add_task(siem_service.process_webhook, payload)
        return {"status": "accepted", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/raw", response_model=Dict[str, Any])
async def receive_raw_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive raw webhook data from SIEM system. No authentication required (external SIEM systems).
    """
    try:
        # Get raw JSON data
        raw_data = await request.json()
        # Extract SIEM ID from headers or query params
        siem_id = request.headers.get("X-SIEM-ID") or request.query_params.get("siem_id")
        if not siem_id:
            raise HTTPException(status_code=400, detail="Missing SIEM ID in headers or query parameters")
        # Create webhook payload
        payload = SIEMWebhookPayload(
            siem_id=siem_id,
            webhook_id=str(uuid4()),
            raw_data=raw_data,
            timestamp=datetime.utcnow()
        )
        
        # Process webhook in background
        background_tasks.add_task(siem_service.process_webhook, payload)
        return {"status": "accepted", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types", response_model=List[str])
async def get_siem_types():
    """
    Get available SIEM types.
    """
    return [siem_type.value for siem_type in SIEMType]


@router.get("/auth-types", response_model=List[str])
async def get_auth_types():
    """
    Get available SIEM authentication types.
    """
    return [auth_type.value for auth_type in SIEMAuthType]