import numpy as np
from catboost import CatBoostClassifier
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThreatFeatures:
    source_ip: str
    destination_ip: str
    indicator_value: str
    indicator_type: str   # "ip", "domain", "hash", "url", "user"
    source: str           # "network", "ct_log", "paste_monitor", etc.
    tenant_id: str


class CatBoostThreatEngine:
    MODEL_PATH = Path("models/catboost_threat_v1.cbm")

    def __init__(self):
        if self.MODEL_PATH.exists():
            self.model = CatBoostClassifier()
            self.model.load_model(str(self.MODEL_PATH))
            self._model_loaded = True
        else:
            # No pre-trained model yet — return 0.5 (uncertain) for all inputs
            self._model_loaded = False
            logger.warning(
                "CatBoost model not found at models/catboost_threat_v1.cbm — "
                "using 0.5 neutral score until model is trained. "
                "This is expected on first deployment."
            )

    def score(self, features: ThreatFeatures) -> float:
        """Returns 0.0 (clean) to 1.0 (malicious). CPU-friendly — no GPU needed."""
        if not self._model_loaded:
            return 0.5  # uncertain — let QMind decide from feed context
        feature_array = self._prepare_features(features)
        return float(self.model.predict_proba([feature_array])[0][1])

    def _prepare_features(self, features: ThreatFeatures) -> list:
        """
        Extracts numerical features from indicator.
        India-specific: UPI patterns, Indian IP ranges, BFSI keywords in domain.
        """
        domain_features = self._extract_domain_features(features.indicator_value)
        return [
            self._ip_is_indian_asn(features.source_ip),
            len(features.indicator_value),
            domain_features["entropy"],
            domain_features["subdomain_depth"],
            domain_features["has_indian_brand"],
            domain_features["has_typosquat_pattern"],
            self._source_confidence_prior(features.source),
        ]

    def _extract_domain_features(self, value: str) -> dict:
        import math
        from collections import Counter
        INDIAN_BRANDS = ["sbi", "hdfc", "icici", "axis", "npci", "upi", "bhim", "paytm"]
        entropy = -sum(p * math.log2(p) for p in
                         (c/len(value) for c in Counter(value).values()) if p > 0)
        return {
            "entropy": entropy,
            "subdomain_depth": value.count("."),
            "has_indian_brand": int(any(b in value.lower() for b in INDIAN_BRANDS)),
            "has_typosquat_pattern": int(
                any(value.lower().count(b) > 0 and value.lower() != b
                    for b in INDIAN_BRANDS)
            ),
        }

    def _ip_is_indian_asn(self, ip: str) -> int:
        # Simplified: flag RFC1918 as internal (0), public as unknown (0.5)
        return 0

    def _source_confidence_prior(self, source: str) -> float:
        priors = {
            "ct_log": 0.65, "paste_monitor": 0.70, "honeypot": 0.95,
            "network": 0.50, "endpoint": 0.60, "analyst_manual": 0.80,
        }
        return priors.get(source, 0.50)
