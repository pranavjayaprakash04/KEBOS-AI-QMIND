"""
Tenant Management Router - CRUD endpoints for tenant management

Admin-only access for tenant CRUD operations.
Includes per-tenant thresholds and auth policies.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile
import asyncpg
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/tenants", tags=["admin"])


class TenantType(str, Enum):
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class AuthPolicy(str, Enum):
    PASSWORD_ONLY = "password_only"
    MFA_REQUIRED = "mfa_required"
    FIDO2_REQUIRED = "fido2_required"


class TenantCreate(BaseModel):
    """Create tenant request"""
    name: str
    organisation_name: str
    tenant_type: TenantType
    auth_policy: AuthPolicy = AuthPolicy.MFA_REQUIRED
    confidence_threshold: float = 0.5
    sla_hours: int = 6


class TenantUpdate(BaseModel):
    """Update tenant request"""
    name: Optional[str] = None
    organisation_name: Optional[str] = None
    auth_policy: Optional[AuthPolicy] = None
    confidence_threshold: Optional[float] = None
    sla_hours: Optional[int] = None


@router.post("/")
async def create_tenant(
    tenant: TenantCreate,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Create a new tenant (ADMIN role only).
    
    Includes per-tenant thresholds and auth policies.
    """
    # Verify admin role
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    import uuid
    tenant_id = str(uuid.uuid4())
    
    try:
        async with app.state.db_pool.acquire() as conn:
            # Insert tenant
            await conn.execute(
                """
                INSERT INTO tenants (id, name, organisation_name, tenant_type, auth_policy, confidence_threshold, sla_hours)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                tenant_id, tenant.name, tenant.organisation_name,
                tenant.tenant_type.value, tenant.auth_policy.value,
                tenant.confidence_threshold, tenant.sla_hours
            )
            
            logger.info(f"Created tenant {tenant_id} by admin {current_user.username}")
            
            return {
                "id": tenant_id,
                "name": tenant.name,
                "organisation_name": tenant.organisation_name,
                "tenant_type": tenant.tenant_type.value,
                "auth_policy": tenant.auth_policy.value,
                "confidence_threshold": tenant.confidence_threshold,
                "sla_hours": tenant.sla_hours
            }
            
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tenant")


@router.get("/")
async def list_tenants(
    current_user: UserProfile = Depends(get_current_user)
):
    """List all tenants (ADMIN role only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        async with app.state.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, organisation_name, tenant_type, auth_policy, confidence_threshold, sla_hours, created_at
                FROM tenants
                ORDER BY created_at DESC
                """
            )
            
            return {"tenants": [dict(row) for row in rows]}
            
    except Exception as e:
        logger.error(f"Failed to list tenants: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tenants")


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get tenant details by ID (ADMIN role only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        async with app.state.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, organisation_name, tenant_type, auth_policy, confidence_threshold, sla_hours, created_at
                FROM tenants
                WHERE id = $1
                """,
                tenant_id
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            return dict(row)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant")


@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    tenant: TenantUpdate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Update tenant details (ADMIN role only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        async with app.state.db_pool.acquire() as conn:
            # Build update query dynamically
            updates = []
            params = []
            param_idx = 2
            
            if tenant.name:
                updates.append(f"name = ${param_idx}")
                params.append(tenant.name)
                param_idx += 1
            
            if tenant.organisation_name:
                updates.append(f"organisation_name = ${param_idx}")
                params.append(tenant.organisation_name)
                param_idx += 1
            
            if tenant.auth_policy:
                updates.append(f"auth_policy = ${param_idx}")
                params.append(tenant.auth_policy.value)
                param_idx += 1
            
            if tenant.confidence_threshold is not None:
                updates.append(f"confidence_threshold = ${param_idx}")
                params.append(tenant.confidence_threshold)
                param_idx += 1
            
            if tenant.sla_hours is not None:
                updates.append(f"sla_hours = ${param_idx}")
                params.append(tenant.sla_hours)
                param_idx += 1
            
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            params.insert(0, tenant_id)
            
            await conn.execute(
                f"UPDATE tenants SET {', '.join(updates)} WHERE id = $1",
                *params
            )
            
            logger.info(f"Updated tenant {tenant_id} by admin {current_user.username}")
            
            return {"status": "success"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tenant")


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Delete a tenant (ADMIN role only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        async with app.state.db_pool.acquire() as conn:
            # Check if tenant has users
            user_count = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE tenant_id = $1",
                tenant_id
            )
            
            if user_count > 0:
                raise HTTPException(status_code=400, detail="Cannot delete tenant with active users")
            
            # Delete tenant
            await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_id)
            
            logger.info(f"Deleted tenant {tenant_id} by admin {current_user.username}")
            
            return {"status": "success"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tenant")
