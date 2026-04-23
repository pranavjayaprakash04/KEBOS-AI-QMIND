from app.integrations.egress_control import EgressControlledClient
import logging
logger = logging.getLogger(__name__)

class SplunkHECClient:
    def __init__(self):
        self.url = ""
        self.token = ""
        self.index = "kebos"
        self._ready = False

    def configure(self, hec_url: str, hec_token: str, index: str = "kebos"):
        self.url = f"{hec_url}/services/collector"
        self.token = hec_token
        self.index = index
        self._ready = bool(hec_url and hec_token)
        if self._ready:
            logger.info(f"Splunk HEC configured → {hec_url}, index={index}")

    async def send_event(self, threat_event: dict):
        if not self._ready:
            return   # Not configured — silently skip
        payload = {
            "event": {
                "indicator":         threat_event.get("indicator_value"),
                "lead_category":     threat_event.get("lead_category"),
                "confidence":        threat_event.get("confidence"),
                "category_scores":   threat_event.get("category_scores", {}),
                "reversibility":     threat_event.get("reversibility"),
                "mitre_techniques":  threat_event.get("mitre_techniques", []),
                "status":            threat_event.get("status"),
                "source":            threat_event.get("source"),
                "tenant_id":         threat_event.get("tenant_id"),
            },
            "sourcetype": "kebos:qmind:threat",
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
        except Exception as e:
            logger.error(f"Splunk HEC send failed: {e}")

splunk_hec = SplunkHECClient()
