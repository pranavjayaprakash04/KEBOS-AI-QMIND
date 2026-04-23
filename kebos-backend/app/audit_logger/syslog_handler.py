"""
TLS Syslog Handler for Kebos AI.
Phase 2.4 - TCP+TLS syslog handler (NEVER UDP, port 6514).
"""
import logging
import ssl
import socket
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class TLSSyslogHandler(logging.Handler):
    """
    TLS Syslog Handler for secure audit log forwarding.
    TCP socket ONLY - NEVER UDP.
    Port 6514 (RFC 5425/TLS).
    """
    
    def __init__(self, host: str = None, port: int = None, ca_cert: str = None):
        super().__init__()
        self.host = host or settings.SYSLOG_HOST
        self.port = port or settings.SYSLOG_PORT
        self.ca_cert = ca_cert or settings.SYSLOG_CA_CERT
        self.sock: Optional[socket.socket] = None
        
        # Only register if SYSLOG_HOST is configured
        if not self.host:
            logger.warning("SYSLOG_HOST not configured - TLS SyslogHandler disabled")
            return
        
        # Create SSL context
        self.ssl_context = ssl.create_default_context()
        if self.ca_cert:
            self.ssl_context.load_verify_locations(cafile=self.ca_cert)
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            # For development, use default system certs
            self.ssl_context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"TLS SyslogHandler configured for {self.host}:{self.port}")
    
    def emit(self, record: logging.LogRecord):
        """Emit log record to TLS syslog server"""
        if not self.host:
            return
        
        try:
            msg = self.format(record)
            self._send(msg + "\n")
        except Exception as e:
            self.handleError(record)
    
    def _send(self, msg: str):
        """Send message to syslog server"""
        try:
            # Create TCP socket (NEVER UDP)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Wrap with SSL
            ssl_sock = self.ssl_context.wrap_socket(sock, server_hostname=self.host)
            
            # Connect and send
            ssl_sock.connect((self.host, self.port))
            ssl_sock.sendall(msg.encode('utf-8'))
            
            # Close connection
            ssl_sock.close()
            
        except Exception as e:
            logger.error(f"Failed to send to syslog: {e}")
            raise
    
    def emit_raw(self, msg: str):
        """Emit raw message to syslog (for CEF forwarding)"""
        if not self.host:
            return
        
        try:
            self._send(msg + "\n")
        except Exception as e:
            logger.error(f"Failed to send raw message to syslog: {e}")
    
    def close(self):
        """Close the handler"""
        if self.sock:
            self.sock.close()
        super().close()


def get_tls_syslog_handler() -> Optional[TLSSyslogHandler]:
    """Get TLS SyslogHandler if configured"""
    if settings.SYSLOG_HOST:
        return TLSSyslogHandler()
    return None
