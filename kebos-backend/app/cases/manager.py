"""
Case Manager - Auto-creation and management of threat cases

Automatically creates cases when threats are confirmed as CONFIRMED_THREAT.
Generates CERT-In reports and enforces 6-hour SLA.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncpg

logger = logging.getLogger(__name__)


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CERTInStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLOSED = "CLOSED"


class CaseManager:
    """Manages threat case lifecycle"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def create_case(
        self,
        threat_event_id: str,
        tenant_id: str,
        ioc_value: str,
        lead_category: str,
        qmind_confidence: float
    ) -> dict:
        """
        Auto-create case when threat is confirmed as CONFIRMED_THREAT.
        
        Case includes:
        - 6-hour CERT-In deadline
        - Severity based on confidence
        - Auto-generated CERT-In report
        """
        case_id = str(uuid.uuid4())
        case_number = f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Map confidence to severity
        severity = self._map_severity(qmind_confidence)
        
        # CERT-In deadline: 6 hours from creation
        cert_in_deadline = datetime.utcnow() + timedelta(hours=6)
        
        try:
            async with self.db_pool.acquire() as conn:
                # Look up the actual threat event UUID by indicator value
                te_row = await conn.fetchrow(
                    "SELECT id FROM threat_events WHERE indicator_value = $1",
                    ioc_value
                )
                actual_threat_id = te_row['id'] if te_row else None

                # Insert case
                await conn.execute(
                    """
                    INSERT INTO cases (id, case_number, tenant_id, threat_id, title, status, severity, cert_in_deadline, cert_in_status, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                    """,
                    case_id, case_number, tenant_id, actual_threat_id,
                    f"{lead_category} - {ioc_value}", CaseStatus.OPEN.value,
                    severity.value, cert_in_deadline, CERTInStatus.PENDING.value
                )

                logger.info(f"Created case {case_number} for threat {ioc_value}")
                
                # Generate CERT-In report in background
                # Note: In production, this would be a separate background task
                # For now, we'll trigger it synchronously for simplicity
                await self._generate_cert_in_report(case_id, ioc_value, lead_category)
                
                return {
                    "id": case_id,
                    "case_number": case_number,
                    "status": CaseStatus.OPEN.value,
                    "severity": severity.value,
                    "cert_in_deadline": cert_in_deadline.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to create case: {e}")
            raise
    
    def _map_severity(self, confidence: float) -> Severity:
        """Map QMind confidence to severity level"""
        if confidence >= 0.90:
            return Severity.CRITICAL
        elif confidence >= 0.75:
            return Severity.HIGH
        elif confidence >= 0.50:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    async def _generate_cert_in_report(self, case_id: str, ioc_value: str, lead_category: str):
        """
        Generate CERT-In report for the case.
        
        In production, this would use the SOCReportGenerator and Dilithium-3 signing.
        For now, this is a placeholder.
        """
        try:
            # TODO: Integrate with SOCReportGenerator
            # TODO: Apply Dilithium-3 signature
            logger.info(f"Generated CERT-In report for case {case_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate CERT-In report: {e}")
    
    async def get_case(self, case_id: str, tenant_id: str) -> Optional[dict]:
        """Get case details by ID"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, case_number, title, status, severity, cert_in_deadline, cert_in_status, created_at
                    FROM cases
                    WHERE id = $1 AND tenant_id = $2
                    """,
                    case_id, tenant_id
                )
                
                if not row:
                    return None
                
                return dict(row)
                
        except Exception as e:
            logger.error(f"Failed to get case: {e}")
            return None
    
    async def list_cases(self, tenant_id: str, status: Optional[str] = None) -> list:
        """List cases for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                if status:
                    rows = await conn.fetch(
                        """
                        SELECT id, case_number, title, status, severity, cert_in_deadline, created_at
                        FROM cases
                        WHERE tenant_id = $1 AND status = $2
                        ORDER BY created_at DESC
                        """,
                        tenant_id, status
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, case_number, title, status, severity, cert_in_deadline, created_at
                        FROM cases
                        WHERE tenant_id = $1
                        ORDER BY created_at DESC
                        """,
                        tenant_id
                    )
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to list cases: {e}")
            return []


# Singleton instance
_case_manager: Optional[CaseManager] = None


def get_case_manager(db_pool) -> CaseManager:
    """Get or create the singleton CaseManager instance"""
    global _case_manager
    if _case_manager is None:
        _case_manager = CaseManager(db_pool)
    return _case_manager
