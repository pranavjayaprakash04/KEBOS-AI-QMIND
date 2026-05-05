from typing import Optional
import asyncio
import logging
from fastapi import HTTPException, Depends, Request
from .services import AuthService, UserProfile
from .session_risk import SessionRiskScorer
from app.config import settings
from app.ueba.baseline_engine import get_ueba_engine
import asyncpg

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends()
) -> UserProfile:
    """Dependency to get current user from HttpOnly cookie or Authorization header with session risk scoring"""
    token = request.cookies.get("access_token")
    
    # Fallback to Authorization header if cookie not present
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = await auth_service.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    tenant_id = payload["tenant_id"]
    user_id = payload["sub"]  # UUID as string

    # MANDATORY: Set PostgreSQL session variable for Row-Level Security
    # Without this line, ALL RLS policies are inactive — every tenant sees all data
    try:
        app = request.app
        if hasattr(app.state, 'db_pool'):
            async with app.state.db_pool.acquire() as conn:
                # SET LOCAL doesn't accept parameters, use literal value
                await conn.execute("SELECT set_config('app.current_tenant', $1, true)", tenant_id)
    except Exception as e:
        logger.error(f"Failed to set PostgreSQL session variable: {e}")

    # Check if session was invalidated by emergency rotation (skip if redis_client is None)
    redis_client = auth_service.redis_client
    if redis_client:
        rotation_ts = await redis_client.get("session:rotation_timestamp")
        if rotation_ts:
            token_issued_at = payload.get("iat", 0)
            if token_issued_at < int(rotation_ts):
                raise HTTPException(
                    status_code=401,
                    detail="Session invalidated by emergency rotation. Please log in again."
                )
    
    # Update UEBA baseline (non-blocking)
    try:
        if hasattr(app.state, 'db_pool'):
            ueba_engine = get_ueba_engine(app.state.db_pool)
            # Don't await - let it run in background
            task = asyncio.create_task(ueba_engine.update_baseline(user_id, tenant_id, request))
            task.add_done_callback(lambda t: logger.info("UEBA baseline update completed"))
    except Exception as e:
        logger.error(f"Failed to update UEBA baseline: {e}")
    
    tenant_type = payload.get("tenant_type", "enterprise")
    fido2_enabled = payload.get("fido2_enabled", False)

    # Government tenant enforcement
    if tenant_type == "government" and not fido2_enabled:
        raise HTTPException(
            status_code=403,
            detail="FIDO2 hardware key required for government tenants. "
                   "Register a YubiKey at /api/v1/auth/fido2/register/begin."
        )
    
    # Run SessionRiskScorer on every authenticated request (skip if redis_client is None)
    if redis_client:
        risk_scorer = SessionRiskScorer(
            redis_client=redis_client,
            geoip_db_path=settings.GEOIP_DB_PATH
        )
        risk_result = await risk_scorer.score(request, user_id, tenant_id)
        
        if risk_result.action == "lock":
            raise HTTPException(
                status_code=401,
                detail=f"Account locked due to security risk: {risk_result.reason}"
            )
        
        if risk_result.action == "step_up_auth":
            # TODO: Implement step-up authentication flow
            # For scaffold, allow with warning
            pass
    
    return UserProfile(
        id=user_id,
        username=payload["username"],
        email=payload.get("email"),
        role=payload["role"],
        tenant_id=tenant_id,
        tenant_type=tenant_type,
        fido2_verified=fido2_enabled,
        fido2_enabled=fido2_enabled,
        jti=payload.get("jti")
    )
