"""
QMind Enrichment Consumer - Kafka consumer for honeypot events

Consumes from honeypot.interactions, enriches via QMind, triggers auto-response.
"""
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.services.qmind_client import analyze_indicator
from app.dashboard.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

# Stability threshold for auto-response
STABILITY_THRESHOLD = 0.72

# Try to import auto_respond (may not exist yet in WS-05)
try:
    from app.tasks.auto_respond import trigger_auto_response
    AUTO_RESPOND_AVAILABLE = True
except ImportError:
    AUTO_RESPOND_AVAILABLE = False
    logger.warning("auto_respond not available — will skip auto-response triggers")


async def run_enrichment_consumer():
    """
    Run the QMind enrichment consumer forever.
    Consumes from honeypot.interactions topic.
    """
    consumer: Optional[AIOKafkaConsumer] = None

    try:
        consumer = AIOKafkaConsumer(
            "honeypot.interactions",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="kebos-enrichment",
            value_deserializer=lambda m: json.loads(m.decode()),
            auto_offset_reset="latest",
        )

        await consumer.start()
        logger.info("QMind enrichment consumer started — honeypot.interactions pipeline live")

        async for msg in consumer:
            try:
                event = msg.value
                await _process_honeypot_event(event)
            except Exception as e:
                logger.error(f"Error processing honeypot event: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Enrichment consumer crashed: {e}", exc_info=True)
        raise

    finally:
        if consumer:
            try:
                await consumer.stop()
                logger.info("Enrichment consumer stopped")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")


async def _process_honeypot_event(event: dict):
    """
    Process a single honeypot event:
    1. Extract attacker_ip and trap_type
    2. Call QMind for enrichment
    3. Trigger auto-response if stability >= 0.72
    4. Broadcast via WebSocket
    """
    attacker_ip = event.get("attacker_ip")
    trap_type = event.get("trap_type")

    if not attacker_ip:
        logger.warning("Honeypot event missing attacker_ip")
        return

    logger.info(f"Processing honeypot event: {trap_type} from {attacker_ip}")

    # Call QMind for enrichment
    enrichment = await analyze_indicator(
        indicator_value=attacker_ip,
        indicator_type="ip",
        source=f"honeypot:{trap_type}",
        confidence=0.8,
        extra_context={
            "trap_type": trap_type,
            "event_type": event.get("event_type"),
            "data": event.get("data", {})
        }
    )

    # Log enrichment result
    category = enrichment.get("category", "Unknown")
    stability = enrichment.get("stability_score", 0.0)
    logger.info(f"QMind enrichment for {attacker_ip}: category={category}, stability={stability:.2f}")

    # Trigger auto-response if stability >= threshold
    if stability >= STABILITY_THRESHOLD and AUTO_RESPOND_AVAILABLE:
        try:
            trigger_auto_response.delay(
                attacker_ip=attacker_ip,
                enrichment=enrichment,
                trap_type=trap_type
            )
            logger.info(f"Auto-response triggered for {attacker_ip} (stability={stability:.2f})")
        except Exception as e:
            logger.error(f"Failed to trigger auto-response: {e}")

    # Broadcast via WebSocket
    try:
        await _push_websocket_update(
            attacker_ip=attacker_ip,
            trap_type=trap_type,
            enrichment=enrichment
        )
    except Exception as e:
        logger.error(f"Failed to push WebSocket update: {e}")


async def _push_websocket_update(attacker_ip: str, trap_type: str, enrichment: dict):
    """
    Broadcast enrichment result via WebSocket manager to all connected tenants.
    """
    from datetime import datetime, timezone
    message = {
        "type": "honeypot_event",
        "attacker_ip": attacker_ip,
        "trap_type": trap_type,
        "enrichment": enrichment,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        await websocket_manager.broadcast(message)
        logger.debug(f"WebSocket broadcast: {attacker_ip} - {enrichment.get('category')}")
    except Exception as e:
        logger.error(f"WebSocket broadcast failed: {e}")
