"""
Splunk HEC Client for Kebos AI SIEM Integration.
Phase 4.3 - Sends threat events to Splunk via HTTP Event Collector.
"""
import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.integrations.egress_control import EgressControlledClient

logger = logging.getLogger(__name__)


class SplunkHECClient:
    """
    Sends threat events to Splunk via HTTP Event Collector (HEC).
    """
    
    def __init__(self, hec_url: str = None, hec_token: str = None, index: str = "kebos"):
        self.url = f"{hec_url or settings.SPLUNK_HEC_URL}/services/collector"
        self.token = hec_token or settings.SPLUNK_HEC_TOKEN
        self.index = index or settings.SPLUNK_INDEX
    
    async def send_event(self, threat_event: Dict[str, Any]) -> bool:
        """
        Send threat event to Splunk HEC.
        
        Args:
            threat_event: Threat event data
        
        Returns:
            True if sent successfully
        """
        if not self.token:
            return  # Splunk not configured
        
        payload = {
            "event": {
                "indicator": threat_event.get("indicator_value"),
                "lead_category": threat_event.get("lead_category"),
                "confidence": threat_event.get("confidence"),
                "category_scores": threat_event.get("category_scores", {}),
                "reversibility": threat_event.get("reversibility"),
                "mitre_techniques": threat_event.get("mitre_techniques", []),
                "status": threat_event.get("status"),
                "tenant_id": threat_event.get("tenant_id"),
            },
            "sourcetype": "kebos:threat",
            "index": self.index,
            "time": threat_event.get("timestamp"),
        }
        
        try:
            async with EgressControlledClient() as client:
                resp = await client.post(
                    self.url,
                    headers={"Authorization": f"Splunk {self.token}"},
                    json=payload
                )
                resp.raise_for_status()
                logger.info(f"Sent threat event to Splunk HEC")
                return True
        except Exception as e:
            logger.error(f"Error sending to Splunk HEC: {e}")
            return False


# Singleton instance
_splunk_hec_instance: Optional[SplunkHECClient] = None


def get_splunk_hec_client() -> SplunkHECClient:
    """Get or create the singleton SplunkHECClient instance"""
    global _splunk_hec_instance
    if _splunk_hec_instance is None:
        _splunk_hec_instance = SplunkHECClient()
    return _splunk_hec_instance
