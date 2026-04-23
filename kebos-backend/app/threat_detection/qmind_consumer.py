from aiokafka import AIOKafkaConsumer
import asyncio, json, logging
from uuid import UUID, uuid4
from datetime import datetime
from app.config import settings
from app.deception.honeygrid import HoneyGridManager
from app.siem_integration.cef_forwarder import cef_forwarder
from app.siem_integration.splunk_hec import splunk_hec
from app.dashboard.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

# System actor ID for audit events
SYSTEM_ACTOR_ID = UUID("00000000-0000-0000-0000-000000000001")

# Global references to be set from main.py
_db_pool = None
_case_manager = None
_audit_chain = None
_honeygrid = None

TENANT_THRESHOLDS = {
    "government": {"confirmed_threat": 0.70, "elevated": 0.55, "monitoring": 0.40},
    "bfsi":       {"confirmed_threat": 0.72, "elevated": 0.58, "monitoring": 0.42},
    "enterprise": {"confirmed_threat": 0.75, "elevated": 0.60, "monitoring": 0.45},
}


def set_qmind_dependencies(db_pool, case_manager, audit_chain, honeygrid=None):
    """Set global dependencies for qmind consumer."""
    global _db_pool, _case_manager, _audit_chain, _honeygrid
    _db_pool = db_pool
    _case_manager = case_manager
    _audit_chain = audit_chain
    _honeygrid = honeygrid


async def consume_qmind_results():
    """
    Consumes qmind.results Kafka topic.
    Registered as startup background task with done_callback.
    Auto-restarts on crash after 5-second delay.
    """
    consumer = AIOKafkaConsumer(
        "qmind.results",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="kebos-backend-qmind-results",
        value_deserializer=lambda m: json.loads(m.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info("qmind.results consumer started — CONFIRMED_THREAT pipeline is live")
    try:
        async for msg in consumer:
            result = msg.value
            try:
                await update_threat_with_qmind_result(result)
            except Exception as e:
                logger.error(f"Error processing qmind result: {e}", exc_info=True)
    finally:
        await consumer.stop()


async def update_threat_with_qmind_result(result: dict):
    """
    FULLY IMPLEMENTED — never a stub. This is load-bearing code.
    Called for every message on qmind.results topic.
    """
    tenant_id   = UUID(result["tenant_id"])
    tenant_type = result.get("tenant_type", "enterprise")
    indicator   = result["indicator_value"]
    confidence  = float(result["confidence"])
    lead_category = result["lead_category"]
    category_scores = result.get("category_scores", {})
    reversibility   = result.get("reversibility", "REVERSIBLE")

    # 1. Determine status from tenant-specific thresholds
    thresholds = TENANT_THRESHOLDS.get(tenant_type, TENANT_THRESHOLDS["enterprise"])
    if confidence >= thresholds["confirmed_threat"]:
        new_status = "CONFIRMED_THREAT"
    elif confidence >= thresholds["elevated"]:
        new_status = "ELEVATED"
    elif confidence >= thresholds["monitoring"]:
        new_status = "MONITORING"
    else:
        new_status = "BENIGN"

    # 2. Update threat_events table — asyncpg update
    if _db_pool:
        async with _db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE threat_events
                SET 
                    status = $1,
                    qmind_confidence = $2,
                    lead_category = $3,
                    category_scores = $4,
                    reversibility = $5,
                    updated_at = NOW()
                WHERE indicator_value = $6 AND tenant_id = $7
            """, new_status, confidence, lead_category, json.dumps(category_scores),
                reversibility, indicator, tenant_id)
            logger.info(f"Updated threat_events: {indicator} → {new_status}")

    # 3. CONFIRMED_THREAT: create case + trigger HoneyGrid
    if new_status == "CONFIRMED_THREAT" and _case_manager:
        # Auto-create case with 6-hour CERT-In deadline
        task = asyncio.create_task(
            _case_manager.create_case(
                threat_event_id=result.get("threat_id", str(indicator)),
                tenant_id=str(tenant_id),
                ioc_value=indicator,
                lead_category=lead_category,
                qmind_confidence=confidence
            ),
            name=f"create_case_{indicator}"
        )
        task.add_done_callback(handle_task_error)

        # Log to audit chain
        if _audit_chain:
            task2 = asyncio.create_task(
                _audit_chain.append(
                    tenant_id=tenant_id,
                    actor_id=SYSTEM_ACTOR_ID,
                    action="CONFIRMED_THREAT_DETECTED",
                    resource=indicator,
                    metadata={"confidence": confidence, "lead_category": lead_category}
                ),
                name=f"audit_{indicator}"
            )
            task2.add_done_callback(handle_task_error)

        # Deploy honeypot for high-risk categories
        # Access honeygrid from app state — graceful if unavailable
        from app.main import app as kebos_app
        honeygrid = getattr(kebos_app.state, 'honeygrid', None)
        source_ip = result.get("source_ip", "")
        if honeygrid and source_ip and lead_category in (
            "C2_Infrastructure", "Botnet_IP", "Malware", "Supply_Chain", "Phishing"
        ):
            threat_id = UUID(result.get("threat_id", str(uuid4())))
            task3 = asyncio.create_task(
                honeygrid.deploy_honeypot(
                    threat_id=threat_id,
                    attacker_ip=source_ip,
                    lead_category=lead_category
                ),
                name=f"honeygrid_deploy_{source_ip[:15]}"
            )
            task3.add_done_callback(handle_task_error)
        elif not honeygrid:
            logger.warning("HoneyGrid unavailable — skipping honeypot deployment")

        # Forward to SIEMs (CEF + Splunk) as background tasks
        task4 = asyncio.create_task(
            cef_forwarder.forward(result),
            name=f"cef_forward_{indicator}"
        )
        task4.add_done_callback(handle_task_error)

        task5 = asyncio.create_task(
            splunk_hec.send_event(result),
            name=f"splunk_hec_{indicator}"
        )
        task5.add_done_callback(handle_task_error)

    # 4. WebSocket push to analyst dashboard
    await websocket_manager.broadcast_to_tenant(str(tenant_id), {
        "event": "threat_updated",
        "indicator": indicator,
        "indicator_type": result.get("indicator_type", "unknown"),
        "status": new_status,
        "confidence": round(confidence, 4),
        "lead_category": lead_category,
        "category_scores": category_scores,
        "reversibility": reversibility,
        "source": result.get("source", "unknown"),
        "mitre_techniques": result.get("mitre_techniques", []),
        "timestamp": datetime.utcnow().isoformat(),
    })
    logger.info(f"Threat {indicator} → {new_status} (conf={confidence:.3f}, tenant={tenant_id})")


def handle_task_error(task: asyncio.Task):
    """Global error handler for background tasks with auto-restart for qmind consumer."""
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.error(
            f"Background task '{task.get_name()}' crashed: {exc}",
            exc_info=exc
        )
        # Auto-restart the qmind results consumer after 5s
        if "qmind" in task.get_name():
            asyncio.get_event_loop().call_later(
                5.0,
                lambda: asyncio.create_task(
                    consume_qmind_results(),
                    name="qmind-results-consumer-restart"
                ).add_done_callback(handle_task_error)
            )
