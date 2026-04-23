"""
Q-MIND Enterprise: Dataset Adapters

Integrates real-world threat intelligence from authoritative sources:
- PhishTank: Phishing URLs
- OpenPhish: Phishing URLs
- MalwareBazaar: Malware hashes
- AbuseIPDB: Malicious IPs
- Tranco: Clean/benign domains
- NVD: CVE vulnerability data
- Feodo Tracker: Botnet C2 infrastructure
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import hashlib

from core.threat_state import IndicatorSignature, ThreatCategory
from signals.threat_signals import Signal, SignalType

logger = logging.getLogger(__name__)


# ============================================================================
# BASE ADAPTER INTERFACE
# ============================================================================

class DatasetAdapter(ABC):
    """Base class for all threat intelligence dataset adapters."""
    
    def __init__(self, name: str, source_url: str):
        self.name = name
        self.source_url = source_url
        self.last_update = None
        self.record_count = 0
    
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch raw records from data source."""
        pass
    
    @abstractmethod
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert raw record to (IndicatorSignature, Signal) tuple."""
        pass
    
    def fetch_and_normalize(self) -> List[tuple[IndicatorSignature, Signal]]:
        """
        Main entry point: fetch data and normalize to threat signals.
        """
        try:
            raw_records = self.fetch()
            self.record_count = len(raw_records)
            self.last_update = datetime.utcnow()
            
            normalized = []
            for record in raw_records:
                try:
                    sig, signal = self.normalize(record)
                    if sig and signal:
                        normalized.append((sig, signal))
                except Exception as e:
                    logger.warning(f"{self.name}: Failed to normalize record {record}: {e}")
                    continue
            
            logger.info(f"{self.name}: Fetched {self.record_count} records, "
                       f"normalized {len(normalized)}")
            return normalized
        
        except Exception as e:
            logger.error(f"{self.name}: Fetch failed: {e}")
            return []


# ============================================================================
# PHISHING DATASET: PhishTank
# ============================================================================

class PhishTankAdapter(DatasetAdapter):
    """
    PhishTank dataset: Phishing URLs
    
    Real format (typical):
    {
        "url": "http://phishing-example.com/login",
        "phish_id": 12345,
        "submission_time": "2024-01-15T10:30:00",
        "verified": "yes",
        "online": "yes",
        "target": "PayPal"
    }
    """
    
    def __init__(self):
        super().__init__(
            name="PhishTank",
            source_url="https://phishtank.com/phish_archive.csv"
        )
    
    def fetch(self) -> List[Dict[str, Any]]:
        """
        Simulate fetching PhishTank data.
        In production, use CSV parsing or API call.
        """
        # Mock data for demonstration
        return [
            {
                "url": "http://paypal-verify-account.xyz/login",
                "phish_id": 12001,
                "submission_time": "2024-01-15T10:30:00",
                "verified": "yes",
                "online": "yes",
                "target": "PayPal"
            },
            {
                "url": "https://amazon-security-alert.fake/confirm",
                "phish_id": 12002,
                "submission_time": "2024-01-15T11:00:00",
                "verified": "yes",
                "online": "yes",
                "target": "Amazon"
            },
        ]
    
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert PhishTank record to threat signal."""
        from signals.threat_signals import PhishingLexicalSignal
        
        url = record.get("url", "")
        verified = record.get("verified") == "yes"
        
        # Create indicator signature
        indicator = IndicatorSignature(
            indicator_type="url",
            indicator_value=url,
            category=ThreatCategory.PHISHING
        )
        
        # Calculate entropy for lexical signal
        entropy = self._url_entropy(url)
        confidence = 0.95 if verified else 0.75
        
        signal = PhishingLexicalSignal(
            url=url,
            entropy=entropy,
            special_char_count=self._count_special_chars(url)
        )
        signal.confidence = confidence
        signal.source = self.name
        
        return indicator, signal
    
    def _url_entropy(self, url: str) -> float:
        """Simple entropy calculation for URL."""
        if not url:
            return 0.0
        char_freq = {}
        for char in url:
            char_freq[char] = char_freq.get(char, 0) + 1
        
        entropy = 0.0
        for count in char_freq.values():
            p = count / len(url)
            entropy -= p * (p and -1 * (p ** 0.5) or 0)  # Simplified
        return min(entropy, 5.0) / 5.0
    
    def _count_special_chars(self, url: str) -> int:
        """Count special characters in URL."""
        special = set('!@#$%^&*()-_=+[]{}|;:,.<>?/~`')
        return sum(1 for char in url if char in special)


