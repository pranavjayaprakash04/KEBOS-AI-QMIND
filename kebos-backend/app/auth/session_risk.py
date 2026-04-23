from fastapi import Request
from typing import Optional
from dataclasses import dataclass
import redis.asyncio as redis
import json
import math
import logging
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SessionRiskResult:
    score: float  # 0.0 to 1.0
    action: str  # "allow", "step_up_auth", "lock"
    reason: Optional[str] = None


class SessionRiskScorer:
    """
    Scores session risk based on:
    - Impossible travel (haversine distance / time_delta > 900km/h)
    - Device fingerprint changes
    """
    
    def __init__(self, redis_client, geoip_db_path: str = ""):
        self.redis_client = redis_client
        self._geoip_reader = None
        self._geoip_warned = False
        if geoip_db_path:
            try:
                import geoip2.database
                self._geoip_reader = geoip2.database.Reader(geoip_db_path)
                logger.info(f"GeoIP database loaded: {geoip_db_path}")
            except Exception as e:
                logger.warning(f"GeoIP database failed to load ({e}) — impossible travel disabled")
        else:
            logger.warning(
                "GEOIP_DB_PATH not set — impossible travel detection is DISABLED. "
                "Download GeoLite2-City.mmdb from maxmind.com and set GEOIP_DB_PATH."
            )
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate haversine distance between two lat/lon points in km"""
        R = 6371  # Earth radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    async def _get_previous_session(
        self,
        user_id: int,
        tenant_id: int
    ) -> Optional[dict]:
        """Get previous session data from Redis"""
        key = f"session:{tenant_id}:{user_id}"
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def _store_session(
        self,
        user_id: int,
        tenant_id: int,
        lat: Optional[float],
        lon: Optional[float],
        fingerprint: str
    ):
        """Store current session data in Redis with 24h TTL"""
        key = f"session:{tenant_id}:{user_id}"
        data = {
            "lat": lat,
            "lon": lon,
            "fingerprint": fingerprint,
            "timestamp": math.floor(__import__('time').time())
        }
        await self.redis_client.setex(
            key,
            86400,  # 24 hours
            json.dumps(data)
        )
    
    def _extract_location(self, ip: str) -> tuple[float, float]:
        """
        Returns (latitude, longitude) for an IP address.
        Returns (0.0, 0.0) if GeoIP is not configured (disables distance check).
        """
        if not self._geoip_reader:
            return 0.0, 0.0
        # Skip private/local IPs
        import ipaddress
        try:
            if ipaddress.ip_address(ip).is_private:
                return 0.0, 0.0
        except ValueError:
            return 0.0, 0.0
        try:
            record = self._geoip_reader.city(ip)
            lat = record.location.latitude or 0.0
            lon = record.location.longitude or 0.0
            return float(lat), float(lon)
        except Exception:
            return 0.0, 0.0
    
    def _extract_fingerprint(self, request: Request) -> str:
        """
        Extract device fingerprint from request headers.
        For scaffold, uses user-agent - in production would use more sophisticated fingerprinting
        """
        user_agent = request.headers.get("user-agent", "unknown")
        # TODO: Add more fingerprinting factors (screen resolution, timezone, etc.)
        return user_agent
    
    async def _lock_and_inject_threat(
        self,
        user_id: int,
        tenant_id: int,
        reason: str
    ):
        """
        Lock account and inject threat signal to QMind
        """
        # TODO: Lock user account
        # TODO: Inject threat to /signals/inject with confidence=0.9, category=Insider_Threat
        # This will be implemented in Phase 2
        pass
    
    async def score(
        self,
        request: Request,
        user_id: int,
        tenant_id: int
    ) -> SessionRiskResult:
        """
        Score session risk based on request context
        """
        # Get current location and fingerprint
        client_ip = request.client.host if request.client else ""
        lat, lon = self._extract_location(client_ip)
        fingerprint = self._extract_fingerprint(request)
        
        # Get previous session
        previous = await self._get_previous_session(user_id, tenant_id)
        
        if not previous:
            # First login - no baseline, allow
            await self._store_session(user_id, tenant_id, lat, lon, fingerprint)
            return SessionRiskResult(score=0.0, action="allow")
        
        # Check impossible travel
        if lat and lon and previous.get("lat") and previous.get("lon"):
            distance = self._haversine_distance(
                previous["lat"], previous["lon"],
                lat, lon
            )
            
            current_time = math.floor(__import__('time').time())
            time_delta_hours = (current_time - previous.get("timestamp", current_time)) / 3600
            
            if time_delta_hours > 0:
                speed_kmh = distance / time_delta_hours
                
                # Impossible travel: > 900 km/h
                if speed_kmh > 900:
                    await self._lock_and_inject_threat(
                        user_id, tenant_id,
                        f"Impossible travel detected: {speed_kmh:.0f} km/h"
                    )
                    return SessionRiskResult(
                        score=1.0,
                        action="lock",
                        reason=f"Impossible travel: {speed_kmh:.0f} km/h"
                    )
        
        # Check device fingerprint change
        if previous.get("fingerprint") != fingerprint:
            # New device - require step-up auth
            await self._store_session(user_id, tenant_id, lat, lon, fingerprint)
            return SessionRiskResult(
                score=0.5,
                action="step_up_auth",
                reason="New device detected"
            )
        
        # Store current session
        await self._store_session(user_id, tenant_id, lat, lon, fingerprint)
        
        return SessionRiskResult(score=0.0, action="allow")
