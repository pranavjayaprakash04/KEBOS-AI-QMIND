"""
CERT-In SLA Monitor for Kebos AI.
Phase 3.3 - Background task that monitors CERT-In 6-hour reporting window.
Alerts at 5-hour mark (NOT 6-hour).
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
import asyncpg

logger = logging.getLogger(__name__)


class CERTInSLAMonitor:
    """
    Monitors CERT-In reporting SLA compliance.
    CERT-In requires reporting within 6 hours of incident detection.
    This monitor alerts at 5-hour mark to give 1-hour buffer.
    """
    
    REPORTING_WINDOW_HOURS = 6
    ALERT_THRESHOLD_HOURS = 5  # Alert at 5 hours, not 6
    CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.running = False
    
    async def start(self):
        """Start the SLA monitor background task"""
        if self.running:
            logger.warning("CERT-In SLA monitor already running")
            return
        
        self.running = True
        logger.info("Starting CERT-In SLA monitor")
        
        # Start monitoring loop with done_callback
        task = asyncio.create_task(self._monitor_loop())
        task.add_done_callback(lambda t: logger.info("CERT-In SLA monitor task completed"))
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        try:
            while self.running:
                await self._check_sla_compliance()
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Error in CERT-In SLA monitor loop: {e}")
        finally:
            if self.running:
                await self.stop()
    
    async def _check_sla_compliance(self):
        """Check all open cases for SLA compliance"""
        try:
            async with self.db_pool.acquire() as conn:
                # Fetch all pending CERT-In cases
                open_cases = await conn.fetch("""
                    SELECT id, threat_id, created_at, five_hour_alert_sent,
                           cert_in_status, tenant_id
                    FROM cases
                    WHERE cert_in_status = 'PENDING'
                """)
                
                for case in open_cases:
                    await self._check_case_sla(conn, case)
                    
        except Exception as e:
            logger.error(f"Error checking SLA compliance: {e}")
    
    async def _check_case_sla(self, conn, case):
        """Check SLA for a single case"""
        case_id = case["id"]
        threat_id = case["threat_id"]
        created_at = case["created_at"]
        five_hour_alert_sent = case["five_hour_alert_sent"]
        tenant_id = case["tenant_id"]
        
        # Calculate elapsed time in hours
        elapsed = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
        
        # 5-hour alert (gives 1-hour buffer before 6-hour deadline)
        if elapsed >= self.ALERT_THRESHOLD_HOURS and not five_hour_alert_sent:
            await self._send_five_hour_alert(conn, case_id, threat_id, tenant_id)
            logger.warning(
                f"CERT-In 5-hour alert sent for case {case_id} "
                f"(deadline in {self.REPORTING_WINDOW_HOURS - elapsed:.1f} hours)"
            )
        
        # 6-hour breach (CRITICAL)
        if elapsed >= self.REPORTING_WINDOW_HOURS:
            await self._send_breach_alert(conn, case_id, threat_id, tenant_id)
            logger.error(
                f"CERT-In 6-hour reporting window BREACHED for case {case_id} "
                f"(elapsed: {elapsed:.1f} hours)"
            )
    
    async def _send_five_hour_alert(self, conn, case_id: int, threat_id: str, tenant_id: int):
        """
        Send 5-hour alert to analysts.
        CERT-In deadline in 1 hour - urgent action required.
        """
        # Update database to mark alert as sent
        await conn.execute("""
            UPDATE cases
            SET five_hour_alert_sent = true
            WHERE id = $1
        """, case_id)
        
        # TODO: Send actual notification (email, Slack, etc.)
        # For scaffold, log the alert
        logger.critical(
            f"CERT-IN DEADLINE ALERT: Case {case_id} has 1 hour remaining "
            f"before 6-hour reporting window. Threat ID: {threat_id}, Tenant: {tenant_id}"
        )
        
        # Insert alert record
        await conn.execute("""
            INSERT INTO alerts (case_id, alert_type, severity, message, created_at)
            VALUES ($1, 'CERT_IN_DEADLINE', 'CRITICAL', $2, NOW())
        """, case_id, f"CERT-In deadline in 1 hour for case {case_id}")
    
    async def _send_breach_alert(self, conn, case_id: int, threat_id: str, tenant_id: int):
        """
        Send breach alert - 6-hour window has been violated.
        This is a compliance violation.
        """
        # Update case status
        await conn.execute("""
            UPDATE cases
            SET cert_in_status = 'BREACHED'
            WHERE id = $1
        """, case_id)
        
        # TODO: Send critical notification to security team and compliance officers
        logger.critical(
            f"CERT-IN COMPLIANCE BREACH: Case {case_id} exceeded 6-hour reporting window. "
            f"Threat ID: {threat_id}, Tenant: {tenant_id}"
        )
        
        # Insert critical alert
        await conn.execute("""
            INSERT INTO alerts (case_id, alert_type, severity, message, created_at)
            VALUES ($1, 'CERT_IN_BREACH', 'CRITICAL', $2, NOW())
        """, case_id, f"CERT-In 6-hour reporting window BREACHED for case {case_id}")
    
    async def stop(self):
        """Stop the SLA monitor"""
        self.running = False
        logger.info("CERT-In SLA monitor stopped")


# Singleton instance
_monitor_instance: Optional[CERTInSLAMonitor] = None


def get_cert_in_sla_monitor(db_pool: asyncpg.Pool) -> CERTInSLAMonitor:
    """Get or create the singleton CERTInSLAMonitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = CERTInSLAMonitor(db_pool)
    return _monitor_instance
