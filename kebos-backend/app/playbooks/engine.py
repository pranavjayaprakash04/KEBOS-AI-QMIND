"""
Playbook Engine - Automated response actions

Executes reversible actions immediately.
Requires analyst approval for irreversible actions after Digital Twin simulation.
"""
import logging
from typing import Optional, Dict, Any
from enum import Enum
from uuid import UUID
import asyncpg
from app.simulation.digital_twin import DigitalTwinSimulator, PlaybookAction

logger = logging.getLogger(__name__)


class Reversibility(str, Enum):
    REVERSIBLE = "REVERSIBLE"
    IRREVERSIBLE = "IRREVERSIBLE"


class PlaybookEngine:
    """
    Executes automated response actions based on playbook rules.

    For REVERSIBLE actions: executes immediately
    For IRREVERSIBLE actions: requires Digital Twin simulation and analyst approval
    """

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.digital_twin = DigitalTwinSimulator(db_pool)
    
    async def execute_action(
        self,
        action: Dict[str, Any],
        threat_event_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Execute an action based on its reversibility.
        
        REVERSIBLE: Execute immediately, notify analyst
        IRREVERSIBLE: Simulate with Digital Twin, request approval if impact >= 0.05
        """
        reversibility = action.get("reversibility", "REVERSIBLE")
        
        if reversibility == Reversibility.REVERSIBLE:
            return await self._execute(action, threat_event_id, tenant_id)
        else:
            return await self._handle_irreversible(action, threat_event_id, tenant_id)
    
    async def _execute(
        self,
        action: Dict[str, Any],
        threat_event_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Execute a reversible action immediately.
        """
        try:
            # TODO: Implement actual action execution
            # For now, this is a placeholder
            logger.info(f"Executing reversible action: {action.get('type')}")
            
            # Notify analyst
            await self._notify_analyst(action, threat_event_id, auto_executed=True)
            
            return {
                "status": "executed",
                "action_type": action.get("type"),
                "auto_executed": True
            }
            
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            raise
    
    async def _handle_irreversible(
        self,
        action: Dict[str, Any],
        threat_event_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Handle irreversible action with Digital Twin simulation.
        
        1. Run Digital Twin simulation
        2. If impact_score >= 0.05: block pending investigation
        3. If impact_score < 0.05: request analyst approval
        """
        try:
            # Run Digital Twin simulation
            sim = await self._digital_twin_simulate(action, tenant_id)
            
            if sim["impact_score"] >= 0.05:
                # High impact - block pending investigation
                await self._block_pending_investigation(action, sim)
                return {
                    "status": "blocked",
                    "reason": "High impact detected",
                    "simulation": sim
                }
            else:
                # Low impact - request analyst approval
                await self._request_analyst_approval(action, sim, threat_event_id)
                return {
                    "status": "pending_approval",
                    "simulation": sim
                }
                
        except Exception as e:
            logger.error(f"Failed to handle irreversible action: {e}")
            raise
    
    async def _digital_twin_simulate(
        self,
        action: Dict[str, Any],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Simulate action impact using Digital Twin.
        NEVER a stub - calls actual DigitalTwinSimulator for IRREVERSIBLE actions.
        """
        playbook_action = PlaybookAction(
            action_id=action.get("id", str(uuid.uuid4())),
            action_type=action.get("type"),
            target=action.get("target"),
            reversibility=action.get("reversibility", "REVERSIBLE"),
            description=action.get("description", "")
        )

        sim_result = await self.digital_twin.simulate_action(
            playbook_action,
            UUID(tenant_id)
        )

        return {
            "impact_score": sim_result.impact_score,
            "n_fp": sim_result.n_fp,
            "n_total": sim_result.n_total,
            "recommendation": sim_result.recommendation,
            "replay_window_minutes": sim_result.replay_window_minutes,
            "action_description": sim_result.action_description,
            "simulated_at": sim_result.simulated_at.isoformat()
        }
    
    async def _block_pending_investigation(self, action: Dict[str, Any], sim: Dict[str, Any]):
        """
        Block action pending further investigation due to high impact.
        """
        logger.warning(f"Action blocked pending investigation: {action.get('type')}")
        # TODO: Create pending action record in database
    
    async def _request_analyst_approval(
        self,
        action: Dict[str, Any],
        sim: Dict[str, Any],
        threat_event_id: str
    ):
        """
        Request analyst approval for low-impact irreversible action.
        """
        logger.info(f"Requesting analyst approval for action: {action.get('type')}")
        # TODO: Create pending action record in database
        # TODO: Send notification to analyst
    
    async def _notify_analyst(
        self,
        action: Dict[str, Any],
        threat_event_id: str,
        auto_executed: bool = False
    ):
        """
        Notify analyst of action execution.
        """
        logger.info(f"Notifying analyst of action: {action.get('type')}")
        # TODO: Send notification (WebSocket, email, etc.)


# Singleton instance
_playbook_engine: Optional[PlaybookEngine] = None


def get_playbook_engine(db_pool) -> PlaybookEngine:
    """Get or create the singleton PlaybookEngine instance"""
    global _playbook_engine
    if _playbook_engine is None:
        _playbook_engine = PlaybookEngine(db_pool)
    return _playbook_engine
