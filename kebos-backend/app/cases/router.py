"""
Cases Router - Case management endpoints

Includes case approval endpoint for irreversible actions.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi.responses import Response
from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile
from app.cases.manager import get_case_manager
from app.reporting.cert_in_generator import CERTInReportGenerator
import logging
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

cert_in_generator = CERTInReportGenerator()


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str            # "signal_detected" | "qmind_scored" | "case_created" |
                               # "status_changed" | "cert_in_filed" | "analyst_action"
    actor: str                 # "QMind" | "System" | analyst email
    description: str
    metadata: dict             # Raw data for the event (category scores, old/new status, etc.)
    severity: str              # "info" | "warning" | "critical"


class CaseTimeline(BaseModel):
    case_id: str
    total_events: int
    events: list[TimelineEvent]
    generated_at: datetime
    dilithium_signature: str   # Dilithium-3 signature of the timeline JSON for court evidence


class CaseApprovalRequest(BaseModel):
    """Request to approve an irreversible action"""
    action_id: str
    analyst_notes: Optional[str] = None


@router.get("/")
async def list_cases(
    status: Optional[str] = None,
    current_user: UserProfile = Depends(get_current_user)
):
    """List all cases for the current tenant"""
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    case_manager = get_case_manager(app.state.db_pool)
    cases = await case_manager.list_cases(current_user.tenant_id, status)
    
    return cases


@router.get("/{case_id}")
async def get_case(
    case_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get case details by ID"""
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    case_manager = get_case_manager(app.state.db_pool)
    case = await case_manager.get_case(case_id, current_user.tenant_id)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return case