# ============================================================================
# PHISHING DATASET: OpenPhish
# ============================================================================

class OpenPhishAdapter(DatasetAdapter):
    """
    OpenPhish dataset: Phishing URLs
    
    Similar to PhishTank, focuses on active phishing sites.
    """
    
    def __init__(self):
        super().__init__(
            name="OpenPhish",
            source_url="https://openphish.com/feed.txt"
        )
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Simulate OpenPhish fetch."""
        return [
            {
                "url": "http://secure-apple-id.invalid/signin",
                "added": "2024-01-15T09:15:00",
                "brand": "Apple"
            },
            {
                "url": "https://github-update-required.xyz/verify",
                "added": "2024-01-15T10:45:00",
                "brand": "GitHub"
            },
        ]
    
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert OpenPhish record to threat signal."""
        from signals.threat_signals import PhishingReputationSignal
        
        url = record.get("url", "")
        domain = url.split("/")[2] if "/" in url else url
        
        # Extract domain age heuristic
        age_days = 7  # OpenPhish typically reports newer domains
        
        indicator = IndicatorSignature(
            indicator_type="url",
            indicator_value=url,
            category=ThreatCategory.PHISHING
        )
        
        signal = PhishingReputationSignal(
            domain=domain,
            age_days=age_days,
            blacklist_count=3
        )
        signal.source = self.name
        signal.confidence = 0.9
        
        return indicator, signal


# ============================================================================
# MALWARE DATASET: MalwareBazaar
# ============================================================================

class MalwareBazaarAdapter(DatasetAdapter):
    """
    MalwareBazaar dataset: Malware file hashes
    
    Comprehensive malware sample repository.
    """
    
    def __init__(self):
        super().__init__(
            name="MalwareBazaar",
            source_url="https://malwarebazaar.abuse.ch/"
        )
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Simulate MalwareBazaar fetch."""
        return [
            {
                "sha256": "d41d8cd98f00b204e9800998ecf8427e0" + "0" * 32,  # Mock hash
                "md5": "098f6bcd4621d373cade4e832627b4f6",
                "family": "Emotet",
                "file_type": "PE32",
                "file_size": 524288,
                "first_submission": "2024-01-01",
                "last_analysis_stats": {"malicious": 45, "suspicious": 5, "undetected": 20}
            },
            {
                "sha256": "e41d8cd98f00b204e9800998ecf8427e0" + "1" * 32,
                "md5": "098f6bcd4621d373cade4e832627b4f7",
                "family": "TrickBot",
                "file_type": "PE32",
                "file_size": 768512,
                "first_submission": "2024-01-10",
                "last_analysis_stats": {"malicious": 52, "suspicious": 3, "undetected": 15}
            },
        ]
    
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert MalwareBazaar record to threat signal."""
        from signals.threat_signals import MalwareHashReputationSignal, MalwareFamilySignal
        
        sha256 = record.get("sha256", "")
        family = record.get("family", "Unknown")
        stats = record.get("last_analysis_stats", {})
        
        malicious_count = stats.get("malicious", 0)
        total_scanners = sum(stats.values()) if stats else 70
        
        indicator = IndicatorSignature(
            indicator_type="hash",
            indicator_value=sha256,
            category=ThreatCategory.MALWARE
        )
        
        # Primary signal: hash reputation
        signal = MalwareHashReputationSignal(
            file_hash=sha256,
            av_hits=malicious_count,
            total_scanners=total_scanners
        )
        signal.source = self.name
        
        return indicator, signal


# ============================================================================
# MALICIOUS IP DATASET: AbuseIPDB
# ============================================================================

