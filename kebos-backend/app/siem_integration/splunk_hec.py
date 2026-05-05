from app.integrations.egress_control import EgressControlledClient
from app.config import settings
import logging
logger = logging.getLogger(__name__)


class SplunkHECClient:
    def __init__(self, hec_url: str = None, hec_token: str = None, index: str = None):
        url = hec_url if hec_url is not None else getattr(settings, "SPLUNK_HEC_URL", "")
        token = hec_token if hec_token is not None else getattr(settings, "SPLUNK_HEC_TOKEN", "")
        idx = index if index is not None else getattr(settings, "SPLUNK_INDEX", "kebos")
        self.hec_url = url
        self.url = f"{url}/services/collector" if url else ""
        self.token = token
        self.index = idx

    def configure(self, hec_url: str, hec_token: str, index: str = "kebos"):
        self.hec_url = hec_url
        self.url = f"{hec_url}/services/collector" if hec_url else ""
        self.token = hec_token
        self.index = index
        if hec_url and hec_token:
            logger.info(f"Splunk HEC configured → {hec_url}, index={index}")

    async def send_event(self, threat_event: dict):
        if not self.token:
            return None
        payload = {
            "event": {
                "indicator":        threat_event.get("indicator_value"),
                "lead_category":    threat_event.get("lead_category"),
                "confidence":       threat_event.get("confidence"),
                "category_scores":  threat_event.get("category_scores", {}),
                "reversibility":    threat_event.get("reversibility"),
                "mitre_techniques": threat_event.get("mitre_techniques", []),
                "status":           threat_event.get("status"),
                "source":           threat_event.get("source"),
                "tenant_id":        threat_event.get("tenant_id"),
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
                    json=payload,
                    timeout=10.0
                )
                resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Splunk HEC send failed: {e}")
            return False


# Singleton
_splunk_hec: SplunkHECClient | None = None


def get_splunk_hec_client() -> SplunkHECClient:
    """Get or create the singleton SplunkHECClient instance"""
    global _splunk_hec
    if _splunk_hec is None:
        _splunk_hec = SplunkHECClient()
    return _splunk_hec
