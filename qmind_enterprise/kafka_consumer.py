import asyncio
import json
import logging
from typing import Optional
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError
from signal_engine.scorer import SignalScorer, ThreatCategory
import os

logger = logging.getLogger(__name__)


class QMindKafkaConsumer:
    """
    AIOKafka consumer for QMind signal processing.
    NEVER uses kafka-python - only aiokafka.
    """
    
    TOPICS = [
        "threat.indicators",  # Kebos → QMind (CatBoost output for enrichment)
        "honeypot.interactions",  # HoneyGrid → QMind
        "crawler.discoveries",  # Crawlers → QMind
        "analyst.feedback",  # UI → ML pipeline
    ]
    
    OUTPUT_TOPIC = "qmind.results"  # QMind → Kebos (MUST be consumed)
    
    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.consumer = None
        self.producer = None
        self.scorer = SignalScorer()
        self.running = False
    
    async def start(self):
        """Start the Kafka consumer and producer"""
        print(f"[CONSUMER] Starting QMind Kafka consumer on {self.bootstrap_servers}")
        logger.info(f"Starting QMind Kafka consumer on {self.bootstrap_servers}")
        # Start consumer
        self.consumer = AIOKafkaConsumer(
            *self.TOPICS,
            bootstrap_servers=self.bootstrap_servers,
            group_id="qmind-group",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        
        await self.consumer.start()
        print("[CONSUMER] AIOKafkaConsumer started")
        logger.info("AIOKafkaConsumer started")
        
        # Start producer for qmind.results
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        print("[CONSUMER] AIOKafkaProducer started")
        logger.info("AIOKafkaProducer started")
        
        self.running = True
        print(f"[CONSUMER] QMind Kafka consumer/producer started on {self.bootstrap_servers}")
        logger.info(f"QMind Kafka consumer/producer started on {self.bootstrap_servers}")
        
        # Start consumption loop with done_callback
        print("[CONSUMER] Starting consumption loop task")
        logger.info("Starting consumption loop task")
        self._consume_task = asyncio.create_task(self._consume_loop())
        print("[CONSUMER] Task created, adding callback")
        self._consume_task.add_done_callback(self._handle_consumer_crash)
        print("[CONSUMER] Consumption loop task created")
        logger.info("Consumption loop task created")
    
    def _handle_consumer_crash(self, task):
        """Handle consumer crash with restart after 5s delay"""
        if not task.cancelled() and task.exception():
            logger.error(f"Consumer crashed: {task.exception()}")
            # Schedule restart after 5 seconds
            asyncio.get_event_loop().call_later(5, self._restart_consumer)
    
    def _restart_consumer(self):
        """Restart consumer after crash"""
        logger.info("Restarting consumer after crash...")
        task = asyncio.create_task(self._restart_consumer_async())
        task.add_done_callback(self._handle_consumer_crash)
    
    async def _restart_consumer_async(self):
        """Async restart logic"""
        try:
            await self.stop()
            await self.start()
        except Exception as e:
            logger.error(f"Failed to restart consumer: {e}")
    
    async def _consume_loop(self):
        """Main consumption loop with done_callback for proper cleanup"""
        logger.info("Consumption loop started - waiting for messages")
        try:
            async for msg in self.consumer:
                logger.info(f"Received message from topic {msg.topic}")
                try:
                    await self._process_message(msg)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                finally:
                    # Commit offset after processing
                    await self.consumer.commit()
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in consumption loop: {e}")
            raise
        finally:
            if self.running:
                await self.stop()
    
    async def _process_message(self, msg):
        """Process a single Kafka message"""
        try:
            data = json.loads(msg.value.decode('utf-8'))
            topic = msg.topic
            
            logger.info(f"Processing message from {topic}: {data.get('threat_id', 'unknown')}")
            
            # Route based on topic
            if topic == "threat.indicators":
                result = await self._process_threat_indicator(data)
            elif topic == "honeypot.interactions":
                result = await self._process_honeypot_interaction(data)
            elif topic == "crawler.discoveries":
                result = await self._process_crawler_discovery(data)
            elif topic == "analyst.feedback":
                result = await self._process_analyst_feedback(data)
            else:
                logger.warning(f"Unknown topic: {topic}")
                return
            
            # Send result to output topic
            if result:
                await self._send_result(result)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _process_threat_indicator(self, data: dict) -> dict:
        """Process threat indicator from Kebos CatBoost"""
        threat_id = data.get("threat_id") or data.get("indicator_value")
        _type_category = {"ip": "Botnet_IP", "domain": "Phishing", "url": "Phishing",
                          "hash": "Malware", "email": "Phishing"}
        category_str = data.get("category") or _type_category.get(
            data.get("indicator_type", "").lower(), "Benign")
        confidence = data.get("confidence") if data.get("confidence") is not None \
            else data.get("catboost_score", 0.0)
        supplier_trust = data.get("supplier_trust", 0.5)
        feed_source = data.get("feed_source") or data.get("source", "unknown")
        hours_elapsed = data.get("hours_since_detection", 0.0)
        tenant_id = data.get("tenant_id", "unknown")
        
        try:
            category = ThreatCategory(category_str)
        except ValueError:
            category = ThreatCategory.BENIGN
        
        result = self.scorer.score_signal(
            threat_id=threat_id,
            category=category,
            raw_confidence=confidence,
            supplier_trust=supplier_trust,
            feed_source=feed_source,
            hours_since_detection=hours_elapsed
        )
        
        return {
            "threat_id": result.threat_id,
            "indicator_value": result.threat_id,
            "lead_category": result.category.value,
            "confidence": result.confidence,
            "decayed_confidence": result.decayed_confidence,
            "supplier_trust": result.supplier_trust,
            "adversarial_stability": result.adversarial_stability,
            "feed_source": result.feed_source,
            "timestamp": result.timestamp,
            "source_topic": "threat.indicators",
            "tenant_id": tenant_id,
            "tenant_type": "enterprise",
            "category_scores": {
                "C2_Infrastructure": 0.9 if result.category.value == "C2_Infrastructure" else 0.0,
                "Botnet_IP": 0.8 if result.category.value == "Botnet_IP" else 0.0,
                "Phishing": 0.85 if result.category.value == "Phishing" else 0.0,
                "Malware": 0.75 if result.category.value == "Malware" else 0.0,
                "Credential_Leak": 0.6 if result.category.value == "Credential_Leak" else 0.0,
                "DDoS": 0.7 if result.category.value == "DDoS" else 0.0,
                "Insider_Threat": 0.5 if result.category.value == "Insider_Threat" else 0.0,
                "Supply_Chain": 0.65 if result.category.value == "Supply_Chain" else 0.0,
                "CVE_Exploitation": 0.55 if result.category.value == "CVE_Exploitation" else 0.0,
                "Benign": 0.1 if result.category.value == "Benign" else 0.0,
            },
            "reversibility": "REVERSIBLE"
        }
    
    async def _process_honeypot_interaction(self, data: dict) -> dict:
        """Process honeypot interaction - confidence=1.0 immediately"""
        # Honeytoken triggered → inject to QMind at confidence=1.0 immediately
        threat_id = data.get("threat_id")
        honeytoken_type = data.get("honeytoken_type")
        
        result = self.scorer.score_signal(
            threat_id=threat_id,
            category=ThreatCategory.C2_INFRASTRUCTURE,
            raw_confidence=1.0,
            supplier_trust=1.0,  # Honeytokens are 100% trusted
            feed_source="honeygrid",
            hours_since_detection=0.0
        )
        
        return {
            "threat_id": result.threat_id,
            "indicator_value": result.threat_id,
            "lead_category": result.category.value,
            "confidence": result.confidence,
            "decayed_confidence": result.decayed_confidence,
            "supplier_trust": result.supplier_trust,
            "adversarial_stability": result.adversarial_stability,
            "feed_source": result.feed_source,
            "timestamp": result.timestamp,
            "source_topic": "honeypot.interactions",
            "honeytoken_type": honeytoken_type,
            "tenant_id": "unknown",
            "tenant_type": "enterprise",
            "category_scores": {
                "C2_Infrastructure": 0.95,
                "Botnet_IP": 0.0,
                "Phishing": 0.0,
                "Malware": 0.0,
                "Credential_Leak": 0.0,
                "DDoS": 0.0,
                "Insider_Threat": 0.0,
                "Supply_Chain": 0.0,
                "CVE_Exploitation": 0.0,
                "Benign": 0.0,
            },
            "reversibility": "REVERSIBLE"
        }
    
    async def _process_crawler_discovery(self, data: dict) -> dict:
        """Process crawler discovery with proactive badge"""
        threat_id = data.get("threat_id")
        category_str = data.get("category", "Benign")
        confidence = data.get("confidence", 0.5)
        feed_source = data.get("feed_source", "crawler")
        
        try:
            category = ThreatCategory(category_str)
        except ValueError:
            category = ThreatCategory.BENIGN
        
        result = self.scorer.score_signal(
            threat_id=threat_id,
            category=category,
            raw_confidence=confidence,
            supplier_trust=0.7,  # Crawlers have moderate trust
            feed_source=feed_source,
            hours_since_detection=0.0
        )
        
        return {
            "threat_id": result.threat_id,
            "indicator_value": result.threat_id,
            "lead_category": result.category.value,
            "confidence": result.confidence,
            "decayed_confidence": result.decayed_confidence,
            "supplier_trust": result.supplier_trust,
            "adversarial_stability": result.adversarial_stability,
            "feed_source": result.feed_source,
            "timestamp": result.timestamp,
            "source_topic": "crawler.discoveries",
            "proactive": True,
            "tenant_id": "unknown",
            "tenant_type": "enterprise",
            "category_scores": {
                "C2_Infrastructure": 0.9 if result.category.value == "C2_Infrastructure" else 0.0,
                "Botnet_IP": 0.8 if result.category.value == "Botnet_IP" else 0.0,
                "Phishing": 0.85 if result.category.value == "Phishing" else 0.0,
                "Malware": 0.75 if result.category.value == "Malware" else 0.0,
                "Credential_Leak": 0.6 if result.category.value == "Credential_Leak" else 0.0,
                "DDoS": 0.7 if result.category.value == "DDoS" else 0.0,
                "Insider_Threat": 0.5 if result.category.value == "Insider_Threat" else 0.0,
                "Supply_Chain": 0.65 if result.category.value == "Supply_Chain" else 0.0,
                "CVE_Exploitation": 0.55 if result.category.value == "CVE_Exploitation" else 0.0,
                "Benign": 0.1 if result.category.value == "Benign" else 0.0,
            },
            "reversibility": "REVERSIBLE"
        }
    
    async def _process_analyst_feedback(self, data: dict) -> dict:
        """Process analyst feedback for ML pipeline"""
        threat_id = data.get("threat_id")
        feedback = data.get("feedback")  # true_positive, false_positive, etc.
        analyst_confidence = data.get("analyst_confidence", 0.0)
        
        # This is for ML pipeline feedback, not threat scoring
        return {
            "threat_id": threat_id,
            "indicator_value": threat_id,
            "lead_category": "Benign",
            "confidence": analyst_confidence,
            "decayed_confidence": analyst_confidence,
            "supplier_trust": 1.0,
            "adversarial_stability": 0.5,
            "feed_source": "analyst",
            "timestamp": __import__('time').time(),
            "source_topic": "analyst.feedback",
            "feedback": feedback,
            "analyst_confidence": analyst_confidence,
            "tenant_id": "unknown",
            "tenant_type": "enterprise",
            "category_scores": {
                "C2_Infrastructure": 0.0,
                "Botnet_IP": 0.0,
                "Phishing": 0.0,
                "Malware": 0.0,
                "Credential_Leak": 0.0,
                "DDoS": 0.0,
                "Insider_Threat": 0.0,
                "Supply_Chain": 0.0,
                "CVE_Exploitation": 0.0,
                "Benign": 0.1,
            },
            "reversibility": "REVERSIBLE"
        }
    
    async def _send_result(self, result: dict):
        """Send result to qmind.results topic using AIOKafkaProducer"""
        try:
            await self.producer.send_and_wait(self.OUTPUT_TOPIC, value=result)
            logger.info(f"Sent result to qmind.results: {result.get('threat_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send result to qmind.results: {e}")
    
    async def stop(self):
        """Stop the Kafka consumer and producer"""
        self.running = False
        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass
        if self.consumer:
            await self.consumer.stop()
            logger.info("QMind Kafka consumer stopped")
        if self.producer:
            await self.producer.stop()
            logger.info("QMind Kafka producer stopped")


# Singleton instance
_consumer_instance: Optional[QMindKafkaConsumer] = None


async def get_consumer() -> QMindKafkaConsumer:
    """Get or create the singleton consumer instance"""
    global _consumer_instance
    if _consumer_instance is None:
        _consumer_instance = QMindKafkaConsumer()
        await _consumer_instance.start()
    return _consumer_instance
