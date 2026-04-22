"""
CEF Syslog Forwarder for Kebos AI SIEM Integration.
Phase 4.3 - Formats threat events as CEF and forwards to syslog.
"""
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class CEFSyslogForwarder:
    """
    Forwards QMind threat events as CEF to any SIEM (Sentinel, QRadar, ArcSight, Elastic).
    CEF format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
    """
    
    VENDOR = "Pynevera"
    PRODUCT = "KebosAI"
    VERSION = "1.0"
    
    # CEF Severity mapping (0-10) for QMind status values
    SEVERITY_MAP = {
        "CONFIRMED_THREAT": 10,
        "ELEVATED": 7,
        "MONITORING": 5,
        "BENIGN": 1
    }
    
    def format_event(self, threat_event: Dict[str, Any]) -> str:
        """
        Format threat event as CEF string.
        
        Args:
            threat_event: Threat event data
        
        Returns:
            CEF-formatted string
        """
        # Extract fields matching prompt spec
        lead_category = threat_event.get("lead_category", "Unknown")
        status = threat_event.get("status", "")
        severity_num = self.SEVERITY_MAP.get(status, 5)
        source_ip = threat_event.get("source_ip", "0.0.0.0")
        indicator_value = threat_event.get("indicator_value", "")
        confidence = threat_event.get("confidence", 0)
        mitre_techniques = threat_event.get("mitre_techniques", "")
        
        # CEF Header
        signature_id = f"QMind-{lead_category}"
        name = f"{lead_category} detected"
        
        # CEF Extension
        extension = (
            f"src={source_ip} "
            f"dst={indicator_value} "
            f"confidence={confidence:.3f} "
            f"cat={lead_category} "
            f"cs1={mitre_techniques} "
            f"cs1Label=MITRETechniques"
        )
        
        # Full CEF message
        cef_message = f"CEF:0|{self.VENDOR}|{self.PRODUCT}|{self.VERSION}|{signature_id}|{name}|{severity_num}|{extension}"
        
        return cef_message
    
    async def forward(self, threat_event: Dict[str, Any]) -> bool:
        """
        Forward CEF-formatted event to syslog.
        
        Args:
            threat_event: Threat event to forward
        
        Returns:
            True if forwarded successfully
        """
        cef_line = self.format_event(threat_event)
        
        # Uses TLSSyslogHandler already configured
        from app.audit_logger.syslog_handler import get_tls_syslog_handler
        tls_syslog_handler = get_tls_syslog_handler()
        if tls_syslog_handler:
            tls_syslog_handler.emit_raw(cef_line)
        else:
            logger.info(f"CEF (no syslog configured): {cef_line}")
        
        return True


# Singleton instance
_cef_forwarder_instance: Optional[CEFSyslogForwarder] = None


def get_cef_forwarder() -> CEFSyslogForwarder:
    """Get or create the singleton CEFSyslogForwarder instance"""
    global _cef_forwarder_instance
    if _cef_forwarder_instance is None:
        _cef_forwarder_instance = CEFSyslogForwarder()
    return _cef_forwarder_instance
