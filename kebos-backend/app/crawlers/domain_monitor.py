"""
Domain Monitor - Monitors WHOIS data for new domain registrations

Scans WHOISXMLAPI for newly registered domains matching Indian brand patterns:
- Detects typosquatting domains
- Identifies suspicious domain registrations
- Proactive threat detection

Scan interval: 21600 seconds (6 hours)
"""
import asyncio
import logging
from typing import List
from app.integrations.egress_control import EgressControlledClient
from app.config import settings

logger = logging.getLogger(__name__)

INDIAN_BRAND_PATTERNS = [
    'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'rbi', 'npci',
    'ubi', 'pnb', 'boi', 'canara', 'indianbank', 'unionbank',
    'paytm', 'phonepe', 'googlepay', 'bhim', 'upi', 'neft', 'rtgs',
]


class DomainMonitor:
    """Monitor WHOIS data for suspicious domain registrations"""
    
    SCAN_INTERVAL_SECONDS = 21600  # 6 hours
    
    def __init__(self):
        self.egress_client = None
        self._running = False
    
    async def start(self):
        """Start domain monitoring"""
        self._running = True
        self.egress_client = EgressControlledClient(timeout=30.0)
        
        logger.info("Starting Domain Monitor...")
        
        # Start monitoring in background task
        task = asyncio.create_task(self._scan_new_domains_loop())
        task.add_done_callback(self._handle_task_error)
        
        return task
    
    async def _scan_new_domains_loop(self):
        """Continuously scan for new domain registrations"""
        while self._running:
            try:
                await self.scan_new_domains()
            except Exception as e:
                logger.error(f"Domain monitor scan failed: {e}")
            
            # Wait before next scan
            await asyncio.sleep(self.SCAN_INTERVAL_SECONDS)
    
    async def scan_new_domains(self):
        """Scan WHOISXMLAPI for new domains matching brand patterns"""
        for brand in INDIAN_BRAND_PATTERNS:
            if not self._running:
                break
            
            try:
                await self._scan_brand(brand)
            except Exception as e:
                logger.warning(f"Domain monitor failed for {brand}: {e}")
    
    async def _scan_brand(self, brand: str):
        """Scan WHOIS for a specific brand pattern"""
        if not settings.WHOISXML_API_KEY:
            logger.warning("WHOISXML_API_KEY not set, skipping domain monitor")
            return
        
        try:
            resp = await self.egress_client.get(
                "https://www.whoisxmlapi.com/whoisserver/WhoisService",
                params={
                    "apiKey": settings.WHOISXML_API_KEY,
                    "domainName": brand,
                    "outputFormat": "JSON",
                    "da": 1  # Domain availability check
                },
                timeout=30.0
            )
            resp.raise_for_status()
            
            await self._process_whois_results(resp.json(), brand)
            
        except Exception as e:
            logger.warning(f"WHOIS lookup failed for {brand}: {e}")
    
    async def _process_whois_results(self, data: dict, brand: str):
        """Process WHOIS results and inject signals for suspicious domains"""
        # Check if domain data indicates suspicious registration
        domain_info = data.get("DomainInfo", {})
        
        # Extract relevant fields
        domain_name = domain_info.get("domainName")
        created_date = domain_info.get("createdDate")
        registrar = domain_info.get("registrarName")
        
        if not domain_name:
            return
        
        # Check if domain is newly registered (last 30 days)
        if created_date:
            from datetime import datetime, timedelta
            try:
                created_dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                if datetime.utcnow() - created_dt > timedelta(days=30):
                    # Domain is not new, skip
                    return
            except Exception:
                pass
        
        # Check for suspicious indicators
        suspicious = False
        metadata = {
            "brand_pattern": brand,
            "registrar": registrar,
            "created_date": created_date,
        }
        
        # Typosquatting detection
        if self._is_typosquatting(domain_name, brand):
            suspicious = True
            metadata["typosquatting"] = True
        
        # If suspicious, inject signal
        if suspicious:
            await self._inject_signal(domain_name, metadata)
    
    def _is_typosquatting(self, domain: str, brand: str) -> bool:
        """Check if domain is a potential typosquatting attempt"""
        domain_lower = domain.lower()
        brand_lower = brand.lower()
        
        # Exact match is not typosquatting
        if brand_lower in domain_lower:
            # Check for common typosquatting patterns
            # Missing characters, doubled characters, etc.
            levenshtein_distance = self._levenshtein_distance(domain_lower, brand_lower)
            
            # If distance is small but not exact match, potential typosquatting
            if 1 <= levenshtein_distance <= 3:
                return True
        
        return False
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    async def _inject_signal(self, domain: str, metadata: dict):
        """Inject signal for suspicious domain"""
        try:
            payload = {
                "indicator_value": domain,
                "indicator_type": "domain",
                "source": "domain_monitor",
                "confidence": 0.70,
                "metadata": metadata
            }
            
            response = await self.egress_client.post(
                "http://qmind:8001/signals/inject",
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"Domain Monitor: Injected signal for suspicious domain: {domain}")
            
        except Exception as e:
            logger.error(f"Failed to inject domain monitor signal: {e}")
    
    def _handle_task_error(self, task):
        """Handle background task errors"""
        if not task.cancelled() and task.exception():
            logger.error(f"Domain Monitor task error: {task.exception()}")
    
    async def stop(self):
        """Stop the monitor"""
        self._running = False
        if self.egress_client:
            await self.egress_client.aclose()
        logger.info("Domain Monitor stopped")


def get_domain_monitor():
    """Factory function to get Domain Monitor instance"""
    return DomainMonitor()
