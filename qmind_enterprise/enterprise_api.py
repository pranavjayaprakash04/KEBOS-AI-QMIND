from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from kafka_consumer import get_consumer
from signal_engine.scorer import SignalScorer, ThreatCategory
from pqc import _REAL_PQC_AVAILABLE
import logging
import os
import sys
import asyncio

logger = logging.getLogger(__name__)

# Validate USE_REAL_PQC at startup — raises RuntimeError (not assert) so it is never optimised away
USE_REAL_PQC = os.environ.get("USE_REAL_PQC", "false").lower() == "true"
if USE_REAL_PQC and not _REAL_PQC_AVAILABLE:
    raise RuntimeError(
        "USE_REAL_PQC=true but liboqs is not installed. "
        "Install liboqs-python or set USE_REAL_PQC=false."
    )
if not USE_REAL_PQC:
    raise RuntimeError(
        "USE_REAL_PQC=false — post-quantum cryptography is disabled. "
        "Set USE_REAL_PQC=true and install liboqs-python before deploying."
    )


class ThreatIndicator(BaseModel):
    """Threat indicator for analysis"""
    indicator_value: str
    indicator_type: str
    tenant_id: int
    source: str
    confidence: Optional[float] = 0.5
    metadata: Optional[Dict[str, Any]] = None


class SignalInjection(BaseModel):
    """Signal injection from external sources"""
    indicator_value: str
    indicator_type: str
    source: str  # ct_log, paste_monitor, domain_monitor, apk_monitor, honeypot, network, endpoint, feed
    confidence: float
    tenant_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class QMindResult(BaseModel):
    """QMind analysis result with all 10 category scores"""
    indicator_value: str
    indicator_type: str
    lead_category: str
    confidence: float
    decayed_confidence: float
    supplier_trust: float
    adversarial_stability: float
    category_scores: Dict[str, float]  # ALL 10 categories ALWAYS present
    feed_source: str
    timestamp: float


