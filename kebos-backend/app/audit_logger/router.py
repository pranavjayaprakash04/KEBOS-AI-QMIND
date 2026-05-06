"""
Audit Logger Router

Provides audit log export endpoint.
"""
from fastapi import APIRouter, Depends, Response, HTTPException
from datetime import date
import json
import csv
import io

from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/export")
async def export_audit_log(
    format: str = "json",
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Export audit log entries for the current tenant.

    Query param: format (json or csv, default json)
    Returns: JSON array of entries or CSV text with Content-Disposition header
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

        # Query audit entries for current tenant
        rows = await conn.fetch(
            """
            SELECT id, tenant_id, event_type, actor, resource, details, created_at
            FROM audit_entries
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            """,
            current_user.tenant_id,
        )

    # Convert rows to dicts
    entries = []
    for row in rows:
        entries.append({
            "id": str(row["id"]),
            "tenant_id": str(row["tenant_id"]),
            "event_type": row["event_type"],
            "actor": row["actor"],
            "resource": row["resource"],
            "details": row["details"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })

    filename = f"audit_log_{date.today().isoformat()}.{format}"

    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "tenant_id", "event_type", "actor", "resource", "details", "created_at"]
        )
        writer.writeheader()
        writer.writerows(entries)
        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    else:
        # Default: JSON
        return Response(
            content=json.dumps(entries, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