class AbuseIPDBAdapter(DatasetAdapter):
    """
    AbuseIPDB dataset: Malicious IPs
    
    Reports of abusive IPs (botnet, scanning, malware hosting).
    """
    
    def __init__(self):
        super().__init__(
            name="AbuseIPDB",
            source_url="https://abuseipdb.com/"
        )
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Simulate AbuseIPDB fetch."""
        return [
            {
                "ipAddress": "192.0.2.45",
                "abuseConfidenceScore": 95,
                "usageType": "Data Center",
                "isp": "Evil VPS Provider",
                "reports": [
                    {"category": ["Malware", "Botnet"], "reportedAt": "2024-01-15T08:00:00"},
                    {"category": ["Spam"], "reportedAt": "2024-01-15T09:00:00"}
                ]
            },
            {
                "ipAddress": "198.51.100.22",
                "abuseConfidenceScore": 87,
                "usageType": "Hosting Provider",
                "isp": "Bulletproof Hosting",
                "reports": [
                    {"category": ["C2/Malware"], "reportedAt": "2024-01-14T15:00:00"}
                ]
            },
        ]
    
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert AbuseIPDB record to threat signal."""
        from signals.threat_signals import ASNReputationSignal
        
        ip = record.get("ipAddress", "")
        confidence_score = record.get("abuseConfidenceScore", 0) / 100.0
        isp = record.get("isp", "")
        
        # Determine threat category
        reports = record.get("reports", [])
        categories = []
        for report in reports:
            categories.extend(report.get("category", []))
        
        # Map to threat category
        threat_category = ThreatCategory.BOTNET_IP
        if "C2/Malware" in categories:
            threat_category = ThreatCategory.C2_INFRASTRUCTURE
        
        indicator = IndicatorSignature(
            indicator_type="ip",
            indicator_value=ip,
            category=threat_category
        )
        
        # Use ASN reputation signal
        is_bulletproof = "Bulletproof" in isp or "VPS" in isp
        
        signal = ASNReputationSignal(
            asn=f"AS{hash(isp) % 100000}",  # Mock ASN
            known_bulletproof_hosting=is_bulletproof,
            abuse_reports=len(reports)
        )
        signal.strength = confidence_score
        signal.confidence = confidence_score
        signal.source = self.name
        
        return indicator, signal


# ============================================================================
# BENIGN BASELINE: Tranco
# ============================================================================

class TrancoAdapter(DatasetAdapter):
    """
    Tranco dataset: Top legitimate domains
    
    Used as negative examples to train benign classification.
    """
    
    def __init__(self):
        super().__init__(
            name="Tranco",
            source_url="https://tranco-list.eu/"
        )
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Simulate Tranco fetch."""
        return [
            {"rank": 1, "domain": "google.com", "category": "search"},
            {"rank": 2, "domain": "facebook.com", "category": "social"},
            {"rank": 3, "domain": "amazon.com", "category": "ecommerce"},
            {"rank": 4, "domain": "wikipedia.org", "category": "reference"},
            {"rank": 5, "domain": "github.com", "category": "development"},
        ]
    
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert Tranco record to benign signal."""
        from signals.threat_signals import BenignSignal
        
        domain = record.get("domain", "")
        rank = record.get("rank", 0)
        
        indicator = IndicatorSignature(
            indicator_type="domain",
            indicator_value=domain,
            category=ThreatCategory.BENIGN
        )
        
        # High-ranking domains are very likely benign
        certitude = min(0.99, 1.0 - (rank / 1000000.0))
        
        signal = BenignSignal(
            indicator=domain,
            reason=f"Tranco rank {rank}",
            certitude=certitude
        )
        signal.source = self.name
        
        return indicator, signal


# ============================================================================
# VULNERABILITY DATASET: NVD
# ============================================================================

