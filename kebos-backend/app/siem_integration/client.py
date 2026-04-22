import logging
import socket
from typing import Optional
from app.config import settings
from .formatter import SIEMFormatter, get_siem_formatter

logger = logging.getLogger(__name__)


class SIEMClient:
    """
    SIEM client for sending events via syslog.
    Supports CEF format for SIEM integration.
    """
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or settings.SYSLOG_HOST
        self.port = port or settings.SYSLOG_PORT
        self.ca_cert = settings.SYSLOG_CA_CERT
        self.formatter = get_siem_formatter()
        self.socket: Optional[socket.socket] = None
    
    def connect(self):
        """Connect to syslog server"""
        if not self.host:
            logger.warning("SYSLOG_HOST not configured, SIEM integration disabled")
            return False
        
        try:
            # TODO: Implement TLS connection with CA cert verification
            # For scaffold, use plain TCP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"Connected to SIEM syslog at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SIEM syslog: {e}")
            return False
    
    def send_event(self, cef_message: str) -> bool:
        """Send CEF-formatted event to SIEM"""
        if not self.socket:
            if not self.connect():
                return False
        
        try:
            # Syslog format: <PRI>HEADER MSG
            # Priority calculation: Facility * 8 + Severity
            # Facility = 1 (user-level), Severity = 2 (critical)
            priority = 1 * 8 + 2
            
            # Construct syslog message
            syslog_message = f"<{priority}> {cef_message}\n"
            
            self.socket.send(syslog_message.encode('utf-8'))
            logger.debug(f"Sent event to SIEM: {cef_message[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send event to SIEM: {e}")
            return False
    
    def send_threat_event(
        self,
        threat_id: str,
        category: str,
        confidence: float,
        ioc_value: str,
        ioc_type: str,
        source_type: str,
        is_proactive: bool,
        supplier_trust: Optional[float] = None,
        adversarial_stability: Optional[float] = None
    ) -> bool:
        """Format and send threat event to SIEM"""
        cef_message = self.formatter.format_threat_as_cef(
            threat_id=threat_id,
            category=category,
            confidence=confidence,
            ioc_value=ioc_value,
            ioc_type=ioc_type,
            source_type=source_type,
            is_proactive=is_proactive,
            supplier_trust=supplier_trust,
            adversarial_stability=adversarial_stability
        )
        return self.send_event(cef_message)
    
    def send_honeytoken_trigger(
        self,
        honeytoken_id: str,
        token_type: str,
        trigger_source: str,
        threat_id: str
    ) -> bool:
        """Format and send honeytoken trigger event to SIEM (critical)"""
        cef_message = self.formatter.format_honeytoken_trigger_as_cef(
            honeytoken_id=honeytoken_id,
            token_type=token_type,
            trigger_source=trigger_source,
            threat_id=threat_id
        )
        return self.send_event(cef_message)
    
    def disconnect(self):
        """Disconnect from syslog server"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Disconnected from SIEM syslog")
            except Exception as e:
                logger.error(f"Error disconnecting from SIEM: {e}")
            finally:
                self.socket = None


# Singleton instance
_client_instance: Optional[SIEMClient] = None


def get_siem_client() -> SIEMClient:
    """Get or create the singleton SIEMClient instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = SIEMClient()
    return _client_instance
