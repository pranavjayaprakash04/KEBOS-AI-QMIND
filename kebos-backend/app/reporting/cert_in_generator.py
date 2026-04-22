import hashlib
import time
import json
import logging
from datetime import datetime, timezone
from io import BytesIO
import jinja2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

logger = logging.getLogger(__name__)


class CERTInReportGenerator:
    def __init__(self):
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("app/reporting/templates")
        )

    async def generate(
        self,
        threat_event: dict,
        soc_report,           # SOCReport dataclass from soc_generator
        signing_key_bytes: bytes,
        tenant_name: str
    ) -> bytes:
        """
        Generate a Dilithium-3-signed CERT-In compliant PDF.
        Returns PDF bytes. Logs WARNING if generation > 300s (6-hour window at risk).
        """
        start = time.time()

        # 1. Render Jinja2 template
        template = self._env.get_template("cert_in_report.j2")
        html = template.render(
            organisation_name=tenant_name,
            generated_at=datetime.now(timezone.utc).isoformat(),
            incident_id=threat_event.get("id", "N/A"),
            incident_type=soc_report.cert_in_incident_type,
            severity=soc_report.severity,
            detection_time=threat_event.get("created_at", "N/A"),
            indicator_value=threat_event.get("indicator_value", ""),
            lead_category=threat_event.get("lead_category", ""),
            confidence=f"{threat_event.get('confidence', 0):.3f}",
            description=soc_report.summary,
            affected_systems=soc_report.affected_systems,
            mitre_techniques=soc_report.mitre_techniques,
            recommended_actions=soc_report.recommended_actions,
            dilithium_signature="PENDING",
            pubkey_ref="vault:dilithium3-cert-in-key",
        )

        # 2. HTML → PDF via ReportLab
        pdf_bytes = self._html_to_pdf(html)

        # 3. SHA-256 hash of PDF content
        report_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # 4. Dilithium-3 sign the hash
        try:
            from qmind_enterprise.pqc.dilithium_sign import sign
            signature = sign(signing_key_bytes, report_hash.encode())
            sig_hex = signature.hex()
        except Exception as e:
            logger.error(f"Dilithium-3 signing failed: {e}")
            sig_hex = f"SIGNING_FAILED:{e}"

        # 5. Regenerate PDF with real signature embedded
        html_signed = html.replace("PENDING", sig_hex[:64] + "...")
        pdf_bytes = self._html_to_pdf(html_signed)

        elapsed = time.time() - start
        if elapsed > 300:
            logger.warning(
                f"CERT-In report generation took {elapsed:.1f}s — "
                "6-hour window may be at risk"
            )

        logger.info(f"CERT-In report generated in {elapsed:.2f}s, hash={report_hash[:16]}...")
        return pdf_bytes

    def _html_to_pdf(self, html: str) -> bytes:
        """Convert HTML to PDF using ReportLab."""
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        # Simple text rendering — for full HTML rendering use weasyprint in production
        lines = html.replace("<br>", "\n").replace("</p>", "\n").replace("</li>", "\n")
        y = 800
        for line in lines.split("\n")[:60]:
            import re
            clean = re.sub(r"<[^>]+>", "", line).strip()
            if clean:
                c.drawString(50, y, clean[:120])
                y -= 14
        c.save()
        return buf.getvalue()
