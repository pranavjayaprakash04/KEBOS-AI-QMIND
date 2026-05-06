"""
Auto-Response Task - Celery task for automated threat response

Triggers when QMind detects high-confidence threat from honeypot.
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from celery import shared_task
import psycopg2

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://kebos:kebos_pass@localhost:5432/kebos")


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def trigger_auto_response(self, attacker_ip: str, enrichment: dict, trap_type: str):
    """
    Celery task for automated response to high-confidence threats.

    Actions:
    1. Flag IP in threat_events table
    2. Forward to SIEM
    3. Create audit log entry
    """
    actions_completed = []

    try:
        # Action 1: Flag IP in database
        _flag_ip_in_db(attacker_ip, enrichment)
        actions_completed.append("ip_flagged")
        logger.info(f"IP {attacker_ip} flagged as CONFIRMED_THREAT")

    except Exception as e:
        logger.error(f"Failed to flag IP {attacker_ip}: {e}")
        self.retry(exc=e)

    try:
        # Action 2: Forward to SIEM
        _forward_to_siem(attacker_ip, enrichment, trap_type)
        actions_completed.append("siem_forwarded")
        logger.info(f"Event for {attacker_ip} forwarded to SIEM")

    except Exception as e:
        logger.error(f"Failed to forward to SIEM for {attacker_ip}: {e}")
        # Don't retry for SIEM failures - continue to audit

    try:
        # Action 3: Audit log
        _create_audit_entry(attacker_ip, enrichment, trap_type)
        actions_completed.append("audit_signed")
        logger.info(f"Audit entry created for {attacker_ip}")

    except Exception as e:
        logger.error(f"Failed to create audit entry for {attacker_ip}: {e}")
        # Don't retry for audit failures

    logger.info(f"Auto-response completed for {attacker_ip}: {actions_completed}")

    return {
        "status": "completed",
        "attacker_ip": attacker_ip,
        "actions": actions_completed
    }


def _flag_ip_in_db(attacker_ip: str, enrichment: dict):
    """Flag the attacker IP in the threat_events table"""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO threat_events (
                    indicator_value, indicator_type, source, status, confidence, category, created_at, updated_at
                ) VALUES (
                    %s, 'ip', 'honeypot', 'CONFIRMED_THREAT', %s, %s, NOW(), NOW()
                )
                ON CONFLICT (indicator_value) DO UPDATE SET
                    status = 'CONFIRMED_THREAT',
                    confidence = EXCLUDED.confidence,
                    updated_at = NOW()
                """,
                (
                    attacker_ip,
                    enrichment.get("confidence", 0.0),
                    enrichment.get("category", "Unknown")
                )
            )
            conn.commit()
    finally:
        conn.close()


def _forward_to_siem(attacker_ip: str, enrichment: dict, trap_type: str):
    """Forward event to SIEM integration"""
    try:
        from app.siem_integration.splunk_hec import get_splunk_hec_client
        from app.siem_integration.cef_forwarder import get_cef_forwarder

        # Build event payload
        event_payload = {
            "attacker_ip": attacker_ip,
            "trap_type": trap_type,
            "category": enrichment.get("category", "Unknown"),
            "stability_score": enrichment.get("stability_score", 0.0),
            "gemma_brief": enrichment.get("gemma_brief", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "pynevera_deception"
        }

        # Try Splunk HEC
        try:
            splunk = get_splunk_hec_client()
            # Run async function in sync context
            asyncio.run(splunk.send_event(event_payload))
            logger.info(f"Event sent to Splunk HEC for {attacker_ip}")
        except Exception as e:
            logger.warning(f"Splunk HEC failed for {attacker_ip}: {e}")

        # Try CEF forwarder
        try:
            cef = get_cef_forwarder()
            asyncio.run(cef.forward(event_payload))
            logger.info(f"Event sent via CEF for {attacker_ip}")
        except Exception as e:
            logger.warning(f"CEF forwarder failed for {attacker_ip}: {e}")

    except Exception as e:
        logger.error(f"SIEM forwarding error for {attacker_ip}: {e}")
        raise


def _create_audit_entry(attacker_ip: str, enrichment: dict, trap_type: str):
    """Create audit log entry for auto-response"""
    try:
        from app.audit_logger.chain import AuditChain

        # Get app state for db_pool - use global from main
        # This is a simplified implementation
        conn = psycopg2.connect(DATABASE_URL)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_entries (
                        event_type, actor, resource, details, created_at
                    ) VALUES (
                        'AUTO_RESPONSE_TRIGGERED', 'system', %s, %s, NOW()
                    )
                    """,
                    (
                        attacker_ip,
                        json.dumps({
                            "attacker_ip": attacker_ip,
                            "stability_score": enrichment.get("stability_score"),
                            "category": enrichment.get("category"),
                            "trap_type": trap_type
                        })
                    )
                )
                conn.commit()
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Audit entry error for {attacker_ip}: {e}")
        raise
