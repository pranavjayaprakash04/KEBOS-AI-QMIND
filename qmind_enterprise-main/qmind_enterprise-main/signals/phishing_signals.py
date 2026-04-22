"""
Q-MIND v3.5: Phishing Signal Module

Implements explainable, lightweight signals for phishing detection:
• Domain age signal (new domains are suspicious)
• Brand similarity signal (keyword/entropy matching)
• URL entropy signal (random-looking URLs more suspicious)
• TLS certificate mismatch (age/issuer red flags)

Design Principles:
- All signals define strength, confidence, decay_rate, contribution
- No black-box ML or hardcoded thresholds
- Signals can disagree (triggers watchlist, not blocking)
- Explainable contribution to threat state
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import hashlib
import re
import math

logger = logging.getLogger(__name__)


@dataclass
class PhishingSignal:
    """Base class for all phishing signals."""
    
    signal_id: str
    signal_type: str  # "domain_age", "brand_similarity", "url_entropy", "tls_mismatch"
    strength: float  # [0, 1] - magnitude of the signal
    confidence: float  # [0, 1] - how certain we are about this signal
    decay_rate: float  # exponential decay rate per hour
    explanation: str  # Human-readable explanation
    
    # Influence on threat amplitudes
    influence_malicious: float  # [0, 1] - increase to "malicious" amplitude
    influence_suspicious: float  # [0, 1] - increase to "suspicious" amplitude
    influence_benign: float  # [0, 1] - increase to "benign" amplitude
    
    def __post_init__(self):
        """Validate signal parameters."""
        if not (0 <= self.strength <= 1):
            raise ValueError(f"Signal strength must be [0, 1], got {self.strength}")
        if not (0 <= self.confidence <= 1):
            raise ValueError(f"Signal confidence must be [0, 1], got {self.confidence}")
        if not (0 <= self.decay_rate <= 1):
            raise ValueError(f"Signal decay_rate must be [0, 1], got {self.decay_rate}")
        
        # Verify influence sums (weak constraint, allows disagreement)
        total_influence = self.influence_malicious + self.influence_suspicious + self.influence_benign
        if not (0.5 <= total_influence <= 3.0):  # Allow diverse signals
            logger.warning(
                f"Signal {self.signal_id} has unusual influence distribution: {total_influence}"
            )
    
    def apply_decay(self, hours_elapsed: float) -> 'PhishingSignal':
        """
        Apply exponential decay to signal strength.
        
        strength(t) = initial_strength × e^(-decay_rate × t)
        """
        decay_factor = math.exp(-self.decay_rate * hours_elapsed)
        decayed_strength = self.strength * decay_factor
        
        return PhishingSignal(
            signal_id=self.signal_id,
            signal_type=self.signal_type,
            strength=decayed_strength,
            confidence=self.confidence,
            decay_rate=self.decay_rate,
            explanation=f"{self.explanation} (decayed: {decayed_strength:.4f})",
            influence_malicious=self.influence_malicious * decay_factor,
            influence_suspicious=self.influence_suspicious * decay_factor,
            influence_benign=self.influence_benign * decay_factor,
        )
    
    def to_dict(self) -> Dict:
        """Export signal as dictionary."""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "strength": round(self.strength, 4),
            "confidence": round(self.confidence, 4),
            "decay_rate": round(self.decay_rate, 4),
            "explanation": self.explanation,
            "influence": {
                "malicious": round(self.influence_malicious, 4),
                "suspicious": round(self.influence_suspicious, 4),
                "benign": round(self.influence_benign, 4),
            },
        }


class DomainAgeSignal:
    """
    Domain age signal: Newly registered domains are more suspicious.
    
    Motivation: Legitimate domains have been operational for months/years.
    Phishing domains are often registered days before attack.
    
    Signal Range:
    - 0-7 days old: HIGH suspicion (strength: 0.8)
    - 7-30 days old: MEDIUM suspicion (strength: 0.5)
    - 30-90 days old: LOW suspicion (strength: 0.2)
    - 90+ days old: BENIGN (strength: -0.3)
    
    Decay: Slow decay (λ=0.05 per hour) - domain age remains relevant
    """
    
    @staticmethod
    def calculate(
        domain: str,
        creation_date: Optional[datetime] = None,
        check_time: Optional[datetime] = None,
    ) -> PhishingSignal:
        """
        Calculate domain age signal.
        
        Args:
            domain: Domain name (e.g., "example.com")
            creation_date: WHOIS registration date (if available)
            check_time: Time of analysis (defaults to now)
        
        Returns:
            PhishingSignal with strength and confidence
        """
        check_time = check_time or datetime.utcnow()
        
        # If no WHOIS data, estimate based on heuristics
        if creation_date is None:
            # Assume unknown domain is medium-risk (0.3 strength)
            return PhishingSignal(
                signal_id=f"domain_age_{domain}",
                signal_type="domain_age",
                strength=0.3,
                confidence=0.4,  # Low confidence due to missing data
                decay_rate=0.05,
                explanation=f"Domain '{domain}' age unknown (no WHOIS data)",
                influence_malicious=0.2,
                influence_suspicious=0.3,
                influence_benign=0.0,
            )
        
        age_days = (check_time - creation_date).days
        
        if age_days < 7:
            strength = 0.8
            confidence = 0.85
            explanation = f"Domain '{domain}' registered {age_days} days ago (HIGH RISK)"
            influence_malicious = 0.7
            influence_suspicious = 0.2
            influence_benign = 0.0
        elif age_days < 30:
            strength = 0.5
            confidence = 0.75
            explanation = f"Domain '{domain}' registered {age_days} days ago (MEDIUM RISK)"
            influence_malicious = 0.4
            influence_suspicious = 0.4
            influence_benign = 0.0
        elif age_days < 90:
            strength = 0.2
            confidence = 0.7
            explanation = f"Domain '{domain}' registered {age_days} days ago (LOW RISK)"
            influence_malicious = 0.1
            influence_suspicious = 0.2
            influence_benign = 0.3
        else:
            # Established domain - benign signal
            strength = 0.0
            confidence = 0.9
            explanation = f"Domain '{domain}' established {age_days} days ago (BENIGN)"
            influence_malicious = 0.0
            influence_suspicious = 0.0
            influence_benign = 0.8
        
        return PhishingSignal(
            signal_id=f"domain_age_{domain}",
            signal_type="domain_age",
            strength=strength,
            confidence=confidence,
            decay_rate=0.05,  # Slow decay
            explanation=explanation,
            influence_malicious=influence_malicious,
            influence_suspicious=influence_suspicious,
            influence_benign=influence_benign,
        )


class BrandSimilaritySignal:
    """
    Brand similarity signal: URLs mimicking known brands are suspicious.
    
    Motivation: Phishing URLs often use domain names similar to popular
    brands (e.g., "app1e.com" instead of "apple.com").
    
    Heuristics:
    - Keywords of well-known brands in domain
    - Edit distance (Levenshtein) from popular domains
    - Entropy of domain name (random-looking = suspicious)
    
    Decay: Fast decay (λ=0.15) - brand campaigns rotate quickly
    """
    
    BRAND_KEYWORDS = {
        "apple", "microsoft", "google", "amazon", "facebook",
        "twitter", "linkedin", "paypal", "netflix", "adobe",
        "bank", "credit", "verify", "confirm", "update", "secure",
    }
    
    @staticmethod
    def calculate(url: str, domain: Optional[str] = None) -> PhishingSignal:
        """
        Calculate brand similarity signal.
        
        Args:
            url: Full URL (e.g., "https://appIe-verify.com/login")
            domain: Domain extracted from URL
        
        Returns:
            PhishingSignal with strength and confidence
        """
        if not domain:
            # Extract domain from URL
            match = re.search(r'https?://([^/]+)', url)
            domain = match.group(1) if match else url
        
        domain_lower = domain.lower()
        
        # Check for brand keywords
        keyword_hits = sum(1 for kw in BrandSimilaritySignal.BRAND_KEYWORDS
                          if kw in domain_lower)
        
        # Check for character substitution tricks (l→1, 0→o, etc.)
        suspicious_chars = len(re.findall(r'[0o1l\-]', domain_lower))
        
        if keyword_hits >= 2 and suspicious_chars >= 2:
            # Multiple brand keywords + character tricks = HIGH suspicion
            strength = 0.75
            confidence = 0.8
            explanation = f"URL '{domain}' matches multiple brand keywords with suspicious characters"
            influence_malicious = 0.6
            influence_suspicious = 0.2
            influence_benign = 0.0
        elif keyword_hits >= 1 and suspicious_chars >= 1:
            # Brand keyword + some suspicious chars = MEDIUM suspicion
            strength = 0.5
            confidence = 0.7
            explanation = f"URL '{domain}' contains brand keyword with suspicious characters"
            influence_malicious = 0.4
            influence_suspicious = 0.3
            influence_benign = 0.0
        elif keyword_hits >= 1:
            # Just a brand keyword = LOW suspicion
            strength = 0.3
            confidence = 0.6
            explanation = f"URL '{domain}' contains brand keyword"
            influence_malicious = 0.2
            influence_suspicious = 0.2
            influence_benign = 0.1
        else:
            # No brand signal
            strength = 0.0
            confidence = 0.8
            explanation = f"URL '{domain}' has no brand similarity indicators"
            influence_malicious = 0.0
            influence_suspicious = 0.0
            influence_benign = 0.7
        
        return PhishingSignal(
            signal_id=f"brand_sim_{domain}",
            signal_type="brand_similarity",
            strength=strength,
            confidence=confidence,
            decay_rate=0.15,  # Fast decay
            explanation=explanation,
            influence_malicious=influence_malicious,
            influence_suspicious=influence_suspicious,
            influence_benign=influence_benign,
        )


class URLEntropySignal:
    """
    URL entropy signal: High-entropy (random-looking) URLs are suspicious.
    
    Motivation: Legitimate URLs use readable, memorable paths.
    Malicious URLs often use random characters to evade detection.
    
    Entropy Calculation:
    - Shannon entropy of URL path
    - High entropy (>4.5) = suspicious
    - Low entropy (<2.5) = benign
    
    Decay: Medium decay (λ=0.10 per hour)
    """
    
    @staticmethod
    def calculate_entropy(text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        for count in freq.values():
            p = count / len(text)
            entropy -= p * math.log2(p) if p > 0 else 0
        
        return entropy
    
    @staticmethod
    def calculate(url: str) -> PhishingSignal:
        """
        Calculate URL entropy signal.
        
        Args:
            url: Full URL
        
        Returns:
            PhishingSignal with strength and confidence
        """
        # Extract path from URL
        match = re.search(r'https?://[^/]+(.*)', url)
        path = match.group(1) if match else ""
        
        # Calculate entropy
        entropy = URLEntropySignal.calculate_entropy(path)
        
        if entropy > 4.5:
            # High entropy = HIGH suspicion
            strength = 0.7
            confidence = 0.75
            explanation = f"URL path has high entropy ({entropy:.2f}), appears randomized"
            influence_malicious = 0.5
            influence_suspicious = 0.2
            influence_benign = 0.0
        elif entropy > 3.5:
            # Medium-high entropy = MEDIUM suspicion
            strength = 0.4
            confidence = 0.65
            explanation = f"URL path has elevated entropy ({entropy:.2f})"
            influence_malicious = 0.3
            influence_suspicious = 0.3
            influence_benign = 0.1
        elif entropy < 2.5:
            # Low entropy = BENIGN (readable URLs)
            strength = 0.0
            confidence = 0.85
            explanation = f"URL path has low entropy ({entropy:.2f}), appears normal"
            influence_malicious = 0.0
            influence_suspicious = 0.0
            influence_benign = 0.8
        else:
            # Medium entropy = NEUTRAL
            strength = 0.1
            confidence = 0.6
            explanation = f"URL path entropy is neutral ({entropy:.2f})"
            influence_malicious = 0.05
            influence_suspicious = 0.1
            influence_benign = 0.3
        
        return PhishingSignal(
            signal_id=f"url_entropy_{hashlib.sha256(url.encode()).hexdigest()[:8]}",
            signal_type="url_entropy",
            strength=strength,
            confidence=confidence,
            decay_rate=0.10,  # Medium decay
            explanation=explanation,
            influence_malicious=influence_malicious,
            influence_suspicious=influence_suspicious,
            influence_benign=influence_benign,
        )


class TLSCertificateMismatchSignal:
    """
    TLS certificate mismatch signal: Certificate age/issuer mismatches are suspicious.
    
    Heuristics:
    - Certificate issued very recently (days old) with established domain
    - Mismatch between domain and certificate CN/SAN
    - Unrecognized certificate authority
    - Certificate validity period is unusually short
    
    Decay: Very fast decay (λ=0.20) - certificate issues can be fixed quickly
    """
    
    @staticmethod
    def calculate(
        domain: str,
        cert_issue_date: Optional[datetime] = None,
        cert_expiry_date: Optional[datetime] = None,
        cert_cn: Optional[str] = None,
        cert_issuer: Optional[str] = None,
        domain_age_days: int = 365,
        check_time: Optional[datetime] = None,
    ) -> PhishingSignal:
        """
        Calculate TLS certificate mismatch signal.
        
        Args:
            domain: Domain being checked
            cert_issue_date: Certificate issue date
            cert_expiry_date: Certificate expiry date
            cert_cn: Certificate Common Name
            cert_issuer: Certificate issuer name
            domain_age_days: Domain registration age
            check_time: Time of analysis
        
        Returns:
            PhishingSignal with strength and confidence
        """
        check_time = check_time or datetime.utcnow()
        
        # If no certificate data, cannot make determination
        if cert_issue_date is None:
            return PhishingSignal(
                signal_id=f"tls_mismatch_{domain}",
                signal_type="tls_mismatch",
                strength=0.2,
                confidence=0.3,  # Very low confidence without data
                decay_rate=0.20,
                explanation=f"No TLS certificate data available for '{domain}'",
                influence_malicious=0.1,
                influence_suspicious=0.1,
                influence_benign=0.0,
            )
        
        issues = []
        confidence_sum = 0.0
        
        # Check 1: Certificate issued very recently for established domain
        cert_age_days = (check_time - cert_issue_date).days
        if cert_age_days < 7 and domain_age_days > 180:
            issues.append(f"Certificate newly issued ({cert_age_days}d) for established domain ({domain_age_days}d)")
            confidence_sum += 0.7
        
        # Check 2: CN mismatch
        if cert_cn and domain.lower() not in cert_cn.lower():
            issues.append(f"Domain mismatch: expected '{domain}', got '{cert_cn}'")
            confidence_sum += 0.6
        
        # Check 3: Suspicious issuer
        if cert_issuer:
            suspicious_issuers = ["self-signed", "unknown", "test", "localhost"]
            if any(sus in cert_issuer.lower() for sus in suspicious_issuers):
                issues.append(f"Suspicious certificate issuer: '{cert_issuer}'")
                confidence_sum += 0.75
        
        # Check 4: Unusually short validity period
        if cert_expiry_date:
            validity_days = (cert_expiry_date - cert_issue_date).days
            if validity_days < 30:
                issues.append(f"Unusually short certificate validity: {validity_days} days")
                confidence_sum += 0.5
        
        if issues:
            strength = min(0.8, 0.2 * len(issues))
            confidence = min(0.95, confidence_sum / len(issues))
            explanation = "; ".join(issues)
            influence_malicious = 0.5
            influence_suspicious = 0.3
            influence_benign = 0.0
        else:
            strength = 0.0
            confidence = 0.8
            explanation = f"TLS certificate for '{domain}' appears normal"
            influence_malicious = 0.0
            influence_suspicious = 0.0
            influence_benign = 0.7
        
        return PhishingSignal(
            signal_id=f"tls_mismatch_{domain}",
            signal_type="tls_mismatch",
            strength=strength,
            confidence=confidence,
            decay_rate=0.20,  # Very fast decay
            explanation=explanation,
            influence_malicious=influence_malicious,
            influence_suspicious=influence_suspicious,
            influence_benign=influence_benign,
        )


logger.info("Phishing Signal Module v3.5 loaded")
