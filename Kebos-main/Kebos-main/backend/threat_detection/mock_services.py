"""
Mock Threat Detection Service

Temporary replacement for the corrupted services.py file.
This provides basic compatibility while we use the CatBoost detector.
"""

import logging
from typing import List, Optional
from .models import ThreatAlert, NetworkPacket

logger = logging.getLogger(__name__)


class ThreatDetectionService:
    """
    Mock service for compatibility with existing API
    """
    
    def __init__(self):
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the threat detection service"""
        self.is_initialized = True
        logger.info("Mock threat detection service initialized")
    
    async def detect_threats(self, packets: List[NetworkPacket]) -> List[ThreatAlert]:
        """Process packets through detection pipeline (mock)"""
        logger.info(f"Mock processing {len(packets)} packets")
        return []
    
    async def detect_single_threat(self, packet: NetworkPacket) -> Optional[ThreatAlert]:
        """Process a single packet for threat detection (mock)"""
        logger.info("Mock processing single packet")
        return None
    
    async def process_packet(self, packet: NetworkPacket) -> Optional[ThreatAlert]:
        """Process a single packet (mock)"""
        return await self.detect_single_threat(packet)
    
    async def get_health_status(self):
        """Get health status of the detection system"""
        return {
            'service': 'mock_threat_detection',
            'status': 'healthy' if self.is_initialized else 'initializing',
            'detection_pipeline': 'mock',
            'note': 'This is a mock service for compatibility'
        }
