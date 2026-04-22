"""Network Analytics Module - Modernized for CTP Backend

Real-time network data processing and analytics with comprehensive visualization support.
Features async database operations, pattern detection, anomaly analysis, and traffic monitoring.
"""

from .api import router
from .services import NetworkAnalyticsService
from .models import (
    # Pydantic Models
    AnalyticsQueryCreate, AnalyticsResult, TimeSeriesDataPoint,
    CategoryDataPoint, NetworkNode, NetworkEdge, NetworkGraph, GeoPoint,
    TrafficPatternResponse, NetworkAnomalyResponse, NetworkFlowResponse,
    NetworkTopologyResponse, AnalyticsJobResponse, NetworkStatsResponse,
    
    # Enums
    TimeRange, VisualizationType, MetricType, TrafficDirection,
    ProtocolType, TrafficPatternType, AnomalyType, AnalysisStatus
)

__all__ = [
    "router",
    "network_analytics_service",
    "AnalyticsQueryCreate", "AnalyticsResult", "TimeSeriesDataPoint",
    "CategoryDataPoint", "NetworkNode", "NetworkEdge", "NetworkGraph", "GeoPoint",
    "TrafficPatternResponse", "NetworkAnomalyResponse", "NetworkFlowResponse",
    "NetworkTopologyResponse", "AnalyticsJobResponse", "NetworkStatsResponse",
    "TimeRange", "VisualizationType", "MetricType", "TrafficDirection",
    "ProtocolType", "TrafficPatternType", "AnomalyType", "AnalysisStatus"
]
