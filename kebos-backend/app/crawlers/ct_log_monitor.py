"""
CT Log Monitor - Certificate Transparency Log Monitoring for Proactive Threat Detection

Monitors certificate transparency logs (via certstream.calidog.io) to detect:
- Typosquatting domains targeting Indian brands
- Spoofed certificates for financial institutions
- Proactive detection of phishing infrastructure

Target: < 10s from cert issuance to QMind signal injection
"""
import asyncio
import logging
from datetime import datetime
from typing import Set
from app.integrations.egress_control import EgressControlledClient
from app.config import settings

logger = logging.getLogger(__name__)

INDIAN_BRAND_PATTERNS = [
    'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'rbi', 'npci',
    'ubi', 'pnb', 'boi', 'canara', 'indianbank', 'unionbank',
    'paytm', 'phonepe', 'googlepay', 'bhim', 'upi', 'neft', 'rtgs',
    # Extended at runtime via tenant.brand_patterns field
]


class CTLogMonitor:
    """Monitor Certificate Transparency logs for brand spoofing detection"""
    
    def __init__(self):
        self.egress_client = None
        self.brand_patterns: Set[str] = set(INDIAN_BRAND_PATTERNS)
        self._running = False
    
    async def start(self):
        """Subscribe to certstream WebSocket"""
        self._running = True
        self.egress_client = EgressControlledClient(timeout=30.0)
        
        logger.info("Starting CT Log Monitor...")
        
        # Start monitoring in background task
        task = asyncio.create_task(self._monitor_certstream())
        task.add_done_callback(self._handle_task_error)
        
        return task
    
    async def _monitor_certstream(self):
        """Connect to certstream WebSocket and monitor certificates"""
        while self._running:
            try:
                # Connect to certstream WebSocket
                async with self.egress_client.stream(
                    "GET",
                    "https://certstream.calidog.io/",
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not self._running:
                            break
                        
                        if line.startswith("data: "):
                            # Parse SSE data
                            import json
                            try:
                                data = json.loads(line[6:])
                                await self._handle_cert(data)
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                logger.error(f"CT Log Monitor error: {e}")
                if self._running:
                    # Reconnect after 5 seconds
                    await asyncio.sleep(5)
    
    async def _handle_cert(self, message: dict):
        """Process certificate update from certstream"""
        if message.get("message_type") != "certificate_update":
            return
        
        cert_data = message.get("data", {})
        leaf_cert = cert_data.get("leaf_cert", {})
        domains = leaf_cert.get("all_domains", [])
        
        for domain in domains:
            if self._matches_brand_pattern(domain):
                # Signal injection in background task
                task = asyncio.create_task(self._inject_signal(domain, message))
                task.add_done_callback(self._handle_task_error)
    
    def _matches_brand_pattern(self, domain: str) -> bool:
        """Check if domain matches Indian brand patterns"""
        domain_lower = domain.lower()
        
        for pattern in self.brand_patterns:
            if pattern in domain_lower and not domain_lower.endswith('.in'):
                # Contains brand but not legit .in domain = likely spoofing
                return True
        
        return False
    
    async def _inject_signal(self, domain: str, cert_data: dict):
        """Inject detected domain as signal to QMind"""
        try:
            leaf_cert = cert_data.get("data", {}).get("leaf_cert", {})
            issuer = leaf_cert.get("issuer", {})
            
            payload = {
                "indicator_value": domain,
                "indicator_type": "domain",
                "source": "ct_log",  # triggers PROACTIVELY DETECTED badge in UI
                "confidence": 0.65,
                "metadata": {
                    "cert_issuer": issuer,
                    "detected_at": datetime.utcnow().isoformat()
                }
            }
            
            # Inject signal to QMind
            response = await self.egress_client.post(
                "http://qmind:8001/signals/inject",
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"CT Log: Injected signal for suspicious domain: {domain}")
            
        except Exception as e:
            logger.error(f"Failed to inject CT Log signal: {e}")
    
    def _handle_task_error(self, task):
        """Handle background task errors"""
        if not task.cancelled() and task.exception():
            logger.error(f"CT Log Monitor task error: {task.exception()}")
    
    async def stop(self):
        """Stop the monitor"""
        self._running = False
        if self.egress_client:
            await self.egress_client.aclose()
        logger.info("CT Log Monitor stopped")


def get_ct_log_monitor():
    """Factory function to get CT Log Monitor instance"""
    return CTLogMonitor()