class NVDAdapter(DatasetAdapter):
    """
    National Vulnerability Database (NVD): CVE data
    
    Curated vulnerability information with CVSS scores.
    """
    
    def __init__(self):
        super().__init__(
            name="NVD",
            source_url="https://nvd.nist.gov/"
        )
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Simulate NVD fetch."""
        return [
            {
                "cve_id": "CVE-2024-0001",
                "description": "Critical RCE in popular web framework",
                "cvss_score": 9.8,
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "published": "2024-01-01",
                "exploits_exist": True,
                "affected_products": ["WebApp v1.0-v2.5"]
            },
            {
                "cve_id": "CVE-2024-0002",
                "description": "XSS in library authentication module",
                "cvss_score": 6.2,
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:L/A:N",
                "published": "2024-01-05",
                "exploits_exist": False,
                "affected_products": ["AuthLib v2.0-v3.1"]
            },
        ]
    
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert NVD record to threat signal."""
        from signals.threat_signals import CVESeveritySignal
        
        cve_id = record.get("cve_id", "")
        cvss_score = record.get("cvss_score", 0.0)
        exploits = 1 if record.get("exploits_exist") else 0
        
        indicator = IndicatorSignature(
            indicator_type="cve",
            indicator_value=cve_id,
            category=ThreatCategory.VULNERABILITY
        )
        
        signal = CVESeveritySignal(
            cve_id=cve_id,
            cvss_score=cvss_score,
            exploits_public=exploits
        )
        signal.source = self.name
        
        return indicator, signal


# ============================================================================
# C2 INFRASTRUCTURE: Feodo Tracker
# ============================================================================

class FeodoTrackerAdapter(DatasetAdapter):
    """
    Feodo Tracker dataset: Botnet C2 infrastructure
    
    Tracks Emotet, TrickBot, Dridex and other botnet C2 servers.
    """
    
    def __init__(self):
        super().__init__(
            name="FeodoTracker",
            source_url="https://feodotracker.abuse.ch/"
        )
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Simulate Feodo Tracker fetch."""
        return [
            {
                "c2_ip": "203.0.113.42",
                "c2_port": 8080,
                "c2_domain": "botnet-c2-001.invalid",
                "malware_family": "Emotet",
                "last_seen": "2024-01-15T05:30:00",
                "status": "Online"
            },
            {
                "c2_ip": "198.51.100.99",
                "c2_port": 443,
                "c2_domain": "trickbot-master.invalid",
                "malware_family": "TrickBot",
                "last_seen": "2024-01-15T04:15:00",
                "status": "Online"
            },
        ]
    
    def normalize(self, record: Dict[str, Any]) -> tuple[IndicatorSignature, Signal]:
        """Convert Feodo record to C2 threat signal."""
        from signals.threat_signals import C2TemporalSignal
        
        ip = record.get("c2_ip", "")
        domain = record.get("c2_domain", "")
        family = record.get("malware_family", "")
        
        # Use IP as primary indicator
        indicator = IndicatorSignature(
            indicator_type="ip",
            indicator_value=ip,
            category=ThreatCategory.C2_INFRASTRUCTURE
        )
        
        # C2 infrastructure shows sustained temporal patterns
        signal = C2TemporalSignal(
            ip_or_domain=ip,
            request_rate=50.0,  # Mock: 50 req/min sustained
            off_hours_activity=True
        )
        signal.strength = 0.95  # Very high confidence for known C2
        signal.confidence = 0.98
        signal.source = self.name
        
        return indicator, signal


# ============================================================================
# DATASET REGISTRY
# ============================================================================

class DatasetRegistry:
    """Central registry for all dataset adapters."""
    
    def __init__(self):
        self.adapters: Dict[str, DatasetAdapter] = {}
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register all standard adapters."""
        adapters = [
            PhishTankAdapter(),
            OpenPhishAdapter(),
            MalwareBazaarAdapter(),
            AbuseIPDBAdapter(),
            TrancoAdapter(),
            NVDAdapter(),
            FeodoTrackerAdapter(),
        ]
        for adapter in adapters:
            self.register(adapter.name, adapter)
    
    def register(self, name: str, adapter: DatasetAdapter):
        """Register a dataset adapter."""
        self.adapters[name] = adapter
        logger.info(f"Registered adapter: {name}")
    
    def get_adapter(self, name: str) -> Optional[DatasetAdapter]:
        """Get adapter by name."""
        return self.adapters.get(name)
    
    def fetch_all(self) -> Dict[str, List[tuple[IndicatorSignature, Signal]]]:
        """Fetch and normalize all dataset sources."""
        results = {}
        for name, adapter in self.adapters.items():
            results[name] = adapter.fetch_and_normalize()
        return results
    
    def list_adapters(self) -> List[str]:
        """List all registered adapters."""
        return list(self.adapters.keys())


logger.info("Q-MIND Enterprise: Dataset adapters initialized (7 sources)")
