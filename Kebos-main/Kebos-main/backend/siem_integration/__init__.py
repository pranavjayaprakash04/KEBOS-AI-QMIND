"""SIEM Integration Module - Modernized for CTP Backend

Handles integration with external SIEM systems via async APIs, webhooks, and real-time event processing.
Features comprehensive health monitoring, query execution, and event normalization.
"""

from .api import router
from .services import siem_service
from .models import (
    SIEMConfigCreate, SIEMConfigUpdate, SIEMConfigResponse,
    SIEMEventCreate, SIEMEventResponse,
    SIEMQueryRequest, SIEMQueryResponse,
    SIEMHealthStatus, SIEMWebhookPayload, SIEMStatsResponse,
    SIEMType, SIEMAuthType, SIEMEventSeverity, SIEMConnectionStatus
)

__all__ = [
    "router",
    "siem_service",
    "SIEMConfigCreate", "SIEMConfigUpdate", "SIEMConfigResponse",
    "SIEMEventCreate", "SIEMEventResponse",
    "SIEMQueryRequest", "SIEMQueryResponse",
    "SIEMHealthStatus", "SIEMWebhookPayload", "SIEMStatsResponse",
    "SIEMType", "SIEMAuthType", "SIEMEventSeverity", "SIEMConnectionStatus"
]
