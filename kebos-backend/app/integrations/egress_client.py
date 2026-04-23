"""
Egress-Controlled HTTP Client for Kebos AI.
Phase 3.1 - Enforces domain allowlist and timeout on all external API calls.
"""
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class EgressViolation(Exception):
    """Raised when egress to non-allowlisted domain is attempted in STRICT_MODE"""
    pass


class EgressControlledClient:
    """
    HTTP client with egress control - domain allowlist and enforced timeout.
    ALL external API calls in Kebos MUST use this client.
    """
    
    ALLOWED_DOMAINS = settings.ALLOWED_EGRESS_DOMAINS
    STRICT_MODE = settings.EGRESS_STRICT_MODE
    TIMEOUT = 10.0  # 10 second timeout as per requirements
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client with timeout"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self._client
    
    def _check_domain_allowed(self, url: str) -> None:
        """
        Check if domain is in allowlist. Raise EgressViolation if not.
        
        Args:
            url: Target URL
        
        Raises:
            EgressViolation: If domain not in allowlist and STRICT_MODE is True
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        if domain not in self.ALLOWED_DOMAINS and self.STRICT_MODE:
            raise EgressViolation(
                f"Egress to '{domain}' not allowed - domain not in ALLOWED_EGRESS_DOMAINS. "
                f"URL: {url}"
            )
        
        if domain not in self.ALLOWED_DOMAINS:
            logger.warning(f"Egress to non-allowlisted domain '{domain}' (STRICT_MODE=False)")
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """
        Perform GET request with egress control.
        
        Args:
            url: Target URL
            **kwargs: Additional httpx arguments
        
        Returns:
            httpx.Response
        
        Raises:
            EgressViolation: If domain not in allowlist and STRICT_MODE is True
        """
        self._check_domain_allowed(url)
        client = self._get_client()
        logger.info(f"Egress GET: {url}")
        return await client.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """
        Perform POST request with egress control.
        
        Args:
            url: Target URL
            **kwargs: Additional httpx arguments
        
        Returns:
            httpx.Response
        
        Raises:
            EgressViolation: If domain not in allowlist and STRICT_MODE is True
        """
        self._check_domain_allowed(url)
        client = self._get_client()
        logger.info(f"Egress POST: {url}")
        return await client.post(url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Perform PUT request with egress control"""
        self._check_domain_allowed(url)
        client = self._get_client()
        logger.info(f"Egress PUT: {url}")
        return await client.put(url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Perform DELETE request with egress control"""
        self._check_domain_allowed(url)
        client = self._get_client()
        logger.info(f"Egress DELETE: {url}")
        return await client.delete(url, **kwargs)
    
    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """Perform PATCH request with egress control"""
        self._check_domain_allowed(url)
        client = self._get_client()
        logger.info(f"Egress PATCH: {url}")
        return await client.patch(url, **kwargs)
    
    async def close(self):
        """Close the httpx client"""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
_egress_client: Optional[EgressControlledClient] = None


def get_egress_client() -> EgressControlledClient:
    """Get or create the singleton EgressControlledClient instance"""
    global _egress_client
    if _egress_client is None:
        _egress_client = EgressControlledClient()
    return _egress_client
