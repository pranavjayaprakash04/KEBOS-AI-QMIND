import ssl
import socket
import logging
import threading


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
            except Exception:
                try:
                    self._connect()
                    self._sock.sendall(msg.encode("utf-8"))
                except Exception:
                    self.handleError(record)


def setup_tls_syslog(app_logger: logging.Logger, host: str, port: int, ca_cert: str):
    """Call at startup if SYSLOG_HOST is configured."""
    if not host:
        return  # disabled in development
    handler = TLSSyslogHandler(host=host, port=port, ca_cert_path=ca_cert or None)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    app_logger.addHandler(handler)