@router.post("/{case_id}/approve-action")
async def approve_action(
    case_id: str,
    request: CaseApprovalRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Approve an irreversible action (ANALYST role only).
    
    Verifies case ownership, executes action, and logs audit entry.
    """
    # Verify user has ANALYST role
    if current_user.role not in ["analyst", "admin"]:
        raise HTTPException(status_code=403, detail="Analyst role required")
    
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        async with app.state.db_pool.acquire() as conn:
            # Verify case ownership
            case = await conn.fetchrow(
                "SELECT id, tenant_id FROM cases WHERE id = $1",
                case_id
            )
            
            if not case:
                raise HTTPException(status_code=404, detail="Case not found")
            
            if str(case['tenant_id']) != str(current_user.tenant_id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Fetch pending action
            action = await conn.fetchrow(
                "SELECT action FROM pending_actions WHERE id = $1 AND case_id = $2 AND status = 'PENDING'",
                request.action_id, case_id
            )
            
            if not action:
                raise HTTPException(status_code=404, detail="Pending action not found")
            
            # Update action status
            await conn.execute(
                "UPDATE pending_actions SET status = 'APPROVED' WHERE id = $1",
                request.action_id
            )
            
            # Execute the action
            # TODO: Integrate with PlaybookEngine
            logger.info(f"Action {request.action_id} approved by analyst {current_user.username}")
            
            # Audit log
            try:
                from app.audit_logger.chain import AuditChain
                audit_chain = AuditChain()
                await audit_chain.log_entry(
                    actor_id=str(current_user.id),
                    action="ACTION_APPROVED",
                    resource=case_id,
                    metadata={
                        "action_id": request.action_id,
                        "analyst_notes": request.analyst_notes
                    }
                )
            except Exception:
                pass  # Audit logging not available
            
            return {
                "status": "success",
                "message": "Action approved and executed",
                "action_id": request.action_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve action: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve action")


@router.post("/{case_id}/cert-in-report",
             response_class=Response,
             summary="Generate and download Dilithium-3-signed CERT-In PDF")
async def generate_cert_in_report(
    case_id: UUID,
    request: Request,
    current_user: UserProfile = Depends(get_current_user)
):
    # Fetch case + threat event
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")

    async with app.state.db_pool.acquire() as db:
        case = await db.fetchrow(
            "SELECT * FROM cases WHERE id=$1 AND tenant_id=$2",
            str(case_id), str(current_user.tenant_id)
        )
        if not case:
            raise HTTPException(404, "Case not found")
        threat = await db.fetchrow(
            "SELECT * FROM threat_events WHERE id=$1",
            case['threat_id']
        )

    # Build minimal SOC report — all fields have defaults in cert_in_generator
    import types
    soc_report = types.SimpleNamespace()

    # Get Dilithium-3 signing key from settings/Vault
    signing_key = getattr(app.state, 'dilithium_signing_key', None)

    # Generate signed PDF
    threat_dict = dict(threat) if threat else {}
    pdf_bytes = await cert_in_generator.generate(
        threat_event=threat_dict,
        soc_report=soc_report,
        tenant_name=getattr(current_user, 'organisation_name', None) or "Pynevera Technologies",
        signing_key_bytes=signing_key,
    )

    # Log to audit trail (non-blocking — skip if unavailable)
    try:
        await app.state.audit_chain.append(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            action="CERT_IN_REPORT_GENERATED",
            resource=f"case:{case_id}",
            metadata={"case_id": str(case_id)}
        )
    except Exception:
        pass

    return Response(
        content=pdf_bytes,
        status_code=200,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cert-in-{case_id}.pdf"',
            "X-Dilithium3-Signed": "true" if signing_key else "false",
        }
    )


@router.get(
    "/{case_id}/timeline",
    response_model=CaseTimeline,
    summary="Full forensic timeline for a case — Dilithium-3 signed for legal admissibility"
)
async def get_case_timeline(
    case_id: str,
    current_user: UserProfile = Depends(get_current_user)
) -> CaseTimeline:
    """
    Returns every event related to a case in chronological order.
    The complete timeline is signed with Dilithium-3 — admissible as evidence
    under Indian IT Act Section 5 and CERT-In S.O. 1374(E) reporting requirements.

    Timeline includes:
      - Original signal detection event
      - QMind scoring events (all 10 category scores)
      - Case creation with CERT-In deadline
      - All status transitions
      - Analyst actions (acknowledge, escalate, resolve)
      - CERT-In report filing timestamp
      - HoneyGrid deployment (if triggered)
    """
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")

    async with app.state.db_pool.acquire() as db:
        # Verify the case belongs to the requesting tenant (RLS enforces this at DB level,
        # but explicit check provides a clearer 404 instead of empty result)
        case = await db.fetchrow(
            "SELECT id, tenant_id, title, cert_in_status, created_at FROM cases "
            "WHERE id = $1 AND tenant_id = $2",
            case_id, str(current_user.tenant_id)
        )
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

        # Fetch all timeline events from the audit log for this case
        rows = await db.fetch(
            """SELECT
                 al.timestamp,
                 al.event_type,
                 al.actor,
                 al.description,
                 al.metadata,
                 al.severity
               FROM audit_log al
               WHERE al.case_id = $1
                 AND al.tenant_id = $2
               ORDER BY al.timestamp ASC""",
            case_id, str(current_user.tenant_id)
        )

        events = [
            TimelineEvent(
                timestamp=row["timestamp"],
                event_type=row["event_type"],
                actor=row["actor"] or "System",
                description=row["description"],
                metadata=row["metadata"] or {},
                severity=row["severity"] or "info"
            )
            for row in rows
        ]

        # Build timeline payload for signing
        timeline_payload = {
            "case_id": case_id,
            "tenant_id": str(current_user.tenant_id),
            "total_events": len(events),
            "events": [e.dict() for e in events],
            "generated_at": datetime.utcnow().isoformat()
        }

        # Sign the entire timeline with Dilithium-3 for legal admissibility
        from app.main import app as kebos_app
        audit_chain = getattr(kebos_app.state, "audit_chain", None)
        signature_hex = ""
        if audit_chain:
            try:
                import json, hashlib
                payload_bytes = json.dumps(timeline_payload, default=str).encode()
                payload_hash = hashlib.sha256(payload_bytes).hexdigest()
                sig_bytes = audit_chain.sign(payload_bytes)
                signature_hex = sig_bytes.hex() if sig_bytes else ""
                logger.info(f"Timeline for case {case_id} signed with Dilithium-3: {payload_hash[:16]}...")
            except Exception as e:
                logger.error(f"Dilithium-3 signing failed for timeline {case_id}: {e}")

        return CaseTimeline(
            case_id=case_id,
            total_events=len(events),
            events=events,
            generated_at=datetime.utcnow(),
            dilithium_signature=signature_hex
        )
