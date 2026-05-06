"""
Honeypot Event Logger - Shared event logger for all traps

Writes to InfluxDB and publishes to Kafka.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class HoneypotEventLogger:
    """
    Shared event logger for honeypot traps.
    Logs events to InfluxDB and publishes to Kafka.
    """

    def __init__(self):
        self._kafka_producer: Optional = None
        self._influx_client: Optional = None

    async def _get_kafka_producer(self):
        """Lazy initialization of Kafka producer"""
        if self._kafka_producer is None:
            try:
                from aiokafka import AIOKafkaProducer
                self._kafka_producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await self._kafka_producer.start()
                logger.info("Kafka producer initialized for honeypot events")
            except Exception as e:
                logger.error(f"Failed to initialize Kafka producer: {e}")
                self._kafka_producer = None
        return self._kafka_producer

    def _get_influx_client(self):
        """Lazy initialization of InfluxDB client"""
        if self._influx_client is None:
            try:
                from influxdb_client import InfluxDBClient
                from influxdb_client.client.write_api import ASYNCHRONOUS
                self._influx_client = InfluxDBClient(
                    url=settings.INFLUXDB_URL or "http://localhost:8086",
                    token=settings.INFLUXDB_TOKEN or "",
                    org=settings.INFLUXDB_ORG or "kebos"
                )
                self._write_api = self._influx_client.write_api(write_options=ASYNCHRONOUS)
                logger.info("InfluxDB client initialized for honeypot events")
            except Exception as e:
                logger.error(f"Failed to initialize InfluxDB client: {e}")
                self._influx_client = None
        return self._influx_client

    async def log_event(
        self,
        trap_type: str,
        attacker_ip: str,
        event_type: str,
        data: dict
    ):
        """
        Log a honeypot event to InfluxDB and Kafka.

        Args:
            trap_type: Type of trap (ssh, http, rdp)
            attacker_ip: IP address of the attacker
            event_type: Type of event (credential_attempt, page_visit, etc.)
            data: Additional event data
        """
        ts = datetime.now(timezone.utc).isoformat()

        # Write to InfluxDB
        try:
            influx_client = self._get_influx_client()
            if influx_client:
                from influxdb_client import Point

                point = Point("honeypot_event") \
                    .tag("trap_type", trap_type) \
                    .tag("event_type", event_type) \
                    .tag("attacker_ip", attacker_ip) \
                    .field("data_json", json.dumps(data)) \
                    .time(datetime.now(timezone.utc))

                self._write_api.write(
                    bucket=settings.INFLUXDB_BUCKET or "honeypot",
                    record=point
                )
                logger.debug(f"Wrote honeypot event to InfluxDB: {trap_type}/{event_type}")
        except Exception as e:
            logger.error(f"InfluxDB write failed (silent): {e}")

        # Publish to Kafka
        try:
            kafka_producer = await self._get_kafka_producer()
            if kafka_producer:
                await kafka_producer.send(
                    "honeypot.interactions",
                    value={
                        "trap_type": trap_type,
                        "attacker_ip": attacker_ip,
                        "event_type": event_type,
                        "data": data,
                        "timestamp": ts
                    }
                )
                logger.debug(f"Published honeypot event to Kafka: {trap_type}/{event_type}")
        except Exception as e:
            logger.error(f"Kafka publish failed (silent): {e}")

    async def stop(self):
        """Clean up resources"""
        if self._kafka_producer:
            try:
                await self._kafka_producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")

        if self._influx_client:
            try:
                self._influx_client.close()
                logger.info("InfluxDB client closed")
            except Exception as e:
                logger.error(f"Error closing InfluxDB client: {e}")


# Singleton instance
event_logger = HoneypotEventLogger()
