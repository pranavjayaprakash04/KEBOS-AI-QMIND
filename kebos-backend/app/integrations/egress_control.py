import httpx
from urllib.parse import urlparse
from app.config import settings

ALLOWED_EGRESS_DOMAINS = {
    # Threat feeds
    "api.abuseipdb.com",
    "feodotracker.abuse.ch",
    "bazaar.abuse.ch",
    "services.nvd.nist.gov",
    "openphish.com",
    "data.phishtank.com",
    "urlhaus-api.abuse.ch",
    "tranco-list.eu",
    # LLM APIs
    "api.groq.com",
    # CT log monitoring — CRITICAL: must be here or CT monitor silently processes nothing
    "certstream.calidog.io",
    "ct.googleapis.com",
    "ctfe.g.co",
    "crt.sh",
    # Domain monitoring
    "www.whoisxmlapi.com",
    # CDN/Proxy
    "api.cloudflare.com",
    # Internal services (Docker network)
    "qmind",
    "vault",
    "localhost",
    "127.0.0.1",
}


class EgressControlledClient(httpx.AsyncClient):
    """
    Drop-in replacement for httpx.AsyncClient.
    All outbound HTTP in Kebos MUST use this class.
    Enforces allowlist — unexpected external connections = breach indicator.
    """
    def __init__(self, *args, **kwargs):
        # Default 10-second timeout on all requests
        kwargs.setdefault("timeout", httpx.Timeout(10.0))
        super().__init__(*args, **kwargs)

    async def request(self, method: str, url, **kwargs):
        parsed = urlparse(str(url))
        hostname = parsed.hostname or ""
        strict = getattr(settings, "EGRESS_STRICT_MODE", True)
        if hostname not in ALLOWED_EGRESS_DOMAINS:
            msg = (
                f"Egress blocked: '{hostname}' not in ALLOWED_EGRESS_DOMAINS. "
                f"Add it if intentional. URL: {url}"
            )
            if strict:
                raise PermissionError(msg)
            else:
                import logging
                logging.getLogger(__name__).warning(f"EGRESS WARNING (non-strict): {msg}")
        return await super().request(method, url, **kwargs)
