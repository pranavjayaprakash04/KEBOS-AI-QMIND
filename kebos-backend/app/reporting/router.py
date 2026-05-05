"""
Reporting Router for Kebos AI.
Phase 3.2 - CERT-In report generation with Dilithium-3 signatures.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from uuid import UUID
from typing import Optional
from app.auth.dependencies import get_current_user
from app.reporting.cert_in_generator import CERTInReportGenerator
from app.reporting.soc_generator import SOCReportGenerator
from app.cases.manager import get_case_manager
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/", summary="List generated CERT-In reports")
async def list_reports(
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
):
    """Return all CERT-In reports ordered by creation date descending."""
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")

    async with app.state.db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT report_id, incident_id, incident_type, severity,
                   pubkey_ref, report_hash, created_at
            FROM cert_in_reports
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )

    return [
        {
            "report_id": row["report_id"],
            "incident_id": str(row["incident_id"]),
            "incident_type": row["incident_type"],
            "severity": row["severity"],
            "pubkey_ref": row["pubkey_ref"],
            "report_hash": row["report_hash"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]


@router.post("/cert-in")
async def generate_cert_in(
    case_id: UUID,
    current_user = Depends(get_current_user)
):
    """
    Generate CERT-In compliant PDF report for a case.
    
    Returns PDF with Dilithium-3 signature.
    """
    try:
        # Get case manager
        case_manager = get_case_manager()
        
        # Fetch case and threat event
        case = await case_manager.get_case(case_id)
        if not case:
            return Response("Case not found", status_code=404)
        
        threat_event = case.get("threat_event", {})
        
        # Generate SOC report
        soc_generator = SOCReportGenerator()
        soc_report = await soc_generator.generate_incident_report(
            threat_data=threat_event,
            classification=case.get("classification", "INTERNAL"),
            tenant_type=case.get("tenant_type", "commercial")
        )
        
        # Generate CERT-In PDF
        cert_in_generator = CERTInReportGenerator()
        
        # Get signing key (for now, use placeholder - will be loaded from Vault in production)
        signing_key_bytes = b"placeholder_key"
        
        tenant_name = case.get("tenant_name", "Unknown Organisation")
        
        pdf_bytes = await cert_in_generator.generate(
            threat_event=threat_event,
            soc_report=soc_report,
            signing_key_bytes=signing_key_bytes,
            tenant_name=tenant_name
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=cert-in-{case_id}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate CERT-In report: {e}")
        return Response(f"Report generation failed: {str(e)}", status_code=500)
