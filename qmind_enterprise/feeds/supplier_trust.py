from typing import Dict, Optional, List, Set
from dataclasses import dataclass
from enum import Enum
import time
import logging
from scipy.stats import ks_2samp

logger = logging.getLogger(__name__)


class FeedSource(Enum):
    """8 live external feed sources"""
    ABUSEIPDB = "abuseipdb"
    FEODO = "feodo"
    MALWAREBAZAAR = "malwarebazaar"
    NVD = "nvd"
    OPENPHISH = "openphish"
    PHISHTANK = "phishtank"
    URLHAUS = "urlhaus"
    TRANCO = "tranco"


@dataclass
class SupplierMetrics:
    """Metrics for calculating supplier trust score"""
    true_positives: int = 0
    false_positives: int = 0
    total_indicators: int = 0
    avg_response_time_ms: float = 0.0
    uptime_percentage: float = 100.0
    last_updated: float = 0.0
    scores: List[float] = None  # Historical confidence scores for anomaly detection
    mean_volume: float = 0.0  # Mean indicator volume for spike detection
    
    def __post_init__(self):
        if self.scores is None:
            self.scores = []


class SupplierTrustEngine:
    """
    Supplier trust scoring for 8 external feeds.
    Trust score is ACTIVE on all feeds at ALL times.
    Includes quarantine mechanism for anomalous feeds.
    """
    
    FEEDS = ['abuseipdb', 'feodo', 'malwarebazaar', 'nvd', 'openphish', 'phishtank', 'urlhaus', 'tranco']
    
    def __init__(self):
        # Initialize metrics for all feeds
        self.metrics: Dict[FeedSource, SupplierMetrics] = {
            feed: SupplierMetrics(last_updated=time.time())
            for feed in FeedSource
        }
        
        # Base trust scores (can be adjusted based on historical performance)
        self.base_trust_scores = {
            FeedSource.ABUSEIPDB: 0.85,
            FeedSource.FEODO: 0.82,
            FeedSource.MALWAREBAZAAR: 0.88,
            FeedSource.NVD: 0.90,
            FeedSource.OPENPHISH: 0.87,
            FeedSource.PHISHTANK: 0.85,
            FeedSource.URLHAUS: 0.80,
            FeedSource.TRANCO: 0.75,
        }
        
        # Trust scores for all feeds (dynamic)
        self.trust_scores: Dict[FeedSource, float] = {
            feed: self.base_trust_scores[feed]
            for feed in FeedSource
        }
        
        # Quarantined feeds
        self.quarantined: Set[FeedSource] = set()
        
        # Confirmed safe and threat IOCs for anomaly detection
        self.confirmed_safe: Set[str] = set()
        self.confirmed_threats: Set[str] = set()
        
        # Cached snapshots for quarantined feeds (feed_name -> list of indicators)
        self._snapshots: Dict[str, List[Dict]] = {}
        
        # Current data for each feed (feed_name -> list of indicators)
        self._current_data: Dict[str, List[Dict]] = {}
    
    def calculate_trust_score(self, feed: FeedSource) -> float:
        """
        Calculate dynamic trust score for a feed.
        
        Factors:
        - Base trust score (historical reputation)
        - Precision (TP / (TP + FP))
        - Response time (faster is better)
        - Uptime (higher is better)
        """
        metrics = self.metrics[feed]
        base_score = self.base_trust_scores[feed]
        
        # Precision score
        if metrics.true_positives + metrics.false_positives > 0:
            precision = metrics.true_positives / (
                metrics.true_positives + metrics.false_positives
            )
        else:
            precision = 0.8  # Default if no data
        
        # Response time score (normalize: <100ms = 1.0, >1000ms = 0.0)
        if metrics.avg_response_time_ms > 0:
            response_score = max(0, 1 - (metrics.avg_response_time_ms / 1000))
        else:
            response_score = 1.0
        
        # Uptime score
        uptime_score = metrics.uptime_percentage / 100.0
        
        # Weighted combination
        trust_score = (
            base_score * 0.4 +  # Historical reputation
            precision * 0.3 +   # Accuracy
            response_score * 0.15 +  # Performance
            uptime_score * 0.15  # Reliability
        )
        
        return min(max(trust_score, 0.0), 1.0)
    
    def record_true_positive(self, feed: FeedSource):
        """Record a true positive for a feed"""
        self.metrics[feed].true_positives += 1
        self.metrics[feed].total_indicators += 1
        self.metrics[feed].last_updated = time.time()
    
    def add_confirmed_threat(self, ioc: str):
        """Add IOC to confirmed threats set"""
        self.confirmed_threats.add(ioc)
    
    def add_confirmed_safe(self, ioc: str):
        """Add IOC to confirmed safe set"""
        self.confirmed_safe.add(ioc)
    
    def record_false_positive(self, feed: FeedSource):
        """Record a false positive for a feed"""
        self.metrics[feed].false_positives += 1
        self.metrics[feed].total_indicators += 1
        self.metrics[feed].last_updated = time.time()
    
    def update_response_time(self, feed: FeedSource, response_time_ms: float):
        """Update average response time for a feed"""
        metrics = self.metrics[feed]
        n = metrics.total_indicators
        if n > 0:
            # Running average
            metrics.avg_response_time_ms = (
                (metrics.avg_response_time_ms * (n - 1) + response_time_ms) / n
            )
        else:
            metrics.avg_response_time_ms = response_time_ms
    
    def update_uptime(self, feed: FeedSource, is_up: bool):
        """Update uptime percentage for a feed"""
        # Simplified: in production, would use proper time-weighted average
        metrics = self.metrics[feed]
        if is_up:
            metrics.uptime_percentage = min(metrics.uptime_percentage + 0.1, 100.0)
        else:
            metrics.uptime_percentage = max(metrics.uptime_percentage - 1.0, 0.0)
    
    def get_feed_trust_scores(self) -> Dict[FeedSource, float]:
        """Get current trust scores for all feeds"""
        return {
            feed: self.calculate_trust_score(feed)
            for feed in FeedSource
        }
    
    def get_low_trust_feeds(self, threshold: float = 0.5) -> list[FeedSource]:
        """Get feeds with trust score below threshold"""
        return [
            feed for feed, score in self.get_feed_trust_scores().items()
            if score < threshold
        ]
    
    def get_qmind_weight(self, feed_name: str) -> float:
        """
        Get QMind weight for a feed by name.
        
        CRITICAL: Returns 0.0 for quarantined feeds.
        This ensures quarantine has actual effect on scoring.
        
        Args:
            feed_name: String name of the feed (e.g., 'abuseipdb')
            
        Returns:
            float: Weight between 0.0 and 1.0. Returns 0.0 if feed is quarantined.
        """
        # Find FeedSource enum by name
        feed_source = None
        for feed in FeedSource:
            if feed.value == feed_name:
                feed_source = feed
                break
        
        if feed_source is None:
            logger.warning(f"Unknown feed name: {feed_name}, returning 0.0 weight")
            return 0.0
        
        # Check if feed is quarantined
        if feed_source in self.quarantined:
            logger.warning(f"Feed '{feed_name}' is quarantined, returning 0.0 weight")
            return 0.0
        
        # Return current trust score as weight
        return self.calculate_trust_score(feed_source)
    
    def quarantine_feed(self, feed_name: str):
        """
        Quarantine a feed by name.
        
        Args:
            feed_name: String name of the feed to quarantine
        """
        # Save current data as snapshot before quarantining
        if feed_name in self._current_data:
            self._snapshots[feed_name] = self._current_data[feed_name]
            logger.info(f"Cached snapshot saved for quarantined feed '{feed_name}'")
        
        for feed in FeedSource:
            if feed.value == feed_name:
                self.quarantined.add(feed)
                logger.warning(f"Feed '{feed_name}' quarantined — cached snapshot saved")
                return
        logger.warning(f"Unknown feed name: {feed_name}, cannot quarantine")
    
    def get_cached_snapshot(self, feed_name: str) -> list:
        """Return last known-good snapshot for quarantined feed."""
        return self._snapshots.get(feed_name, [])
    
    def set_current_data(self, feed_name: str, data: List[Dict]):
        """Set current data for a feed (used for snapshot caching)."""
        self._current_data[feed_name] = data
    
    def unquarantine_feed(self, feed_name: str):
        """
        Unquarantine a feed by name.
        
        Args:
            feed_name: String name of the feed to unquarantine
        """
        for feed in FeedSource:
            if feed.value == feed_name:
                self.quarantined.discard(feed)
                logger.info(f"Feed '{feed_name}' has been unquarantined")
                return
        logger.warning(f"Unknown feed name: {feed_name}, cannot unquarantine")


# Singleton instance
_trust_engine: Optional[SupplierTrustEngine] = None


def get_supplier_trust_engine() -> SupplierTrustEngine:
    """Get or create the singleton SupplierTrustEngine instance"""
    global _trust_engine
    if _trust_engine is None:
        _trust_engine = SupplierTrustEngine()
    return _trust_engine
