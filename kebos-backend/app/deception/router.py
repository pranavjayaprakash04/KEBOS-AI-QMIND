from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile
from app.deception.honeygrid_manager import (
    HoneyGridManager,
    HoneytokenType,
    get_honeygrid_manager
)
import asyncpg

router = APIRouter(prefix="/api/v1/honeygrid", tags=["honeygrid"])


class CreateHoneytokenRequest(BaseModel):
    token_type: str  # aws_access_key, database_credential, api_token
    description: str
    custom_value: Optional[str] = None


class DeployHoneytokenRequest(BaseModel):
    honeytoken_id: str
    deployment_target: str


class TriggerHoneytokenRequest(BaseModel):
    honeytoken_value: str
    trigger_source: str
    metadata: Optional[dict] = None


@router.post("/honeytokens")
async def create_honeytoken(
    request: CreateHoneytokenRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Create a new honeytoken"""
    # Validate token type
    try:
        token_type = HoneytokenType(request.token_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid token type: {request.token_type}. "
                   f"Must be one of: {[t.value for t in HoneytokenType]}"
        )
    
    # Only admins can create honeytokens
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only admins can create honeytokens"
        )
    
    manager = get_honeygrid_manager()
    honeytoken = await manager.create_honeytoken(
        token_type=token_type,
        description=request.description,
        custom_value=request.custom_value
    )
    
    return {
        "id": honeytoken.id,
        "token_type": honeytoken.token_type.value,
        "value": honeytoken.value,
        "description": honeytoken.description,
        "message": "Honeytoken created successfully"
    }


@router.post("/honeytokens/deploy")
async def deploy_honeytoken(
    request: DeployHoneytokenRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Deploy a honeytoken to a target"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only admins can deploy honeytokens"
        )
    
    manager = get_honeygrid_manager()
    success = await manager.deploy_honeytoken(
        honeytoken_id=request.honeytoken_id,
        deployment_target=request.deployment_target
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to deploy honeytoken"
        )
    
    return {"message": "Honeytoken deployed successfully"}


@router.post("/honeytokens/trigger")
async def trigger_honeytoken(
    request: TriggerHoneytokenRequest
):
    """
    Handle honeytoken trigger.
    This endpoint is typically called by monitoring systems.
    """
    manager = get_honeygrid_manager()
    threat_id = await manager.trigger_honeytoken(
        honeytoken_value=request.honeytoken_value,
        trigger_source=request.trigger_source,
        metadata=request.metadata
    )
    
    if threat_id:
        return {
            "threat_id": threat_id,
            "message": "Honeytoken triggered successfully"
        }
    else:
        return {
            "message": "Honeytoken not found or inactive"
        }


@router.get("/honeytokens")
async def list_honeytokens(
    active_only: bool = True,
    current_user: UserProfile = Depends(get_current_user)
):
    """List all honeytokens"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only admins can list honeytokens"
        )
    
    manager = get_honeygrid_manager()
    honeytokens = await manager.list_honeytokens(active_only=active_only)
    
    return {
        "honeytokens": [
            {
                "id": h.id,
                "token_type": h.token_type.value,
                "value": h.value,
                "description": h.description,
                "deployed_at": h.deployed_at,
                "last_triggered": h.last_triggered,
                "trigger_count": h.trigger_count,
                "is_active": h.is_active
            }
            for h in honeytokens
        ]
    }


@router.delete("/honeytokens/{honeytoken_id}")
async def revoke_honeytoken(
    honeytoken_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Revoke a honeytoken"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only admins can revoke honeytokens"
        )
    
    manager = get_honeygrid_manager()
    success = await manager.revoke_honeytoken(honeytoken_id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke honeytoken"
        )
    
    return {"message": "Honeytoken revoked successfully"}
