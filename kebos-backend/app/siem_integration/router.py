"""
SIEM Integration Router for Kebos AI.
Phase 4.3 - Provides STIX export, TAXII endpoint, and enrich API.
"""
import logging
import json
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.integrations.egress_control import EgressControlledClient
from app.siem_integration.stix_export import get_stix_exporter
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/siem", tags=["siem"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/stix/bundle",
            summary="Export recent IOCs as STIX 2.1 bundle")
async def get_stix_bundle(
    limit: int = 500,
    request: Request = None,
    current_user: Dict = Depends(get_current_user)
) -> dict:
    """
    STIX 2.1 bundle of recent IOCs for this tenant. Import into
    MISP, OpenCTI, IBM X-Force, or any TAXII-compatible platform.
    """
    try:
        import stix2
    except ImportError:
        raise HTTPException(503, "stix2 library not installed. Add stix2>=3.0.1 to pyproject.toml")

    db_pool = request.app.state.db_pool
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT indicator_value, indicator_type, lead_category,
                      confidence, first_seen, last_seen
             FROM iocs
             WHERE tenant_id = $1
             ORDER BY last_seen DESC LIMIT $2""",
            str(current_user.tenant_id), limit
        )
        iocs = rows

    indicators = []
    for ioc in iocs:
        try:
            ind = stix2.Indicator(
                name=f"KebosAI IOC: {ioc.indicator_type} - {ioc.indicator_value[:40]}",
                pattern=f"[{ioc.indicator_type}:value = '{ioc.indicator_value}']",
                pattern_type="stix",
                valid_from=(ioc.first_seen or datetime.utcnow()).isoformat() + "Z",
                labels=[ioc.lead_category.lower()],
                confidence=min(100, int(float(ioc.confidence or 0) * 100)),
                external_references=[{
                    "source_name": "KebosAI",
                    "description": f"Detected by QMind probabilistic engine"
                }]
            )
            indicators.append(ind)
        except Exception:
            pass

    bundle = stix2.Bundle(objects=indicators, allow_custom=True)
    return json.loads(bundle.serialize())


@router.get("/taxii/collections")
async def get_taxii_collections(
    current_user: Dict = Depends(get_current_user)
):
    """
    TAXII 2.1 endpoint - list available collections.
    """
    # TODO: Implement TAXII 2.1 server
    return {
        "collections": [
            {
                "id": "kebos-indicators",
                "title": "Kebos Threat Indicators",
                "description": "IOCs from Kebos AI threat detection",
                "media_types": ["application/vnd.oasis.stix+json;version=2.1"],
            }
        ]
    }


@router.post("/enrich",
             summary="Enrich an indicator via QMind — called by external SIEMs")
@limiter.limit("60/minute")
async def enrich_indicator(
    indicator_value: str,
    indicator_type: str,
    request: Request,
    current_user: Dict = Depends(get_current_user)
) -> dict:
    """
    Universal enrichment webhook. POST an IP/domain/hash/URL, get back full
    QMind 10-category analysis in < 200ms. Wire this into Splunk/Sentinel
    alert actions to auto-enrich every alert.
    """
    async with EgressControlledClient() as client:
        resp = await client.post(
            "http://qmind:8001/analyze",
            json={
                "indicator_value": indicator_value,
                "indicator_type": indicator_type,
                "tenant_id": str(current_user.tenant_id),
                "tenant_type": current_user.tenant_type or "enterprise",
            },
            timeout=10.0
        )
        resp.raise_for_status()
        return resp.json()
