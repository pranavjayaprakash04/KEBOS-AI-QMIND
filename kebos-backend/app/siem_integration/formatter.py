from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CEFEvent:
    """Common Event Format (CEF) event structure"""
    header: str  # CEF:0|Vendor|Product|Version|Signature|Severity|Extension
    extensions: Dict[str, str]


class SIEMFormatter:
    """
    SIEM Integration formatter for CEF and STIX formats.
    
    - CEF (Common Event Format) for legacy SIEMs
    - STIX 2.1 for modern threat intelligence platforms
    """
    
    CEF_VERSION = "0"
    CEF_VENDOR = "KebosAI"
    CEF_PRODUCT = "Kebos"
    CEF_VERSION_STR = "1.0.0"
    
    # CEF severity levels
    CEF_SEVERITY = {
        "critical": "10",
        "high": "8",
        "medium": "5",
        "low": "3",
        "info": "1",
    }
    
    def __init__(self):
        pass
    
    def format_cef(
        self,
        event_name: str,
        severity: str,
        extensions: Dict[str, str]
    ) -> str:
        """
        Format event as CEF string.
        
        CEF format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        """
        severity_code = self.CEF_SEVERITY.get(severity.lower(), "5")
        
        # Build CEF header
        header = f"CEF:{self.CEF_VERSION}|{self.CEF_VENDOR}|{self.CEF_PRODUCT}|{self.CEF_VERSION_STR}|{event_name}|{event_name}|{severity_code}"
        
        # Build extensions
        extension_pairs = []
        for key, value in extensions.items():
            # CEF requires escaping of special characters
            safe_value = self._escape_cef_value(str(value))
            extension_pairs.append(f"{key}={safe_value}")
        
        extensions_str = " ".join(extension_pairs)
        
        return f"{header}|{extensions_str}"
    
    def _escape_cef_value(self, value: str) -> str:
        """
        Escape special CEF characters.
        CEF special characters: =, \, |, and spaces in values
        """
        # Replace backslash first to avoid double escaping
        value = value.replace("\\", "\\\\")
        value = value.replace("=", "\\=")
        value = value.replace("|", "\\|")
        
        # No need to escape spaces - CEF handles them in the extension format
        
        return value
    
    def format_threat_as_cef(
        self,
        threat_id: str,
        category: str,
        confidence: float,
        ioc_value: str,
        ioc_type: str,
        source_type: str,
        is_proactive: bool,
        supplier_trust: Optional[float] = None,
        adversarial_stability: Optional[float] = None
    ) -> str:
        """
        Format a threat event as CEF.
        """
        # Determine severity based on confidence and category
        if confidence >= 0.9 or category in ["C2_Infrastructure", "Insider_Threat", "Supply_Chain"]:
            severity = "critical"
        elif confidence >= 0.7:
            severity = "high"
        elif confidence >= 0.5:
            severity = "medium"
        else:
            severity = "low"
        
        extensions = {
            "dvchost": "kebos-backend",
            "cs1Label": "threat_id",
            "cs1": threat_id,
            "cs2Label": "category",
            "cs2": category,
            "cs3Label": "ioc_value",
            "cs3": ioc_value,
            "cs4Label": "ioc_type",
            "cs4": ioc_type,
            "cs5Label": "source_type",
            "cs5": source_type,
            "cs6Label": "confidence",
            "cs6": str(confidence),
            "cs7Label": "is_proactive",
            "cs7": str(is_proactive).lower(),
        }
        
        if supplier_trust is not None:
            extensions["cn1Label"] = "supplier_trust"
            extensions["cn1"] = str(supplier_trust)
        
        if adversarial_stability is not None:
            extensions["cn2Label"] = "adversarial_stability"
            extensions["cn2"] = str(adversarial_stability)
        
        return self.format_cef(f"threat_{category}", severity, extensions)
    
    def format_honeytoken_trigger_as_cef(
        self,
        honeytoken_id: str,
        token_type: str,
        trigger_source: str,
        threat_id: str
    ) -> str:
        """
        Format honeytoken trigger as CEF (critical severity).
        """
        extensions = {
            "dvchost": "kebos-backend",
            "cs1Label": "honeytoken_id",
            "cs1": honeytoken_id,
            "cs2Label": "token_type",
            "cs2": token_type,
            "cs3Label": "trigger_source",
            "cs3": trigger_source,
            "cs4Label": "threat_id",
            "cs4": threat_id,
        }
        
        return self.format_cef("honeytoken_trigger", "critical", extensions)
    
    def format_stix_indicator(
        self,
        ioc_value: str,
        ioc_type: str,
        category: str,
        confidence: float,
        threat_id: str
    ) -> Dict[str, Any]:
        """
        Format threat as STIX 2.1 Indicator object.
        """
        # Map ioc_type to STIX pattern type
        stix_pattern_types = {
            "ip": "ipv4-addr",
            "domain": "domain-name",
            "url": "url",
            "hash": "file:hashes.MD5",
            "email": "email-addr",
        }
        
        pattern_type = stix_pattern_types.get(ioc_type.lower(), "domain-name")
        
        # Create STIX pattern
        pattern = f"[{pattern_type}:value = '{ioc_value}']"
        
        # Determine confidence level
        if confidence >= 0.8:
            confidence_level = "high"
        elif confidence >= 0.5:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        stix_indicator = {
            "type": "indicator",
            "id": f"indicator--{threat_id}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "pattern": pattern,
            "pattern_type": "stix",
            "valid_from": datetime.utcnow().isoformat() + "Z",
            "labels": [category.lower(), "malicious-activity"],
            "confidence": confidence_level,
            "external_references": [
                {
                    "source_name": "KebosAI",
                    "external_id": threat_id,
                }
            ],
            "x_kebos_confidence": confidence,
            "x_kebos_category": category,
        }
        
        return stix_indicator
    
    def format_stix_sighting(
        self,
        indicator_id: str,
        sighting_source: str,
        sighting_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Format threat sighting as STIX 2.1 Sighting object.
        """
        if sighting_time is None:
            sighting_time = datetime.utcnow()
        
        stix_sighting = {
            "type": "sighting",
            "id": f"sighting--{sighting_time.strftime('%Y%m%d%H%M%S')}",
            "created": sighting_time.isoformat() + "Z",
            "modified": sighting_time.isoformat() + "Z",
            "first_seen": sighting_time.isoformat() + "Z",
            "last_seen": sighting_time.isoformat() + "Z",
            "where_sighted_refs": [
                {
                    "source_name": sighting_source,
                }
            ],
            "sighting_of_ref": indicator_id,
        }
        
        return stix_sighting


# Singleton instance
_formatter_instance: Optional[SIEMFormatter] = None


def get_siem_formatter() -> SIEMFormatter:
    """Get or create the singleton SIEMFormatter instance"""
    global _formatter_instance
    if _formatter_instance is None:
        _formatter_instance = SIEMFormatter()
    return _formatter_instance
