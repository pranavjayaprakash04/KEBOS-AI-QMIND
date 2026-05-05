"""
SIEM Integration Router for Kebos AI.
Phase 4.3 - Provides STIX export, TAXII endpoint, and enrich API.
"""
import logging
import json
import inspect
from typing import Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from app.integrations.egress_control import EgressControlledClient
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/siem", tags=["siem"])


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

    _acquired = db_pool.acquire()
    if inspect.isawaitable(_acquired):
        _acquired = await _acquired
    async with _acquired as conn:
        rows = await conn.fetch(
            """SELECT indicator_value, indicator_type, lead_category,
                      confidence, first_seen, last_seen
             FROM iocs
             WHERE tenant_id = $1
             ORDER BY last_seen DESC LIMIT $2""",
            str(current_user.tenant_id), limit
        )
        iocs = rows

    _STIX_SCO = {
        "domain": "domain-name", "ip": "ipv4-addr", "ipv4": "ipv4-addr",
        "ipv6": "ipv6-addr", "url": "url", "email": "email-addr",
        "hash": "file", "md5": "file", "sha256": "file",
    }

    def _ioc_get(ioc, key, default=None):
        try:
            return ioc[key]
        except (KeyError, TypeError):
            return getattr(ioc, key, default)

    indicators = []
    for ioc in iocs:
        try:
            itype = _ioc_get(ioc, 'indicator_type', '') or ''
            ivalue = _ioc_get(ioc, 'indicator_value', '') or ''
            lcategory = _ioc_get(ioc, 'lead_category', '') or ''
            fseen = _ioc_get(ioc, 'first_seen', None)
            conf = _ioc_get(ioc, 'confidence', 0)
            sco_type = _STIX_SCO.get(itype.lower(), "domain-name")
            pattern = f"[{sco_type}:value = '{ivalue}']"
            ind = stix2.Indicator(
                name=f"KebosAI IOC: {itype} - {str(ivalue)[:40]}",
                pattern=pattern,
                pattern_type="stix",
                valid_from=(fseen or datetime.now(timezone.utc)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                labels=[lcategory.lower() or "unknown"],
                confidence=min(100, int(float(conf or 0) * 100)),
                external_references=[{
                    "source_name": "KebosAI",
                    "description": "Detected by QMind probabilistic engine"
                }]
            )
            indicators.append(ind)
        except Exception as e:
            logger.warning(f"Failed to create STIX indicator for IOC: {e}")
            pass

    bundle = stix2.Bundle(objects=indicators, allow_custom=True)
    return json.loads(bundle.serialize())


@router.get("/taxii/collections")
async def get_taxii_collections(
    current_user: Dict = Depends(get_current_user)
):
    """TAXII 2.1 endpoint - list available collections."""
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
async def enrich_indicator(
    indicator_value: str,
    indicator_type: str,
    request: Request = None,
    current_user: Dict = Depends(get_current_user)
) -> dict:
    """
    Universal enrichment webhook. POST an IP/domain/hash/URL, get back full
    QMind 10-category analysis in < 200ms. Wire this into Splunk/Sentinel
    alert actions to auto-enrich every alert.
    """
    import httpx
    async with EgressControlledClient() as client:
        resp = await client.post(
            "http://qmind:8001/analyze",
            json={
                "indicator_value": indicator_value,
                "indicator_type": indicator_type,
                "tenant_id": str(current_user.tenant_id),
                "tenant_type": getattr(current_user, 'tenant_type', None) or "enterprise",
            },
            timeout=httpx.Timeout(30.0)
        )
        if resp.status_code == 500:
            raise HTTPException(
                status_code=503,
                detail="QMind analysis service error — retry in 30s"
            )
        resp.raise_for_status()
        return resp.json()
