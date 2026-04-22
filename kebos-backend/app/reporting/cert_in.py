"""
CERT-In Report Generator for Kebos AI.
Phase 3.2 - Generates CERT-In compliant reports with Dilithium-3 signatures.
"""
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone as dt_timezone
from dataclasses import dataclass
from enum import Enum
import asyncpg
from app.config import settings

logger = logging.getLogger(__name__)


class CERTInStatus(Enum):
    """CERT-In report status"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLOSED = "CLOSED"


@dataclass
class CERTInReport:
    """CERT-In compliant report structure"""
    report_id: str
    incident_id: str
    incident_type: str
    severity: str
    affected_assets: List[str]
    timeline: Dict[str, datetime]
    iocs: List[Dict[str, Any]]
    mitigation_steps: List[str]
    signature: Optional[str] = None
    pubkey_ref: Optional[str] = None
    report_hash: Optional[str] = None
    created_at: datetime = None
    
    def to_canonical_json(self) -> str:
        """Convert to canonical JSON for signing"""
        import json
        # Sort keys for canonical representation
        data = {
            "report_id": self.report_id,
            "incident_id": self.incident_id,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "affected_assets": sorted(self.affected_assets),
            "timeline": {k: v.isoformat() for k, v in sorted(self.timeline.items())},
            "iocs": sorted(self.iocs, key=lambda x: str(x)),
            "mitigation_steps": sorted(self.mitigation_steps),
        }
        return json.dumps(data, sort_keys=True)


class DilithiumSigner:
    """
    Dilithium-3 signature provider using Vault.
    Phase 3.2 - Post-quantum signatures for audit trails.
    """
    
    def __init__(self):
        self.vault_addr = settings.VAULT_ADDR
        self.vault_token = settings.VAULT_TOKEN
        self.key_name = "dilithium3-cert-in-key"
    
    async def sign(self, private_key_ref: str, data: bytes) -> str:
        """
        Sign data using Dilithium-3 via Vault.
        
        Args:
            private_key_ref: Reference to private key in Vault
            data: Data to sign
        
        Returns:
            Base64-encoded signature
        """
        # TODO: Implement actual Vault Dilithium signing
        # For now, return a mock signature (will be implemented with proper Vault PQC plugin)
        import base64
        mock_sig = hashlib.sha256(data + b"dilithium3-mock").digest()
        return base64.b64encode(mock_sig).decode('utf-8')


class CERTInReportGenerator:
    """
    CERT-In Report Generator with Dilithium-3 signatures.
    Generates compliant reports for Indian CERT regulatory requirements.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.signer = DilithiumSigner()
    
    async def generate(
        self,
        threat_event: Dict[str, Any],
        soc_report: Optional[Dict[str, Any]] = None
    ) -> CERTInReport:
        """
        Generate CERT-In compliant report.
        
        Args:
            threat_event: Threat event data
            soc_report: Optional SOC report data
        
        Returns:
            CERTInReport with Dilithium-3 signature
        """
        report_id = f"CERT-IN-{datetime.now(dt_timezone.utc).strftime('%Y%m%d%H%M%S')}"
        incident_id = threat_event.get("id", "unknown")
        
        # Try to generate sections from SOC report, fallback to Jinja2
        try:
            if soc_report:
                sections = await self._generate_from_soc_report(soc_report)
            else:
                sections = await self._jinja2_fallback(threat_event)
        except Exception as e:
            logger.error(f"SOC report generation failed, using fallback: {e}")
            sections = await self._jinja2_fallback(threat_event)
        
        # Build report
        report = CERTInReport(
            report_id=report_id,
            incident_id=incident_id,
            incident_type=threat_event.get("threat_type", "unknown"),
            severity=threat_event.get("severity", "medium"),
            affected_assets=sections.get("affected_assets", []),
            timeline=sections.get("timeline", {}),
            iocs=sections.get("iocs", []),
            mitigation_steps=sections.get("mitigation_steps", []),
            created_at=datetime.now(dt_timezone.utc)
        )
        
        # Generate report hash
        report.report_hash = hashlib.sha256(
            report.to_canonical_json().encode()
        ).hexdigest()
        
        # Sign with Dilithium-3
        report.signature = await self.signer.sign(
            f"vault:{self.signer.key_name}",
            report.report_hash.encode()
        )
        report.pubkey_ref = "vault:dilithium3-cert-in-key"
        
        # Store in database
        await self._store_report(report)
        
        logger.info(f"Generated CERT-In report {report_id} for incident {incident_id}")
        return report
    
    async def _generate_from_soc_report(self, soc_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report sections from SOC report data"""
        return {
            "affected_assets": soc_report.get("affected_assets", []),
            "timeline": soc_report.get("timeline", {}),
            "iocs": soc_report.get("iocs", []),
            "mitigation_steps": soc_report.get("mitigation_steps", []),
        }
    
    async def _jinja2_fallback(self, threat_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Jinja2 fallback for report generation - ALWAYS works.
        Used when SOC report generation fails.
        """
        # Generate basic report structure from threat event
        return {
            "affected_assets": [
                threat_event.get("source_ip", "unknown"),
                threat_event.get("destination_ip", "unknown"),
            ],
            "timeline": {
                "detected": threat_event.get("created_at", datetime.now(dt_timezone.utc)),
                "reported": datetime.now(dt_timezone.utc),
            },
            "iocs": [
                {
                    "type": "ip",
                    "value": threat_event.get("source_ip", ""),
                }
            ],
            "mitigation_steps": [
                "Block source IP at perimeter",
                "Isolate affected systems",
                "Conduct forensic analysis",
                "Update detection rules",
            ],
        }
    
    async def _store_report(self, report: CERTInReport):
        """Store CERT-In report in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cert_in_reports (
                    report_id, incident_id, incident_type, severity,
                    affected_assets, timeline, iocs, mitigation_steps,
                    signature, pubkey_ref, report_hash, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
                report.report_id,
                report.incident_id,
                report.incident_type,
                report.severity,
                report.affected_assets,
                report.timeline,
                report.iocs,
                report.mitigation_steps,
                report.signature,
                report.pubkey_ref,
                report.report_hash,
                report.created_at
            )
    
    def export_pdf(self, report: CERTInReport) -> bytes:
        """
        Export CERT-In report as PDF using ReportLab.
        
        Args:
            report: CERTInReport to export
        
        Returns:
            PDF bytes
        """
        # TODO: Implement ReportLab PDF generation
        # For scaffold, return placeholder
        logger.warning("PDF export not yet implemented - returning placeholder")
        return b"PDF placeholder - ReportLab integration pending"


# Singleton instance
_generator_instance: Optional[CERTInReportGenerator] = None


def get_cert_in_generator(db_pool: asyncpg.Pool) -> CERTInReportGenerator:
    """Get or create the singleton CERTInReportGenerator instance"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = CERTInReportGenerator(db_pool)
    return _generator_instance
