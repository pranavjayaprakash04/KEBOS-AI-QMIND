"""
STIX 2.1 Exporter for Kebos AI SIEM Integration.
Phase 4.3 - Exports IOCs as STIX 2.1 Indicators and Bundles.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import stix2

logger = logging.getLogger(__name__)


class STIXExporter:
    """
    Exports IOCs as STIX 2.1 Indicators and Bundles.
    Supports TAXII 2.1 endpoint for sharing.
    """
    
    def __init__(self):
        self.identity = stix2.Identity(
            name="KebosAI",
            identity_class="organization",
            description="Post-Quantum Native Cyber Threat Platform"
        )
    
    def to_indicator(self, ioc: Dict[str, Any]) -> stix2.Indicator:
        """
        Convert IOC to STIX 2.1 Indicator.
        
        Args:
            ioc: IOC data
        
        Returns:
            STIX 2.1 Indicator
        """
        # Map IOC types to STIX patterns
        ioc_type = ioc.get("type", "unknown")
        ioc_value = ioc.get("value", "")
        
        # STIX pattern mapping
        pattern_map = {
            "ip": f"[ipv4-addr:value = '{ioc_value}']",
            "domain": f"[domain-name:value = '{ioc_value}']",
            "url": f"[url:value = '{ioc_value}']",
            "email": f"[email-addr:value = '{ioc_value}']",
            "hash": f"[file:hashes.MD5 = '{ioc_value}']",
            "md5": f"[file:hashes.MD5 = '{ioc_value}']",
            "sha256": f"[file:hashes.SHA-256 = '{ioc_value}']",
        }
        
        pattern = pattern_map.get(ioc_type, f"[observable:value = '{ioc_value}']")
        
        # Get labels from threat category
        lead_category = ioc.get("lead_category", "malicious-activity")
        labels = [lead_category.lower()]
        
        # Confidence as integer (0-100)
        confidence = int(ioc.get("confidence", 0.5) * 100)
        
        # Create STIX Indicator
        indicator = stix2.Indicator(
            id=f"indicator--{ioc.get('id', 'unknown')}",
            name=f"{ioc_type.upper()}: {ioc_value}",
            pattern=pattern,
            pattern_type="stix",
            labels=labels,
            confidence=confidence,
            valid_from=datetime.now().isoformat(),
            created_by_ref=self.identity.id,
            object_marking_refs=[stix2.TLP_WHITE],
        )
        
        return indicator
    
    def to_bundle(self, iocs: List[Dict[str, Any]]) -> stix2.Bundle:
        """
        Convert list of IOCs to STIX 2.1 Bundle.
        
        Args:
            iocs: List of IOC data
        
        Returns:
            STIX 2.1 Bundle
        """
        objects = [self.identity]
        
        for ioc in iocs:
            try:
                indicator = self.to_indicator(ioc)
                objects.append(indicator)
            except Exception as e:
                logger.error(f"Failed to convert IOC to STIX Indicator: {e}")
        
        bundle = stix2.Bundle(objects=objects, type="bundle")
        return bundle
    
    def to_bundle_json(self, iocs: List[Dict[str, Any]]) -> str:
        """
        Convert IOCs to STIX 2.1 Bundle JSON string.
        
        Args:
            iocs: List of IOC data
        
        Returns:
            STIX 2.1 Bundle JSON string
        """
        bundle = self.to_bundle(iocs)
        return bundle.serialize(pretty=True)


# Singleton instance
_stix_exporter_instance: Optional[STIXExporter] = None


def get_stix_exporter() -> STIXExporter:
    """Get or create the singleton STIXExporter instance"""
    global _stix_exporter_instance
    if _stix_exporter_instance is None:
        _stix_exporter_instance = STIXExporter()
    return _stix_exporter_instance
