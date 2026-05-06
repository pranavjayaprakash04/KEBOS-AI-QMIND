"""
QMind Client - Async HTTP client for QMind Enterprise

Provides indicator analysis with fallback on errors.
"""
import logging
from typing import Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def analyze_indicator(
    indicator_value: str,
    indicator_type: str,
    source: str,
    confidence: float,
    extra_context: Optional[dict] = None
) -> dict:
    """
    Analyze an indicator using QMind Enterprise.

    Args:
        indicator_value: The value to analyze (IP, domain, hash, etc.)
        indicator_type: Type of indicator (ip, domain, hash, url, etc.)
        source: Source of the indicator
        confidence: Initial confidence score
        extra_context: Additional context for analysis

    Returns:
        QMind analysis result or fallback dict on error
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{settings.QMIND_URL}/api/v1/analyze",
                json={
                    "indicator_value": indicator_value,
                    "indicator_type": indicator_type,
                    "source": source,
                    "confidence": confidence,
                    "extra_context": extra_context or {}
                }
            )
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as e:
        logger.warning(f"QMind timeout for {indicator_value}: {e}")
        return _get_fallback_result(confidence)

    except httpx.ConnectError as e:
        logger.warning(f"QMind connection error for {indicator_value}: {e}")
        return _get_fallback_result(confidence)

    except httpx.HTTPError as e:
        logger.warning(f"QMind HTTP error for {indicator_value}: {e}")
        return _get_fallback_result(confidence)

    except Exception as e:
        logger.warning(f"QMind unexpected error for {indicator_value}: {type(e).__name__}: {e}")
        return _get_fallback_result(confidence)


def _get_fallback_result(confidence: float) -> dict:
    """Generate fallback result when QMind is unavailable"""
    return {
        "threat_id": None,
        "confidence": confidence,
        "category": "Unknown",
        "stability_score": 0.0,
        "threat_state": {},
        "mitigation": "QMind unavailable — manual review required",
        "gemma_brief": "QMind enrichment unavailable. Manual triage required.",
        "fallback": True
    }
