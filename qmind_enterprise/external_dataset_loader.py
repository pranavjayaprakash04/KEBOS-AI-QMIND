from typing import List, Dict, Optional
import asyncio
import logging
from feeds.supplier_trust import (
    FeedSource,
    SupplierTrustEngine,
    get_supplier_trust_engine
)
from signal_engine.scorer import SignalScorer, ThreatCategory

logger = logging.getLogger(__name__)


class ExternalDatasetLoader:
    """
    Load and ingest data from 8 external feeds.
    Integrates with SupplierTrustEngine for trust scoring.
    """
    
    FEED_ENDPOINTS = {
        FeedSource.ABUSEIPDB: "https://api.abuseipdb.com/api/v2",
        FeedSource.FEODO: "https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
        FeedSource.MALWAREBAZAAR: "https://mb-api.abuse.ch/api/v1",
        FeedSource.NVD: "https://services.nvd.nist.gov/rest/json/cves/2.0",
        FeedSource.OPENPHISH: "https://openphish.com/feed.txt",
        FeedSource.PHISHTANK: "https://phishtank.org/api/v1/entries",
        FeedSource.URLHAUS: "https://urlhaus.abuse.ch/api/v1/urls",
        FeedSource.TRANCO: "https://tranco-list.eu/list/1000000/1000000",
    }
    
    def __init__(self):
        self.trust_engine = get_supplier_trust_engine()
        self.scorer = SignalScorer()
    
    async def load_feed(self, feed: FeedSource) -> List[Dict]:
        """Load indicators from a single feed, respecting SupplierTrustEngine quarantine."""
        logger.info(f"Loading feed: {feed.value}")

        # CRITICAL: Check quarantine status BEFORE loading any data
        weight = self.trust_engine.get_qmind_weight(feed.value)
        if weight == 0.0:
            logger.warning(
                f"Feed '{feed.value}' is QUARANTINED by SupplierTrustEngine. "
                f"Skipping entirely — using cached snapshot if available."
            )
            # Return cached snapshot signed by Dilithium-3 (if available)
            cached = self.trust_engine.get_cached_snapshot(feed.value)
            return cached if cached else []

        # Load indicators from feed
        raw_indicators = await self._fetch_from_feed(feed)

        # Apply trust weight to every indicator's confidence score
        weighted_indicators = []
        for indicator in raw_indicators:
            adjusted = dict(indicator)
            if 'confidence' in adjusted:
                adjusted['confidence'] = float(adjusted['confidence']) * weight
            adjusted['feed_weight'] = weight
            adjusted['feed_name'] = feed.value
            weighted_indicators.append(adjusted)

        logger.info(
            f"Feed '{feed.value}' loaded {len(weighted_indicators)} indicators "
            f"(weight={weight:.2f})"
        )
        return weighted_indicators

    async def _fetch_from_feed(self, feed: FeedSource) -> List[Dict]:
        """Fetch raw indicators from feed endpoint."""
        # TODO: Implement actual HTTP requests to feed endpoints
        # For scaffold, return empty list
        return []
    
    async def load_all_feeds(self) -> Dict[FeedSource, List[Dict]]:
        """
        Load indicators from all 8 feeds concurrently.
        Returns dict mapping feed to indicators.
        """
        logger.info("Loading all 8 external feeds")
        
        tasks = [
            self.load_feed(feed)
            for feed in FeedSource
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        feed_data = {}
        for feed, result in zip(FeedSource, results):
            if isinstance(result, Exception):
                logger.error(f"Error loading {feed.value}: {result}")
                self.trust_engine.update_uptime(feed, is_up=False)
                feed_data[feed] = []
            else:
                self.trust_engine.update_uptime(feed, is_up=True)
                feed_data[feed] = result
        
        return feed_data
    
    def get_qmind_weight(
        self,
        feed: FeedSource,
        category: ThreatCategory
    ) -> float:
        """
        Calculate QMind weight for a threat indicator.
        
        CRITICAL: Calls SupplierTrustEngine.get_qmind_weight() which returns 0.0
        for quarantined feeds. This ensures quarantine has actual effect.
        
        Factors:
        - Supplier trust score (with quarantine check)
        - Category-specific weighting
        - Feed historical performance
        """
        # CRITICAL: Use get_qmind_weight from trust engine to respect quarantine
        trust_weight = self.trust_engine.get_qmind_weight(feed.value)
        
        # If quarantined, weight is 0.0 - return immediately
        if trust_weight == 0.0:
            return 0.0
        
        # Category-specific weights (higher for more severe categories)
        category_weights = {
            ThreatCategory.C2_INFRASTRUCTURE: 1.2,
            ThreatCategory.SUPPLY_CHAIN: 1.2,
            ThreatCategory.INSIDER_THREAT: 1.2,
            ThreatCategory.CVE_EXPLOITATION: 1.1,
            ThreatCategory.BOTNET_IP: 1.0,
            ThreatCategory.MALWARE: 1.0,
            ThreatCategory.PHISHING: 0.9,
            ThreatCategory.CREDENTIAL_LEAK: 0.9,
            ThreatCategory.DDoS: 0.8,
            ThreatCategory.BENIGN: 0.5,
        }
        
        category_weight = category_weights.get(category, 1.0)
        
        # Combined weight
        qmind_weight = trust_weight * category_weight
        
        return min(max(qmind_weight, 0.0), 1.0)
    
    async def ingest_indicators(
        self,
        feed_data: Dict[FeedSource, List[Dict]]
    ) -> List[Dict]:
        """
        Ingest indicators from all feeds with QMind weight calculation.
        Returns enriched indicators ready for processing.
        
        CRITICAL: Skips quarantined feeds entirely - they do not contribute to scoring.
        """
        enriched_indicators = []
        
        for feed, indicators in feed_data.items():
            feed_name = feed.value
            
            # CRITICAL: Check if feed is quarantined before processing
            feed_weight = self.trust_engine.get_qmind_weight(feed_name)
            if feed_weight == 0.0:
                logger.warning(f"Feed '{feed_name}' is quarantined — skipping for QMind scoring")
                continue
            
            for indicator in indicators:
                # Determine category
                category_str = indicator.get("category", "Benign")
                try:
                    category = ThreatCategory(category_str)
                except ValueError:
                    category = ThreatCategory.BENIGN
                
                # Calculate QMind weight (includes feed quarantine check)
                qmind_weight = self.get_qmind_weight(feed, category)
                
                # Enrich indicator
                enriched = {
                    **indicator,
                    "feed_source": feed_name,
                    "supplier_trust": self.trust_engine.calculate_trust_score(feed),
                    "qmind_weight": qmind_weight,
                    "ingested_at": __import__('time').time()
                }
                
                enriched_indicators.append(enriched)
        
        logger.info(f"Ingested {len(enriched_indicators)} indicators from all feeds")
        return enriched_indicators


# Singleton instance
_loader_instance: Optional[ExternalDatasetLoader] = None


def get_dataset_loader() -> ExternalDatasetLoader:
    """Get or create the singleton ExternalDatasetLoader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ExternalDatasetLoader()
    return _loader_instance
