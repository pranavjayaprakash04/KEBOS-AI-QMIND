from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Literal
from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile
from app.threat_detection.catboost_engine import CatBoostThreatEngine, ThreatFeatures
import asyncpg
from app.config import settings
import logging


# Local ThreatCategory enum (matching qmind_enterprise signal_engine)
class ThreatCategory:
    C2_INFRASTRUCTURE = "C2_Infrastructure"
    BOTNET_IP = "Botnet_IP"
    PHISHING = "Phishing"
    MALWARE = "Malware"
    CREDENTIAL_LEAK = "Credential_Leak"
    DDoS = "DDoS"
    INSIDER_THREAT = "Insider_Threat"
    SUPPLY_CHAIN = "Supply_Chain"
    CVE_EXPLOITATION = "CVE_Exploitation"
    BENIGN = "Benign"
    
    @classmethod
    def values(cls):
        return [
            cls.C2_INFRASTRUCTURE,
            cls.BOTNET_IP,
            cls.PHISHING,
            cls.MALWARE,
            cls.CREDENTIAL_LEAK,
            cls.DDoS,
            cls.INSIDER_THREAT,
            cls.SUPPLY_CHAIN,
            cls.CVE_EXPLOITATION,
            cls.BENIGN,
        ]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


class SignalInjectRequest(BaseModel):
    """Request model for /signals/inject endpoint"""
    threat_id: str
    source_type: Literal[
        "ct_log", "paste_monitor", "domain_monitor", "apk_monitor",
        "honeypot", "crawler", "feed", "analyst"
    ]
    category: str  # Must match ThreatCategory enum
    confidence: float  # 0.0 to 1.0
    ioc_value: str
    ioc_type: str  # ip, domain, url, hash, email, etc.
    feed_source: Optional[str] = None
    metadata: Optional[dict] = None


class SignalInjectResponse(BaseModel):
    """Response model for /signals/inject endpoint"""
    threat_id: str
    status: str
    message: str
    kafka_produced: bool


@router.post("/inject", response_model=SignalInjectResponse)
async def inject_signal(
    request: SignalInjectRequest,
    http_request: Request,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Inject threat signal for QMind processing.
    
    Accepts all 8 source types:
    - ct_log: Certificate Transparency log monitor
    - paste_monitor: Paste site monitor
    - domain_monitor: Domain registration monitor
    - apk_monitor: APK package monitor
    - honeypot: HoneyGrid interaction
    - crawler: External crawler discovery
    - feed: External feed ingestion
    - analyst: Manual analyst submission
    
    Proactive detection badge REQUIRED on ct_log/paste_monitor/domain_monitor/apk_monitor sources.
    """
    # Validate category
    try:
        category = ThreatCategory(request.category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {request.category}. Must be one of: {[c.value for c in ThreatCategory]}"
        )
    
    # Validate confidence range
    if not 0.0 <= request.confidence <= 1.0:
        raise HTTPException(
            status_code=400,
            detail="Confidence must be between 0.0 and 1.0"
        )
    
    # Check for proactive badge requirement
    proactive_sources = ["ct_log", "paste_monitor", "domain_monitor", "apk_monitor"]
    is_proactive = request.source_type in proactive_sources
    
    # Prepare signal data for Kafka
    signal_data = {
        "threat_id": request.threat_id,
        "source_type": request.source_type,
        "category": request.category,
        "confidence": request.confidence,
        "ioc_value": request.ioc_value,
        "ioc_type": request.ioc_type,
        "feed_source": request.feed_source or "manual",
        "is_proactive": is_proactive,
        "submitted_by": current_user.username,
        "tenant_id": current_user.tenant_id,
        "metadata": request.metadata or {},
        "timestamp": __import__('time').time()
    }
    
    # Honeytoken special handling - confidence=1.0 immediately
    if request.source_type == "honeypot":
        signal_data["confidence"] = 1.0
        signal_data["honeytoken_type"] = request.metadata.get("honeytoken_type") if request.metadata else "unknown"
    
    # CatBoost scoring
    catboost_engine = CatBoostThreatEngine()
    source_ip = http_request.client.host if http_request.client else "unknown"
    features = ThreatFeatures(
        source_ip=source_ip,
        destination_ip="unknown",
        indicator_value=request.ioc_value,
        indicator_type=request.ioc_type,
        source=request.source_type,
        tenant_id=current_user.tenant_id
    )
    catboost_score = catboost_engine.score(features)
    signal_data["catboost_score"] = catboost_score
    
    # Send to Kafka topic (threat.indicators)
    if hasattr(http_request.app.state, 'threat_publisher'):
        await http_request.app.state.threat_publisher.publish(
            indicator_value=request.ioc_value,
            indicator_type=request.ioc_type,
            catboost_score=catboost_score,
            source=request.source_type,
            tenant_id=current_user.tenant_id,
            tenant_type=current_user.tenant_type if hasattr(current_user, 'tenant_type') else "enterprise"
        )
        kafka_produced = True
    else:
        logger.warning("Threat publisher not available in app.state")
        kafka_produced = False
    
    logger.info(f"Signal injected: {signal_data}")
    
    # Store in database
    try:
        # TODO: Implement DB storage
        # For scaffold, skip
        pass
    except Exception as e:
        logger.error(f"Error storing signal in database: {e}")
        # Continue anyway - Kafka is the primary path
    
    return SignalInjectResponse(
        threat_id=request.threat_id,
        status="accepted",
        message="Signal injected successfully for QMind processing",
        kafka_produced=kafka_produced
    )


@router.get("/sources")
async def list_sources(current_user: UserProfile = Depends(get_current_user)):
    """List available signal source types"""
    return {
        "sources": [
            {"type": "ct_log", "description": "Certificate Transparency log monitor", "proactive": True},
            {"type": "paste_monitor", "description": "Paste site monitor", "proactive": True},
            {"type": "domain_monitor", "description": "Domain registration monitor", "proactive": True},
            {"type": "apk_monitor", "description": "APK package monitor", "proactive": True},
            {"type": "honeypot", "description": "HoneyGrid interaction", "proactive": False},
            {"type": "crawler", "description": "External crawler discovery", "proactive": True},
            {"type": "feed", "description": "External feed ingestion", "proactive": False},
            {"type": "analyst", "description": "Manual analyst submission", "proactive": False},
        ]
    }


@router.get("/categories")
async def list_categories(current_user: UserProfile = Depends(get_current_user)):
    """List available threat categories"""
    return {
        "categories": ThreatCategory.values()
    }
