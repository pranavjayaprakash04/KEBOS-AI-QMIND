"""
UEBA Router - User and Entity Behavior Analytics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile

router = APIRouter(prefix="/api/v1/ueba", tags=["ueba"])


@router.get("/baseline")
async def get_baseline(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get UEBA baselines for the current user's tenant.
    Returns list of baseline records with user behavior statistics.
    """
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")

    async with app.state.db_pool.acquire() as conn:
        # Set RLS tenant context
        await conn.execute(
            "SELECT set_config('app.current_tenant', $1, true)",
            str(current_user.tenant_id),
        )
        
        rows = await conn.fetch(
            """
            SELECT user_id, feature_name, mean, variance, sample_count, last_updated
            FROM ueba_baselines
            WHERE tenant_id = $1
            ORDER BY last_updated DESC
            """,
            current_user.tenant_id,
        )

    results = []
    for row in rows:
        results.append({
            "user_id": str(row["user_id"]),
            "feature_name": row["feature_name"],
            "mean": float(row["mean"]) if row["mean"] else 0.0,
            "variance": float(row["variance"]) if row["variance"] else 0.0,
            "sample_count": int(row["sample_count"]) if row["sample_count"] else 0,
            "last_updated": row["last_updated"].isoformat() if row["last_updated"] else None,
        })
    
    return results
