from typing import Optional
import asyncio
from fastapi import HTTPException, Depends, Request
from .services import AuthService, UserProfile
from .session_risk import SessionRiskScorer
from app.config import settings
from app.ueba.baseline_engine import get_ueba_engine
import asyncpg


async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends()
) -> UserProfile:
    """Dependency to get current user from HttpOnly cookie with session risk scoring"""
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = await auth_service.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    tenant_id = payload["tenant_id"]

    # Check if session was invalidated by emergency rotation
    redis_client = auth_service.redis_client
    rotation_ts = await redis_client.get("session:rotation_timestamp")
    if rotation_ts:
        token_issued_at = payload.get("iat", 0)
        if token_issued_at < int(rotation_ts):
            raise HTTPException(
                status_code=401,
                detail="Session invalidated by emergency rotation. Please log in again."
            )
    
    # Set PostgreSQL session variable for tenant isolation (RLS)
    # Note: This sets the variable on a temporary connection for the request context
    # In production, this should be integrated with the connection pool middleware
    try:
        app = request.app
        if hasattr(app.state, 'db_pool'):
            async with app.state.db_pool.acquire() as conn:
                await conn.execute("SET LOCAL app.current_tenant = $1", tenant_id)
    except Exception as e:
        # Log but don't fail auth if session variable setting fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to set PostgreSQL session variable: {e}")
    
    # Update UEBA baseline (non-blocking)
    try:
        if hasattr(app.state, 'db_pool'):
            ueba_engine = get_ueba_engine(app.state.db_pool)
            # Don't await - let it run in background
            task = asyncio.create_task(ueba_engine.update_baseline(int(payload["sub"]), tenant_id, request))
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
    
    user_id = int(payload["sub"])
    
    # Run SessionRiskScorer on every authenticated request
    risk_scorer = SessionRiskScorer()
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
