import ssl
import socket
import logging
import threading

logger = logging.getLogger(__name__)


class TLSSyslogHandler(logging.Handler):
    """
    TCP+TLS syslog handler. NEVER UDP — no delivery guarantee, no integrity.
    Connects to SYSLOG_HOST:SYSLOG_PORT (default 6514) with TLS verification.
    """
    def __init__(self, host: str, port: int = 6514, ca_cert_path: str = None):
        super().__init__()
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self._sock = None
        self._connect(ca_cert_path)

    def _connect(self, ca_cert_path: str = None):
        ctx = ssl.create_default_context()
        if ca_cert_path:
            ctx.load_verify_locations(ca_cert_path)
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.settimeout(10)
        self._sock = ctx.wrap_socket(raw, server_hostname=self.host)
        self._sock.connect((self.host, self.port))

    def emit(self, record: logging.LogRecord):
        with self._lock:
            try:
                msg = self.format(record) + "\n"
                self._sock.sendall(msg.encode("utf-8"))
            except Exception as e:
                logger.warning(f"TLS syslog send failed, attempting reconnect: {e}")
                try:
                    self._connect()
                    self._sock.sendall(msg.encode("utf-8"))
                except Exception as e:
                    logger.error(f"TLS syslog reconnect failed: {e}")
                    self.handleError(record)

    def emit_raw(self, message: str):
        with self._lock:
            try:
                self._sock.sendall((message + "\n").encode("utf-8"))
            except Exception as e:
                logger.warning(f"TLS syslog raw send failed, attempting reconnect: {e}")
                try:
                    self._connect()
                    self._sock.sendall((message + "\n").encode("utf-8"))
                except Exception as e:
                    logger.error(f"TLS syslog raw reconnect failed: {e}")


app_tls_handler: TLSSyslogHandler | None = None


def setup_tls_syslog(app_logger: logging.Logger, host: str, port: int, ca_cert: str):
    """Call at startup if SYSLOG_HOST is configured."""
    global app_tls_handler
    if not host:
        return  # disabled in development
    handler = TLSSyslogHandler(host=host, port=port, ca_cert_path=ca_cert or None)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    app_logger.addHandler(handler)
    app_tls_handler = handler
