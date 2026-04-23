from aiokafka import AIOKafkaProducer
import json, asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ThreatIndicatorPublisher:
    """Publishes CatBoost-scored indicators to threat.indicators Kafka topic."""
    _producer: AIOKafkaProducer = None

    async def start(self, bootstrap_servers: str):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
            compression_type="lz4"
        )
        await self._producer.start()
        logger.info(f"Threat indicator publisher started on {bootstrap_servers}")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Threat indicator publisher stopped")

    async def publish(self, indicator_value: str, indicator_type: str,
                      catboost_score: float, source: str,
                      tenant_id: str, tenant_type: str):
        if not self._producer:
            raise RuntimeError("Publisher not started. Call start() before publish().")
        
        message = {
            "indicator_value": indicator_value,
            "indicator_type": indicator_type,
            "catboost_score": catboost_score,
            "source": source,
            "tenant_id": tenant_id,
            "tenant_type": tenant_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._producer.send_and_wait("threat.indicators", value=message)
        logger.info(f"Published indicator {indicator_value} to threat.indicators")

    async def publish_feedback(self, feedback: dict):
        """Publish analyst correction to analyst.feedback Kafka topic."""
        if not self._producer:
            raise RuntimeError("Publisher not started. Call start() before publish().")
        
        await self._producer.send_and_wait("analyst.feedback", value=feedback)
        logger.info(f"Published analyst feedback for {feedback.get('indicator_value')}")
