"""
SIEM Integration Router for Kebos AI.
Phase 4.3 - Provides STIX export, TAXII endpoint, and enrich API.
"""
import logging
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.integrations.egress_control import EgressControlledClient
from app.siem_integration.stix_export import get_stix_exporter
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/siem", tags=["siem"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/stix/bundle")
async def get_stix_bundle(
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Export recent IOCs as STIX 2.1 bundle.
    """
    from stix2 import Indicator, Bundle
    
    db_pool = request.app.state.db_pool
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        iocs = await conn.fetch(
            "SELECT * FROM iocs WHERE tenant_id=$1 ORDER BY last_seen DESC LIMIT 1000",
            str(current_user.tenant_id)
        )
    
    indicators = []
    for ioc in iocs:
        try:
            stix_indicator = Indicator(
                name=f"Kebos IOC: {ioc['indicator_type']}",
                pattern=f"[{ioc['indicator_type']}:value = '{ioc['indicator_value']}']",
                pattern_type="stix",
                valid_from=ioc['first_seen'].isoformat() if ioc['first_seen'] else "1970-01-01T00:00:00Z",
                labels=[ioc['lead_category'].lower() if ioc['lead_category'] else "unknown"],
            )
            indicators.append(stix_indicator)
        except Exception as e:
            logger.error(f"Failed to create STIX indicator for IOC {ioc['indicator_value']}: {e}")
            pass
    
    bundle = Bundle(objects=indicators)
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


@router.post("/enrich")
@limiter.limit("60/minute")
async def enrich_indicator(
    indicator_value: str,
    indicator_type: str,
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Inbound enrichment webhook — called by external SIEMs to enrich indicators.
    Returns full QMind 10-category analysis in < 200ms.
    """
    async with EgressControlledClient() as client:
        resp = await client.post(
            "http://qmind:8001/analyze",
            json={"indicator_value": indicator_value, "indicator_type": indicator_type,
                  "tenant_id": str(current_user.tenant_id)}
        )
        resp.raise_for_status()
        return resp.json()
