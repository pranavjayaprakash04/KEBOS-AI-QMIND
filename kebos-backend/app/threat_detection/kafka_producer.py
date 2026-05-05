from aiokafka import AIOKafkaProducer
import json, asyncio
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ThreatIndicatorPublisher:
    """Publishes CatBoost-scored indicators to threat.indicators Kafka topic."""
    _producer: AIOKafkaProducer = None

    async def start(self, bootstrap_servers: str):
        logger.info(f"Starting Threat indicator publisher on {bootstrap_servers}")
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode()
        )
        await self._producer.start()
        logger.info(f"Threat indicator publisher started successfully on {bootstrap_servers}")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Threat indicator publisher stopped")

    async def publish(self, indicator_value: str, indicator_type: str,
                      catboost_score: float, source: str,
                      tenant_id: str, tenant_type: str,
                      confidence: float = None, category: str = None):
        if not self._producer:
            raise RuntimeError("Publisher not started. Call start() before publish().")

        message = {
            "event_id": str(uuid4()),
            "threat_id": indicator_value,
            "indicator_value": indicator_value,
            "indicator_type": indicator_type,
            "ioc_value": indicator_value,
            "ioc_type": indicator_type,
            "catboost_score": catboost_score,
            "confidence": confidence if confidence is not None else catboost_score,
            "category": category if category is not None else "Unknown",
            "source": source,
            "source_type": source,
            "tenant_id": tenant_id,
            "tenant_type": tenant_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            await self._producer.send_and_wait("threat.indicators", value=message)
            logger.info(f"Published indicator {indicator_value} to threat.indicators")
        except Exception as e:
            logger.error(f"Failed to publish indicator {indicator_value} to threat.indicators: {e}")
            try:
                await self._producer.send_and_wait("threat.indicators.dlq", value=message)
                logger.warning(f"Indicator {indicator_value} sent to DLQ after publish failure")
            except Exception as dlq_exc:
                logger.critical(f"DLQ publish also failed for {indicator_value}: {dlq_exc}")
            raise

    async def publish_feedback(self, feedback: dict):
        """Publish analyst correction to analyst.feedback Kafka topic."""
        if not self._producer:
            raise RuntimeError("Publisher not started. Call start() before publish().")
        try:
            await self._producer.send_and_wait("analyst.feedback", value=feedback)
            logger.info(f"Published analyst feedback for {feedback.get('indicator_value')}")
        except Exception as e:
            logger.error(f"Failed to publish analyst feedback: {e}")
            try:
                await self._producer.send_and_wait("threat.indicators.dlq", value=feedback)
                logger.warning("Analyst feedback sent to DLQ after publish failure")
            except Exception as dlq_exc:
                logger.critical(f"DLQ publish also failed for feedback: {dlq_exc}")
            raise
