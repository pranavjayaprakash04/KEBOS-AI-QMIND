"""
UEBA Baseline Engine - User and Entity Behavior Analytics

Builds behavioural profiles for users based on API request patterns.
Uses Welford online algorithm for efficient baseline computation.
Detects anomalies using Mahalanobis distance.

Patent Claim 3: Server-side behavioural biometrics via API request graph
"""
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import numpy as np
from fastapi import Request
from app.integrations.egress_control import EgressControlledClient
import geoip2.database
import geoip2.errors
from app.config import settings

logger = logging.getLogger(__name__)

# Module-level reader — opened once, thread-safe for reads
_geoip_reader: geoip2.database.Reader | None = None


def _get_geoip_reader() -> geoip2.database.Reader | None:
    global _geoip_reader
    if _geoip_reader is None:
        try:
            _geoip_reader = geoip2.database.Reader(settings.GEOIP_DB_PATH)
            logger.info(f"GeoIP database loaded: {settings.GEOIP_DB_PATH}")
        except FileNotFoundError:
            logger.warning(
                f"GeoLite2-City.mmdb not found at {settings.GEOIP_DB_PATH}. "
                f"Run scripts/download_geoip.sh to enable impossible-travel detection."
            )
    return _geoip_reader


class UEBABaselineEngine:
    """
    UEBA Baseline Engine for behavioral anomaly detection.
    
    Tracks features:
    - hour_of_day
    - day_of_week
    - source_ip
    - endpoint
    - request_size_bytes
    - user_agent
    
    Uses Welford online algorithm for incremental mean/variance computation.
    Computes Mahalanobis distance for anomaly detection.
    """
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self.egress_client = EgressControlledClient(timeout=10.0)
    
    async def update_baseline(self, user_id: str, tenant_id: str, request: Request):
        """
        Called on every authenticated request to build behavioural profile.
        Updates baseline and checks for anomalies.
        """
        features = self._extract_features(request)
        
        # Store event
        await self._store_event(user_id, tenant_id, features)
        
        # Compute anomaly score
        score = await self._compute_anomaly_score(user_id, tenant_id, features)
        
        # Inject signal if anomaly detected
        if score > 0.8:
            await self._inject_insider_threat_signal(user_id, tenant_id, score, features)
            logger.warning(f"UEBA anomaly detected for user {user_id}: score={score:.2f}")
    
    def _extract_features(self, request: Request) -> Dict[str, Any]:
        """Extract features from request for baseline tracking"""
        return {
            "hour_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday(),
            "source_ip": request.client.host if request.client else "unknown",
            "endpoint": request.url.path,
            "request_size_bytes": int(request.headers.get("content-length", 0)),
            "user_agent": request.headers.get("user-agent", ""),
        }

    def _extract_location(self, ip: str) -> tuple[float, float]:
        """
        Return (latitude, longitude) for an IP using MaxMind GeoLite2.
        Returns (0.0, 0.0) only if:
          - IP is private/loopback (expected — not a bug)
          - GeoLite2-City.mmdb is not installed (warns once at startup)
          - IP is not in the database (edge case)
        """
        import ipaddress
        try:
            parsed = ipaddress.ip_address(ip)
            if parsed.is_private or parsed.is_loopback or parsed.is_reserved:
                return (0.0, 0.0)  # Private IPs legitimately have no geo
        except ValueError:
            logger.debug(f"_extract_location: invalid IP '{ip}'")
            return (0.0, 0.0)

        reader = _get_geoip_reader()
        if reader is None:
            return (0.0, 0.0)  # DB not installed — warning already logged at startup

        try:
            response = reader.city(ip)
            lat = float(response.location.latitude or 0.0)
            lon = float(response.location.longitude or 0.0)
            logger.debug(f"GeoIP: {ip} → ({lat:.4f}, {lon:.4f}) [{response.city.name}]")
            return (lat, lon)
        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"GeoIP: {ip} not in database")
            return (0.0, 0.0)
        except Exception as e:
            logger.error(f"GeoIP lookup error for {ip}: {e}")
            return (0.0, 0.0)
    
    async def _store_event(self, user_id: str, tenant_id: str, features: Dict[str, Any]):
        """Store UEBA event in database"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO ueba_events (user_id, tenant_id, features)
                    VALUES ($1, $2, $3)
                    """,
                    user_id, tenant_id, json.dumps(features)
                )
        except Exception as e:
            logger.error(f"Failed to store UEBA event: {e}")
    
    async def _compute_anomaly_score(self, user_id: str, tenant_id: str, current: Dict[str, Any]) -> float:
        """
        Compute anomaly score using Welford online algorithm and Mahalanobis distance.
        
        Returns 0.0 if baseline has insufficient samples (< 50).
        """
        if not self.db_pool:
            return 0.0
        
        try:
            async with self.db_pool.acquire() as conn:
                # Fetch baseline
                baseline = await conn.fetchrow(
                    """
                    SELECT mean_features, variance_features, sample_count
                    FROM ueba_baselines
                    WHERE user_id = $1 AND tenant_id = $2
                    """,
                    user_id, tenant_id
                )
                
                if not baseline or baseline['sample_count'] < 50:
                    # No false positives during ramp-up
                    return 0.0
                
                # Update baseline with new data point (Welford online algorithm)
                await self._update_baseline_welford(user_id, tenant_id, current, baseline)
                
                # Compute Mahalanobis distance
                return self._mahalanobis_distance(current, baseline)
                
        except Exception as e:
            logger.error(f"Failed to compute anomaly score: {e}")
            return 0.0
    
    async def _update_baseline_welford(
        self,
        user_id: str,
        tenant_id: str,
        current: Dict[str, Any],
        baseline: Dict[str, Any]
    ):
        """
        Update baseline using Welford online algorithm.
        Computes incremental mean and variance without storing all data.
        """
        n = baseline['sample_count']
        mean_features = baseline['mean_features']
        variance_features = baseline['variance_features']
        
        # Update mean and variance for each feature
        new_mean = {}
        new_variance = {}
        
        for key, value in current.items():
            old_mean = mean_features.get(key, 0.0)
            old_variance = variance_features.get(key, 0.0)
            
            # Welford online algorithm
            delta = value - old_mean
            new_mean_val = old_mean + delta / (n + 1)
            new_variance_val = old_variance + delta * (value - new_mean_val) / (n + 1)
            
            new_mean[key] = new_mean_val
            new_variance[key] = new_variance_val
        
        # Update database
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO ueba_baselines (user_id, tenant_id, mean_features, variance_features, sample_count, last_updated)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        mean_features = EXCLUDED.mean_features,
                        variance_features = EXCLUDED.variance_features,
                        sample_count = EXCLUDED.sample_count + 1,
                        last_updated = NOW()
                    """,
                    user_id, tenant_id, json.dumps(new_mean), json.dumps(new_variance), n + 1
                )
        except Exception as e:
            logger.error(f"Failed to update baseline: {e}")
    
    def _mahalanobis_distance(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> float:
        """
        Compute Mahalanobis distance between current observation and baseline.
        
        Higher distance = more anomalous.
        Returns normalized score between 0 and 1.
        """
        try:
            mean_features = baseline['mean_features']
            variance_features = baseline['variance_features']
            
            # Convert to numpy arrays
            current_values = np.array([float(current[k]) for k in mean_features.keys()])
            mean_values = np.array([float(mean_features[k]) for k in mean_features.keys()])
            var_values = np.array([float(variance_features[k]) for k in variance_features.keys()])
            
            # Avoid division by zero
            var_values = np.maximum(var_values, 1e-6)
            
            # Compute Mahalanobis distance
            diff = current_values - mean_values
            inv_cov = np.diag(1.0 / var_values)
            mahalanobis = np.sqrt(diff @ inv_cov @ diff)
            
            # Normalize to 0-1 range (using sigmoid)
            normalized_score = 1 / (1 + np.exp(-0.5 * (mahalanobis - 2)))
            
            return float(normalized_score)
            
        except Exception as e:
            logger.error(f"Failed to compute Mahalanobis distance: {e}")
            return 0.0
    
    async def _inject_insider_threat_signal(
        self,
        user_id: str,
        tenant_id: str,
        score: float,
        features: Dict[str, Any]
    ):
        """
        Inject insider threat signal to QMind for analysis.
        """
        try:
            signal = {
                "indicator_value": str(user_id),
                "indicator_type": "user",
                "source": "ueba",
                "confidence": min(0.95, score),
                "metadata": {
                    "ueba_score": score,
                    "anomalous_features": features,
                    "tenant_id": tenant_id
                }
            }
            
            response = await self.egress_client.post(
                "http://qmind:8001/signals/inject",
                json=signal
            )
            response.raise_for_status()
            
            logger.info(f"Injected UEBA signal for user {user_id} with score {score:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to inject UEBA signal: {e}")


# Singleton instance
_ueba_engine: Optional[UEBABaselineEngine] = None


def get_ueba_engine(db_pool=None) -> UEBABaselineEngine:
    """Get or create the singleton UEBA engine instance"""
    global _ueba_engine
    if _ueba_engine is None:
        _ueba_engine = UEBABaselineEngine(db_pool)
    return _ueba_engine
