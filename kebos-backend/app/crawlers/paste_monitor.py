"""
Paste Monitor - Scans paste sites for leaked sensitive data

Monitors pastebin.com for:
- Aadhaar numbers
- PAN cards
- UPI IDs
- IFSC codes
- Bank account numbers

Scan interval: 1800 seconds (30 minutes)
"""
import asyncio
import logging
import re
from typing import Dict
from app.integrations.egress_control import EgressControlledClient
from app.config import settings

logger = logging.getLogger(__name__)


class PasteMonitor:
    """Monitor paste sites for leaked sensitive data"""
    
    PATTERNS = {
        "aadhaar": r'\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b',
        "pan_card": r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
        "upi_id": r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\b',
        "ifsc": r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
        "bank_account": r'\b[0-9]{9,18}\b',
    }
    SCAN_INTERVAL_SECONDS = 1800
    
    def __init__(self):
        self.egress_client = None
        self._running = False
    
    async def start(self):
        """Start paste monitoring"""
        self._running = True
        self.egress_client = EgressControlledClient(timeout=30.0)
        
        logger.info("Starting Paste Monitor...")
        
        # Start monitoring in background task
        task = asyncio.create_task(self._scan_pastebin_loop())
        task.add_done_callback(self._handle_task_error)
        
        return task
    
    async def _scan_pastebin_loop(self):
        """Continuously scan pastebin for sensitive data"""
        while self._running:
            try:
                await self.scan_pastebin()
            except Exception as e:
                logger.error(f"Paste monitor scan failed: {e}")
            
            # Wait before next scan
            await asyncio.sleep(self.SCAN_INTERVAL_SECONDS)
    
    async def scan_pastebin(self):
        """Scan pastebin.com archive for new pastes"""
        try:
            resp = await self.egress_client.get("https://pastebin.com/archive")
            resp.raise_for_status()
            
            # Extract paste URLs from the archive page
            paste_urls = self._extract_paste_urls(resp.text)
            
            logger.info(f"Found {len(paste_urls)} paste URLs to scan")
            
            # Scan each paste
            for paste_url in paste_urls:
                if not self._running:
                    break
                await self._scan_paste(paste_url)
                
        except Exception as e:
            logger.warning(f"Paste monitor failed: {e}")
    
    def _extract_paste_urls(self, html: str) -> list:
        """Extract paste URLs from pastebin archive HTML"""
        import re
        # Match paste URLs like /archive/abc123
        pattern = r'href="/([a-zA-Z0-9]+)"'
        matches = re.findall(pattern, html)
        
        # Convert to full URLs
        urls = [f"https://pastebin.com/raw/{match}" for match in matches]
        return urls[:50]  # Limit to 50 most recent pastes
    
    async def _scan_paste(self, url: str):
        """Scan a single paste for sensitive data patterns"""
        try:
            resp = await self.egress_client.get(url)
            resp.raise_for_status()
            
            # Check for pattern matches
            matches = {}
            for name, regex in self.PATTERNS.items():
                pattern_matches = re.findall(regex, resp.text)
                if pattern_matches:
                    matches[name] = len(pattern_matches)
            
            # If matches found, inject signal
            if matches:
                await self._inject_signal(url, matches)
                
        except Exception as e:
            logger.warning(f"Failed to scan paste {url}: {e}")
    
    async def _inject_signal(self, url: str, matches: Dict[str, int]):
        """Inject signal for paste containing sensitive data"""
        try:
            payload = {
                "indicator_value": url,
                "indicator_type": "url",
                "source": "paste_monitor",
                "confidence": 0.75,
                "metadata": {
                    "pattern_matches": matches,
                    "detected_at": None  # Will be set by QMind
                }
            }
            
            response = await self.egress_client.post(
                "http://qmind:8001/signals/inject",
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(f"Paste Monitor: Injected signal for {url} with matches: {matches}")
            
        except Exception as e:
            logger.error(f"Failed to inject paste monitor signal: {e}")
    
    def _handle_task_error(self, task):
        """Handle background task errors"""
        if not task.cancelled() and task.exception():
            logger.error(f"Paste Monitor task error: {task.exception()}")
    
    async def stop(self):
        """Stop the monitor"""
        self._running = False
        if self.egress_client:
            await self.egress_client.aclose()
        logger.info("Paste Monitor stopped")


def get_paste_monitor():
    """Factory function to get Paste Monitor instance"""
    return PasteMonitor()
