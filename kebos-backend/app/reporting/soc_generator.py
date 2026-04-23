import json, jinja2, logging
from typing import Optional
from dataclasses import dataclass
from app.genai_assistant.sanitiser import LLMDataSanitiser
from app.genai_assistant.llm_router import LLMRouter, LLMClient

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    "ignore previous instructions", "system prompt", "you are now",
    "<script>", "{{", "{%", "jinja", "eval(", "exec(", "__import__",
    "\n\nHuman:", "\n\nAssistant:",
]

SYSTEM_PROMPT = """You are a cybersecurity analyst for an Indian BFSI/Government SOC.
Respond ONLY with valid JSON. No preamble. No markdown. No code blocks. No explanation.
Return exactly this JSON structure:
{
  "summary": "1-2 sentence incident summary",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "affected_systems": ["system1", "system2"],
  "recommended_actions": ["action1", "action2"],
  "cert_in_required": true,
  "mitre_techniques": ["T1566.001"],
  "hunt_query_spl": "index=* ...",
  "hunt_query_kql": "SecurityAlert | where ...",
  "cert_in_incident_type": "Targeted Scanning/Probing/Phishing"
}"""

class SecurityException(Exception):
    """Raised when prompt injection is detected"""
    pass

@dataclass
class SOCReport:
    summary: str
    severity: str
    affected_systems: list[str]
    recommended_actions: list[str]
    cert_in_required: bool
    mitre_techniques: list[str]
    hunt_query_spl: str
    hunt_query_kql: str
    cert_in_incident_type: str
    fallback_used: bool = False

class SOCReportGenerator:
    _groq_client: Optional[LLMClient] = None
    _gemma_client: Optional[LLMClient] = None
    _sanitiser = LLMDataSanitiser()
    _router = LLMRouter()

    def wire_llm_clients(self, groq_client: LLMClient, gemma_client: LLMClient):
        """Must be called at startup before any report generation."""
        self._groq_client = groq_client
        self._gemma_client = gemma_client
        logger.info(
            "SOCReportGenerator: Both LLM clients wired successfully"
        )

    async def generate_incident_report(
        self,
        threat_data: dict,
        classification: str,
        tenant_type: str
    ) -> SOCReport:
        if self._groq_client is None:
            raise RuntimeError(
                "LLM client not wired — call wire_llm_clients() at startup. "
                "This is a startup configuration error."
            )
        # Sanitise before any external call
        try:
            sanitised = self._sanitiser.sanitise(threat_data, classification)
            client = self._router.get_client(classification, tenant_type)
        except ValueError:
            # CONFIDENTIAL/RESTRICTED — use local Gemma
            sanitised = threat_data  # local only, full data is safe
            client = self._gemma_client

        # Override client with correct one
        if tenant_type == "government" or classification in ("CONFIDENTIAL", "RESTRICTED"):
            client = self._gemma_client

        # Check client availability
        if client is None:
            logger.warning("Selected LLM client is None — falling back to Jinja2 template")
            return await self._jinja2_fallback(threat_data)

        try:
            raw = await client.complete(
                system=SYSTEM_PROMPT,
                user=json.dumps(sanitised)
            )
            # Validate for prompt injection BEFORE parsing
            raw_lower = raw.lower()
            for pattern in INJECTION_PATTERNS:
                if pattern.lower() in raw_lower:
                    raise SecurityException(
                        f"Potential prompt injection in LLM output: '{pattern}'"
                    )
            # JSON parse — NEVER line-prefix string parsing
            parsed = json.loads(raw)
            # Build dict with proper defaults, fallback_used defaults to False
            report_dict = {k: parsed.get(k, "") for k in SOCReport.__dataclass_fields__ if k != "fallback_used"}
            return SOCReport(**report_dict, fallback_used=False)
        except (json.JSONDecodeError, SecurityException) as e:
            logger.warning(f"LLM output invalid ({e}) — falling back to Jinja2 template")
            return await self._jinja2_fallback(threat_data)

    async def _jinja2_fallback(self, threat_data: dict) -> SOCReport:
        """Always-available fallback. Works even if all LLMs are down."""
        env = jinja2.Environment(loader=jinja2.PackageLoader("app.reporting", "templates"))
        template = env.get_template("soc_report.j2")
        summary = template.render(**threat_data)
        return SOCReport(
            summary=summary,
            severity="UNKNOWN",
            affected_systems=[],
            recommended_actions=["Manual analyst review required"],
            cert_in_required=True,
            mitre_techniques=[],
            hunt_query_spl="",
            hunt_query_kql="",
            cert_in_incident_type="Unknown",
            fallback_used=True,
        )
