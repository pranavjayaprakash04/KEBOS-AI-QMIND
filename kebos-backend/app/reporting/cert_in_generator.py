import hashlib, logging, time, uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional
import jinja2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

logger = logging.getLogger(__name__)

class CERTInReportGenerator:
    """
    Generates CERT-In compliant incident reports as signed PDFs.
    Each report is:
      1. Rendered from a Jinja2 HTML template
      2. Converted to PDF via ReportLab
      3. SHA-256 hashed
      4. Dilithium-3 signed
      5. Returned as PDF bytes with signature embedded
    """
    TEMPLATE_DIR = Path(__file__).parent / "templates"

    def __init__(self):
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.TEMPLATE_DIR)),
            autoescape=True
        )

    async def generate(
        self,
        threat_event: dict,
        soc_report,          # SOCReport dataclass from soc_generator.py
        tenant_name: str,
        signing_key_bytes: Optional[bytes] = None,
        pubkey_ref: str = "vault:dilithium3-cert-in-key"
    ) -> bytes:
        """
        Generate a Dilithium-3-signed CERT-In compliant PDF.
        Logs a WARNING if generation takes > 300 seconds (6-hour window at risk).
        Returns: PDF bytes ready for download.
        """
        start = time.monotonic()

        now = datetime.now(timezone.utc)
        report_id = f"KEBOS-{now.strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"

        # ── 1. Render HTML template ──
        template = self._env.get_template("cert_in_report.j2")
        html_content = template.render(
            organisation_name=tenant_name,
            report_id=report_id,
            generated_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            incident_type=getattr(soc_report, 'cert_in_incident_type', 'Targeted Attack'),
            severity=getattr(soc_report, 'severity', 'HIGH'),
            detection_time=threat_event.get('created_at', now.strftime("%Y-%m-%d %H:%M:%S")),
            indicator_value=threat_event.get('indicator_value', 'N/A'),
            indicator_type=threat_event.get('indicator_type', 'unknown'),
            lead_category=threat_event.get('lead_category', 'Unknown'),
            confidence=f"{float(threat_event.get('confidence', 0)):.4f}",
            source=threat_event.get('source', 'network'),
            description=getattr(soc_report, 'summary', 'Automated incident detection.'),
            affected_systems=getattr(soc_report, 'affected_systems', []),
            mitre_techniques=getattr(soc_report, 'mitre_techniques', []),
            recommended_actions=getattr(soc_report, 'recommended_actions', []),
            report_hash="COMPUTING...",
            signature_hex="COMPUTING...",
            pubkey_ref=pubkey_ref,
            signed_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        )

        # ── 2. HTML → PDF ──
        pdf_bytes = self._render_pdf(html_content, report_id)

        # ── 3. SHA-256 hash of PDF ──
        report_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # ── 4. Dilithium-3 sign the hash ──
        sig_hex = "UNSIGNED"
        signed_at = now.strftime("%Y-%m-%d %H:%M:%S")
        if signing_key_bytes:
            try:
                from qmind_enterprise.pqc.dilithium_sign import sign
                signature = sign(signing_key_bytes, report_hash.encode())
                sig_hex = signature.hex()
                logger.info(f"CERT-In report {report_id} signed with Dilithium-3")
            except Exception as e:
                logger.error(f"Dilithium-3 signing failed: {e} — report unsigned")
        else:
            logger.warning(
                f"No signing key provided for report {report_id}. "
                "Set DILITHIUM_SIGNING_KEY in Vault before customer demo."
            )

        # ── 5. Re-render with real hash + signature ──
        html_final = template.render(
            organisation_name=tenant_name,
            report_id=report_id,
            generated_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            incident_type=getattr(soc_report, 'cert_in_incident_type', 'Targeted Attack'),
            severity=getattr(soc_report, 'severity', 'HIGH'),
            detection_time=threat_event.get('created_at', now.strftime("%Y-%m-%d %H:%M:%S")),
            indicator_value=threat_event.get('indicator_value', 'N/A'),
            indicator_type=threat_event.get('indicator_type', 'unknown'),
            lead_category=threat_event.get('lead_category', 'Unknown'),
            confidence=f"{float(threat_event.get('confidence', 0)):.4f}",
            source=threat_event.get('source', 'network'),
            description=getattr(soc_report, 'summary', 'Automated incident detection.'),
            affected_systems=getattr(soc_report, 'affected_systems', []),
            mitre_techniques=getattr(soc_report, 'mitre_techniques', []),
            recommended_actions=getattr(soc_report, 'recommended_actions', []),
            report_hash=report_hash,
            signature_hex=sig_hex[:128] + "..." if len(sig_hex) > 128 else sig_hex,
            pubkey_ref=pubkey_ref,
            signed_at=signed_at,
        )
        final_pdf = self._render_pdf(html_final, report_id)

        elapsed = time.monotonic() - start
        if elapsed > 300:
            logger.warning(
                f"CERT-In report generation took {elapsed:.1f}s — "
                "6-hour regulatory window may be at risk."
            )
        else:
            logger.info(f"CERT-In report {report_id} generated in {elapsed:.2f}s")

        return final_pdf

    def _render_pdf(self, html_content: str, report_id: str) -> bytes:
        """Convert HTML string to PDF bytes using ReportLab."""
        import re
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        # Strip HTML tags for text rendering
        clean = re.sub(r'<[^>]+>', ' ', html_content)
        clean = re.sub(r'\s+', ' ', clean).strip()

        # Write header
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(0.8, 0, 0)
        c.drawString(20*mm, height - 25*mm, "CERT-In Cyber Incident Report")

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)

        # Paginate content
        lines = []
        for line in clean.split('.'):
            line = line.strip()
            if line:
                # Word-wrap at ~100 chars
                while len(line) > 100:
                    lines.append(line[:100])
                    line = line[100:]
                if line:
                    lines.append(line + '.')

        y = height - 35*mm
        for line in lines:
            if y < 20*mm:
                c.showPage()
                y = height - 20*mm
                c.setFont("Helvetica", 9)
            c.drawString(20*mm, y, line[:110])
            y -= 5*mm

        c.save()
        return buf.getvalue()
