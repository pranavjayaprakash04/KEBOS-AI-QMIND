import logging

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    "CONFIRMED_THREAT": 10, "ELEVATED": 7, "MONITORING": 5, "BENIGN": 1
}


def get_tls_syslog_handler():
    """Return the configured TLS syslog handler, or None if not set up."""
    try:
        from app.audit_logger.tls_syslog_handler import app_tls_handler
        return app_tls_handler
    except (ImportError, AttributeError):
        return None
CATEGORY_DEVICE_EVENT = {
    "Phishing": "Phishing detected",
    "Malware": "Malware detected",
    "C2_Infrastructure": "C2 Infrastructure detected",
    "Botnet_IP": "Botnet IP detected",
    "Credential_Leak": "Credential Leak detected",
    "Supply_Chain": "Supply Chain Compromise detected",
    "Insider_Threat": "Insider Threat detected",
    "DDoS": "DDoS Activity detected",
    "CVE_Exploitation": "CVE Exploitation detected",
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
        mitre = threat_event.get('mitre_techniques', [])
        mitre_str = ','.join(mitre) if isinstance(mitre, list) else str(mitre)
        return (
            f"CEF:0|Pynevera|KebosAI|1.0"
            f"|QMind-{lead}|{event_name}|{sev}"
            f"|src={threat_event.get('source_ip','0.0.0.0')}"
            f" dst={threat_event.get('indicator_value','')}"
            f" cat={lead}"
            f" confidence={float(threat_event.get('confidence') or threat_event.get('qmind_confidence', 0)):.3f}"
            f" cs1={mitre_str}"
            f" cs1Label=MITRETechniques"
            f" cs2={threat_event.get('tenant_id','')}"
            f" cs2Label=TenantID"
            f" cs3={threat_event.get('source','unknown')}"
            f" cs3Label=DetectionSource"
            f" msg={event_name} via Kebos AI QMind probabilistic engine"
        )

    async def forward(self, threat_event: dict) -> bool:
        """Forward as CEF to configured TLS syslog target. Returns True always."""
        handler = get_tls_syslog_handler()
        if handler is None:
            logger.debug("CEF forward skipped — TLS syslog not configured (SYSLOG_HOST empty)")
            return True
        try:
            cef_line = self.format_event(threat_event)
            handler.emit_raw(cef_line)
        except Exception as e:
            logger.error(f"CEF syslog forward failed: {e}")
        return True

# Singleton
_cef_forwarder: CEFSyslogForwarder | None = None


def get_cef_forwarder() -> CEFSyslogForwarder:
    """Get or create the singleton CEFSyslogForwarder instance"""
    global _cef_forwarder
    if _cef_forwarder is None:
        _cef_forwarder = CEFSyslogForwarder()
    return _cef_forwarder
