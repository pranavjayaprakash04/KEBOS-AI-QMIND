"""
Threat Detection Models

Pydantic models for threat detection, network packets, and anomaly reports.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(str, Enum):
    """MITRE ATT&CK based attack classifications"""
    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_CONTROL = "command_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class NetworkPacket(BaseModel):
    """Network packet data structure"""
    timestamp: datetime
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    payload_size: int
    packet_data: Optional[bytes] = None
    geo_location: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: v.hex() if v else None
        }


class AnomalyReport(BaseModel):
    """Anomaly detection report"""
    id: str
    timestamp: datetime
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    features: Dict[str, float]
    reconstruction_error: Optional[float] = None
    baseline_deviation: Optional[float] = None
    attack_type: Optional[str] = None
    detection_method: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThreatAlert(BaseModel):
    """Comprehensive threat alert with AI analysis"""
    id: str
    timestamp: datetime
    threat_level: ThreatLevel
    attack_type: AttackType
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    # Source data
    source_packets: List[NetworkPacket]
    anomaly_reports: List[AnomalyReport]
    
    # AI Analysis
    threat_description: str
    attack_vector: str
    mitre_attack_id: Optional[str] = None
    recommended_actions: List[str]
    
    # Context
    affected_assets: List[str]
    network_segment: Optional[str] = None
    
    # Metadata
    detection_method: str
    processing_time_ms: float
    false_positive_probability: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SIEMEvent(BaseModel):
    """SIEM integration event structure"""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: str
    source: str
    destination: Optional[str] = None
    description: str
    raw_data: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThreatIntelligence(BaseModel):
    """Threat intelligence data"""
    ioc_type: str  # IP, domain, hash, etc.
    ioc_value: str
    threat_type: str
    confidence: float
    source: str
    first_seen: datetime
    last_seen: datetime
    tags: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
