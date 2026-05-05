from fastapi import APIRouter, HTTPException, Depends, Request, Body
from pydantic import BaseModel
from typing import Optional, Literal
from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile
from app.threat_detection.catboost_engine import CatBoostThreatEngine, ThreatFeatures
from app.api.middleware.rate_limit import limiter
import asyncpg
from app.config import settings
from datetime import datetime
import logging
import json


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

router = APIRouter(prefix="/api/v1/threats", tags=["threats"])


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


@router.get("/", summary="List threat events for current tenant")
async def list_threats(
    status: Optional[str] = None,
    limit: int = 100,
    http_request: Request = None,
    current_user: UserProfile = Depends(get_current_user),
):
    """Return all threat events for the authenticated tenant."""
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")

    async with app.state.db_pool.acquire() as conn:
        await conn.execute(
            "SELECT set_config('app.current_tenant', $1, true)",
            str(current_user.tenant_id),
        )
        where = "WHERE tenant_id = $1"
        params = [current_user.tenant_id]
        if status:
            where += " AND status = $2"
            params.append(status)

        rows = await conn.fetch(
            f"""
            SELECT id, tenant_id, event_type, source_ip, indicator_value,
                   lead_category, qmind_confidence, category_scores, reversibility,
                   status, severity, created_at, updated_at
            FROM threat_events
            {where}
            ORDER BY created_at DESC
            LIMIT {limit}
            """,
            *params,
        )

    results = []
    for row in rows:
        results.append({
            "id": str(row["id"]),
            "tenant_id": str(row["tenant_id"]),
            "ioc_value": row["indicator_value"] or "",
            "ioc_type": row["event_type"] or "unknown",
            "lead_category": row["lead_category"] or "Benign",
            "confidence": float(row["qmind_confidence"] or 0.0),
            "qmind_confidence": float(row["qmind_confidence"] or 0.0),
            "source": row["source_ip"] or "unknown",
            "is_proactive": False,
            "status": row["status"] or "PENDING",
            "reversibility": row["reversibility"] or "REVERSIBLE",
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        })
    return results


class ThreatStatusUpdate(BaseModel):
    status: Literal["BENIGN", "CONFIRMED_THREAT", "PROBABLE_THREAT",
                    "POSSIBLE_THREAT", "MONITORING", "PENDING",
                    "ELEVATED", "FALSE_POSITIVE"]
    analyst_notes: Optional[str] = None


@router.patch("/{threat_id}", summary="Update threat status (e.g. mark as benign)")
async def update_threat_status(
    threat_id: str,
    body: ThreatStatusUpdate,
    current_user: UserProfile = Depends(get_current_user),
):
    """Update the status of a threat event (analyst triage action)."""
    from app.main import app
    if not hasattr(app.state, 'db_pool'):
        raise HTTPException(status_code=500, detail="Database not available")

    import uuid as _uuid
    try:
        threat_uuid = _uuid.UUID(threat_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid threat_id format")

    async with app.state.db_pool.acquire() as conn:
        await conn.execute(
            "SELECT set_config('app.current_tenant', $1, true)",
            str(current_user.tenant_id),
        )
        row = await conn.fetchrow(
            """
            UPDATE threat_events
            SET status = $1, updated_at = NOW()
            WHERE id = $2 AND tenant_id = $3
            RETURNING id, status, updated_at
            """,
            body.status, threat_uuid, current_user.tenant_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Threat not found")

    return {
        "id": str(row["id"]),
        "status": row["status"],
        "updated_at": row["updated_at"].isoformat(),
    }


@router.post("/ingest", response_model=SignalInjectResponse)
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
    if request.category not in ThreatCategory.values():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {request.category}. Must be one of: {ThreatCategory.values()}"
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
            tenant_type=current_user.tenant_type if hasattr(current_user, 'tenant_type') else "enterprise",
            confidence=signal_data["confidence"],
            category=request.category,
        )
        kafka_produced = True
    else:
        logger.warning("Threat publisher not available in app.state")
        kafka_produced = False
    
    logger.info(f"Signal injected: {signal_data}")
    
    # Store in database
    try:
        if hasattr(http_request.app.state, 'db_pool'):
            async with http_request.app.state.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO threat_events (
                        id, tenant_id, event_type, source_ip, destination_ip,
                        severity, status, qmind_confidence, indicator_value,
                        lead_category, category_scores, reversibility,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW()
                    )
                """, 
                    __import__('uuid').uuid4(),
                    current_user.tenant_id,
                    request.category,
                    source_ip,
                    "unknown",
                    "medium",
                    "pending",
                    catboost_score,
                    request.ioc_value,
                    request.category,
                    json.dumps({}),
                    "REVERSIBLE"
                )
                logger.info(f"Stored threat event in database: {request.ioc_value}")
        else:
            logger.warning("Database pool not available in app.state")
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


@router.post("/feedback/correction")
@limiter.limit("60/minute")
async def submit_correction(
    request: Request,
    indicator_value: str = Body(...),
    predicted_category: str = Body(...),
    corrected_category: str = Body(...),
    current_user: UserProfile = Depends(get_current_user)
):
    """Analyst corrects a QMind classification — feeds the retraining loop."""
    # Publish to analyst.feedback Kafka topic
    from app.threat_detection.kafka_producer import ThreatIndicatorPublisher
    if hasattr(request.app.state, 'threat_publisher'):
        await request.app.state.threat_publisher.publish_feedback({
            "indicator_value": indicator_value,
            "predicted_category": predicted_category,
            "corrected_category": corrected_category,
            "analyst_id": str(current_user.id),
            "tenant_id": str(current_user.tenant_id),
            "timestamp": datetime.utcnow().isoformat(),
        })
        return {"status": "correction submitted", "message": "Thank you. Model will improve."}
    else:
        logger.warning("Threat publisher not available in app.state")
        raise HTTPException(status_code=503, detail="Threat publisher not available")
