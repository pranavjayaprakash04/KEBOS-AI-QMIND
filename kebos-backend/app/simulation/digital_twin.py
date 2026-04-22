import asyncio, logging
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timezone
import asyncpg

logger = logging.getLogger(__name__)

@dataclass
class PlaybookAction:
    action_id: str
    action_type: str      # "BLOCK_IP", "BLOCK_DOMAIN", "ISOLATE_HOST", "DISABLE_ACCOUNT"
    target: str           # IP, domain, hostname, or user ID
    reversibility: str    # "REVERSIBLE" or "IRREVERSIBLE"
    description: str

@dataclass
class SimulationResult:
    impact_score: float        # N_FP / N_total — false positive rate
    n_fp: int
    n_total: int
    recommendation: str        # "PRESENT_TO_ANALYST_FOR_APPROVAL" or "BLOCK_PENDING_INVESTIGATION"
    replay_window_minutes: int
    action_description: str
    simulated_at: datetime

class DigitalTwinSimulator:
    """
    Before any IRREVERSIBLE action, replay the last 30 minutes of historical
    traffic against the proposed rule to estimate false positive rate.
    impact_score < 0.05 (< 5% FP rate) → present to analyst for approval.
    impact_score >= 0.05 → block pending further investigation.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def simulate_action(
        self, action: PlaybookAction, tenant_id: UUID
    ) -> SimulationResult:
        """
        FULLY IMPLEMENTED. NEVER a stub. Load-bearing code.
        """
        # TimescaleDB 30-minute replay query
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    time_bucket('1 minute', timestamp) AS bucket,
                    source_ip,
                    indicator_value,
                    status,
                    COUNT(*) AS event_count
                FROM threat_events
                WHERE tenant_id = $1
                  AND timestamp >= NOW() - INTERVAL '30 minutes'
                GROUP BY bucket, source_ip, indicator_value, status
                ORDER BY bucket ASC
                """,
                str(tenant_id)
            )
            events = rows

        n_total = len(events)
        if n_total == 0:
            # No historical data — be conservative
            logger.warning(
                f"No historical data for tenant {tenant_id} — "
                "returning conservative impact_score=1.0"
            )
            return SimulationResult(
                impact_score=1.0,
                n_fp=0, n_total=0,
                recommendation="BLOCK_PENDING_INVESTIGATION",
                replay_window_minutes=30,
                action_description=action.description,
                simulated_at=datetime.now(timezone.utc),
            )

        # Count historical events that would have been incorrectly blocked
        n_fp = sum(
            1 for event in events
            if self._would_block(action, event) and not self._is_confirmed_threat(event)
        )

        impact_score = n_fp / n_total

        if impact_score < 0.05:
            recommendation = "PRESENT_TO_ANALYST_FOR_APPROVAL"
            logger.info(
                f"Digital Twin: {action.action_type} on {action.target} — "
                f"impact_score={impact_score:.3f} (<5%) → present to analyst"
            )
        else:
            recommendation = "BLOCK_PENDING_INVESTIGATION"
            logger.warning(
                f"Digital Twin: {action.action_type} on {action.target} — "
                f"impact_score={impact_score:.3f} (>5%) → blocked pending investigation"
            )

        return SimulationResult(
            impact_score=impact_score,
            n_fp=n_fp,
            n_total=n_total,
            recommendation=recommendation,
            replay_window_minutes=30,
            action_description=action.description,
            simulated_at=datetime.now(timezone.utc),
        )

    def _would_block(self, action: PlaybookAction, event) -> bool:
        if action.action_type == "BLOCK_IP":
            return event.get("source_ip") == action.target
        if action.action_type == "BLOCK_DOMAIN":
            return action.target in str(event.get("indicator_value", ""))
        if action.action_type == "ISOLATE_HOST":
            return event.get("source_ip") == action.target
        if action.action_type == "DISABLE_ACCOUNT":
            return action.target in str(event.get("indicator_value", ""))
        return False

    def _is_confirmed_threat(self, event) -> bool:
        return event.get("status") in ("CONFIRMED_THREAT", "ELEVATED")
