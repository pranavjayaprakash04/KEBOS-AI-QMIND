import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    "CONFIRMED_THREAT": 10, "ELEVATED": 7, "MONITORING": 4, "BENIGN": 1
}
CATEGORY_DEVICE_EVENT = {
    "Phishing": "Phishing Domain Detected",
    "Malware": "Malware Indicator Detected",
    "C2_Infrastructure": "C2 Infrastructure Detected",
    "Botnet_IP": "Botnet IP Detected",
    "Credential_Leak": "Credential Leak Detected",
    "Supply_Chain": "Supply Chain Compromise Detected",
    "Insider_Threat": "Insider Threat Signal Detected",
    "DDoS": "DDoS Activity Detected",
    "CVE_Exploitation": "CVE Exploitation Detected",
    "Benign": "Benign Indicator",
}

class CEFSyslogForwarder:
    """
    Converts QMind threat events to Common Event Format (CEF) and forwards
    via TLS syslog to any SIEM (Sentinel, QRadar, ArcSight, LogRhythm, Elastic).
    All major SIEMs speak CEF natively — zero configuration on their side.
    """
    def format_event(self, threat_event: dict) -> str:
        lead = threat_event.get("lead_category", "Unknown")
        status = threat_event.get("status", "MONITORING")
        sev = SEVERITY_MAP.get(status, 5)
        event_name = CATEGORY_DEVICE_EVENT.get(lead, f"{lead} Detected")
        return (
            f"CEF:0|Pynevera Technologies|KebosAI|1.0"
            f"|QMind-{lead}|{event_name}|{sev}"
            f"|src={threat_event.get('source_ip','0.0.0.0')}"
            f" dst={threat_event.get('indicator_value','')}"
            f" confidence={float(threat_event.get('confidence', 0)):.4f}"
            f" cs1={','.join(threat_event.get('mitre_techniques', []))}"
            f" cs1Label=MITRETechniques"
            f" cs2={threat_event.get('tenant_id','')}"
            f" cs2Label=TenantID"
            f" cs3={threat_event.get('source','unknown')}"
            f" cs3Label=DetectionSource"
            f" msg={event_name} via Kebos AI QMind probabilistic engine"
        )

    async def forward(self, threat_event: dict):
        """Forward as CEF to configured TLS syslog target."""
        from app.audit_logger.tls_syslog_handler import app_tls_handler
        if app_tls_handler is None:
            logger.debug("CEF forward skipped — TLS syslog not configured (SYSLOG_HOST empty)")
            return
        try:
            cef_line = self.format_event(threat_event)
            record = logging.LogRecord(
                name="kebos.cef", level=logging.WARNING,
                pathname="", lineno=0, msg=cef_line, args=(), exc_info=None
            )
            app_tls_handler.emit(record)
        except Exception as e:
            logger.error(f"CEF syslog forward failed: {e}")

# Singleton
cef_forwarder = CEFSyslogForwarder()