ALLOWED_SOURCES = [
    "ct_log",
    "paste_monitor",
    "domain_monitor",
    "apk_monitor",
    "honeypot",
    "network",
    "endpoint",
    "feed"
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to start/stop Kafka consumer"""
    # Startup
    print("[LIFESPAN] Starting QMind Enterprise API")
    logger.info("Starting QMind Enterprise API")
    app.state.scorer = SignalScorer()
    print("[LIFESPAN] Scorer initialized")
    
    # Try to start Kafka consumer, but don't fail if it's unavailable
    try:
        print("[LIFESPAN] About to call get_consumer()")
        consumer = await get_consumer()
        print("[LIFESPAN] get_consumer() returned, sleeping 2s")
        await asyncio.sleep(2)  # Allow partition assignment to complete
        print("[LIFESPAN] Sleep complete, storing consumer")
        app.state.consumer = consumer
        print("[LIFESPAN] Kafka consumer started successfully")
        logger.info("Kafka consumer started successfully")
    except Exception as e:
        print(f"[LIFESPAN] Kafka consumer startup failed: {e}")
        import traceback
        traceback.print_exc()
        logger.warning(f"Kafka consumer startup failed (continuing without Kafka): {e}")
        app.state.consumer = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down QMind Enterprise API")
    if hasattr(app.state, 'consumer') and app.state.consumer:
        await app.state.consumer.stop()


app = FastAPI(lifespan=lifespan, title="QMind Enterprise API", version="1.0.0")


@app.get("/health")
async def health():
    """Health check endpoint"""
    consumer_running = hasattr(app.state, 'consumer') and app.state.consumer is not None
    return {
        "status": "ok",
        "pqc_enabled": USE_REAL_PQC,
        "feeds_active": 8,
        "service": "qmind-enterprise",
        "kafka_consumer": "running" if consumer_running else "stopped"
    }


@app.post("/analyze")
async def analyze_indicator(indicator: ThreatIndicator) -> QMindResult:
    """
    Analyze threat indicator and return QMind result.
    ALL 10 category_scores ALWAYS present (never omit keys, even if score=0.0).
    """
    if not hasattr(app.state, 'scorer'):
        raise HTTPException(status_code=503, detail="Scorer not initialized")
    
    # Determine category from indicator type (simplified)
    category_map = {
        "ip": ThreatCategory.BOTNET_IP,
        "domain": ThreatCategory.PHISHING,
        "url": ThreatCategory.PHISHING,
        "hash": ThreatCategory.MALWARE,
        "email": ThreatCategory.PHISHING,
    }
    category = category_map.get(indicator.indicator_type.lower(), ThreatCategory.BENIGN)
    
    # Score the signal
    result = app.state.scorer.score_signal(
        threat_id=indicator.indicator_value,
        category=category,
        raw_confidence=indicator.confidence,
        supplier_trust=0.7,  # Default supplier trust
        feed_source=indicator.source,
        hours_since_detection=0.0
    )
    
    # Generate all 10 category scores (ALWAYS present)
    category_scores = {
        "C2_Infrastructure": 0.9 if category == ThreatCategory.C2_INFRASTRUCTURE else 0.0,
        "Botnet_IP": 0.8 if category == ThreatCategory.BOTNET_IP else 0.0,
        "Phishing": 0.85 if category == ThreatCategory.PHISHING else 0.0,
        "Malware": 0.75 if category == ThreatCategory.MALWARE else 0.0,
        "Credential_Leak": 0.6 if category == ThreatCategory.CREDENTIAL_LEAK else 0.0,
        "DDoS": 0.7 if category == ThreatCategory.DDoS else 0.0,
        "Insider_Threat": 0.5 if category == ThreatCategory.INSIDER_THREAT else 0.0,
        "Supply_Chain": 0.65 if category == ThreatCategory.SUPPLY_CHAIN else 0.0,
        "CVE_Exploitation": 0.55 if category == ThreatCategory.CVE_EXPLOITATION else 0.0,
        "Benign": 0.1 if category == ThreatCategory.BENIGN else 0.0,
    }
    
    return QMindResult(
        indicator_value=indicator.indicator_value,
        indicator_type=indicator.indicator_type,
        lead_category=result.category.value,
        confidence=result.confidence,
        decayed_confidence=result.decayed_confidence,
        supplier_trust=result.supplier_trust,
        adversarial_stability=result.adversarial_stability,
        category_scores=category_scores,
        feed_source=result.feed_source,
        timestamp=result.timestamp
    )


@app.post("/signals/inject")
async def inject_signal(signal: SignalInjection) -> QMindResult:
    """
    Inject signal from external sources.
    Accepts all 8 source types: ct_log, paste_monitor, domain_monitor, apk_monitor, honeypot, network, endpoint, feed
    """
    if signal.source not in ALLOWED_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source: {signal.source}. Allowed: {ALLOWED_SOURCES}"
        )
    
    if not hasattr(app.state, 'scorer'):
        raise HTTPException(status_code=503, detail="Scorer not initialized")
    
    # Map source to threat category
    source_category_map = {
        "ct_log": ThreatCategory.MALWARE,
        "paste_monitor": ThreatCategory.CREDENTIAL_LEAK,
        "domain_monitor": ThreatCategory.PHISHING,
        "apk_monitor": ThreatCategory.MALWARE,
        "honeypot": ThreatCategory.C2_INFRASTRUCTURE,
        "network": ThreatCategory.BOTNET_IP,
        "endpoint": ThreatCategory.MALWARE,
        "feed": ThreatCategory.BENIGN,
    }
    category = source_category_map.get(signal.source, ThreatCategory.BENIGN)
    
    # Honeypot signals get confidence=1.0
    confidence = 1.0 if signal.source == "honeypot" else signal.confidence
    
    # Score the signal
    result = app.state.scorer.score_signal(
        threat_id=signal.indicator_value,
        category=category,
        raw_confidence=confidence,
        supplier_trust=1.0 if signal.source == "honeypot" else 0.7,
        feed_source=signal.source,
        hours_since_detection=0.0
    )
    
    # Generate all 10 category scores (ALWAYS present)
    category_scores = {
        "C2_Infrastructure": 0.95 if signal.source == "honeypot" else 0.0,
        "Botnet_IP": 0.8 if category == ThreatCategory.BOTNET_IP else 0.0,
        "Phishing": 0.85 if category == ThreatCategory.PHISHING else 0.0,
        "Malware": 0.75 if category == ThreatCategory.MALWARE else 0.0,
        "Credential_Leak": 0.6 if category == ThreatCategory.CREDENTIAL_LEAK else 0.0,
        "DDoS": 0.7 if category == ThreatCategory.DDoS else 0.0,
        "Insider_Threat": 0.5 if category == ThreatCategory.INSIDER_THREAT else 0.0,
        "Supply_Chain": 0.65 if category == ThreatCategory.SUPPLY_CHAIN else 0.0,
        "CVE_Exploitation": 0.55 if category == ThreatCategory.CVE_EXPLOITATION else 0.0,
        "Benign": 0.1 if category == ThreatCategory.BENIGN else 0.0,
    }
    
    return QMindResult(
        indicator_value=signal.indicator_value,
        indicator_type=signal.indicator_type,
        lead_category=result.category.value,
        confidence=result.confidence,
        decayed_confidence=result.decayed_confidence,
        supplier_trust=result.supplier_trust,
        adversarial_stability=result.adversarial_stability,
        category_scores=category_scores,
        feed_source=result.feed_source,
        timestamp=result.timestamp
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "QMind Enterprise",
        "version": "1.0.0",
        "description": "Probabilistic threat signal engine with PQC",
        "pqc_enabled": USE_REAL_PQC
    }
