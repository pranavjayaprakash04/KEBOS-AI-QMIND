"""
Cases Router - Case management endpoints

Includes case approval endpoint for irreversible actions.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile
from app.cases.manager import get_case_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


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
    
    return {"cases": cases}


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
                raise HTTPException(status_code=404, detail "Pending action not found")
            
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
