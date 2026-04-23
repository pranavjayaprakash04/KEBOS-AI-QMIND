"""
Dependency Health Monitor - Graceful degradation policies

Continuously monitors dependency health and implements graceful degradation
when dependencies fail. Prevents silent failures.
"""
import logging
from typing import Dict, Optional, Callable
from enum import Enum
import asyncio
from app.integrations.egress_control import EgressControlledClient
from app.config import settings

logger = logging.getLogger(__name__)


class DependencyStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class DegradationPolicy:
    """Defines how to handle dependency failures"""
    
    def __init__(
        self,
        name: str,
        fallback: Optional[Callable] = None,
        silent_fail: bool = False,
        timeout_ms: int = 5000
    ):
        self.name = name
        self.fallback = fallback
        self.silent_fail = silent_fail
        self.timeout_ms = timeout_ms


class DependencyHealthMonitor:
    """
    Monitors dependency health and implements graceful degradation.
    
    Dependencies monitored:
    - PostgreSQL
    - Kafka
    - QMind
    - Vault
    - Redis
    - AbuseIPDB (feed)
    - Groq (SOC reports)
    - CertStream (CT monitoring)
    - Cloudflare (CDN)
    
    For each dependency:
    - Run health check every 30s
    - If DOWN: apply degradation policy
    - If DEGRADED: log warning
    - On recovery: restore normal settings
    """
    
    def __init__(self):
        self._running = False
        self._health_status: Dict[str, DependencyStatus] = {}
        self._degradation_policies: Dict[str, DegradationPolicy] = {}
        self._client = EgressControlledClient(timeout=5.0)
        
        # Degradation state persistence
        self.max_confidence_cap: float = 1.0  # Normal cap
        self.soc_report_mode: str = "normal"  # normal or jinja2_only
        self.read_only_mode: bool = False
        self.qmind_transport: str = "kafka"  # kafka or http
        self.rate_limit_backend: str = "redis"  # redis or db
        self.ct_monitor_mode: str = "certstream"  # certstream or whoisxml_fallback
        
        # Track previous state for recovery
        self._previous_health_status: Dict[str, DependencyStatus] = {}
        
        # Register degradation policies
        self._register_default_policies()
    
    def _register_default_policies(self):
        """Register default degradation policies for dependencies"""
        self._degradation_policies["postgres"] = DegradationPolicy(
            name="postgres",
            silent_fail=False  # PostgreSQL is critical
        )
        
        self._degradation_policies["kafka"] = DegradationPolicy(
            name="kafka",
            silent_fail=True  # Kafka can fail silently, signals queued locally
        )
        
        self._degradation_policies["qmind"] = DegradationPolicy(
            name="qmind",
            silent_fail=True,  # QMind can fail silently, fall back to static rules
            fallback=lambda: 0.5  # Default confidence score
        )
        
        self._degradation_policies["vault"] = DegradationPolicy(
            name="vault",
            silent_fail=False  # Vault is critical for secrets
        )
        
        self._degradation_policies["redis"] = DegradationPolicy(
            name="redis",
            silent_fail=True  # Redis can fail silently, fall back to in-memory
        )
        
        self._degradation_policies["abuseipdb"] = DegradationPolicy(
            name="abuseipdb",
            silent_fail=True  # Single feed can fail, continue with 7 others
        )
        
        self._degradation_policies["groq"] = DegradationPolicy(
            name="groq",
            silent_fail=True  # SOC reports can queue for retry
        )
        
        self._degradation_policies["certstream"] = DegradationPolicy(
            name="certstream",
            silent_fail=True  # Can fall back to WhoisXML
        )
        
        self._degradation_policies["cloudflare"] = DegradationPolicy(
            name="cloudflare",
            silent_fail=True  # Can go direct-to-origin
        )
    
    async def start(self):
        """Start continuous health monitoring"""
        if self._running:
            return
        
        self._running = True
        logger.info("Starting Dependency Health Monitor")
        
        # Start background task
        task = asyncio.create_task(self._monitor_loop())
        task.add_done_callback(lambda t: logger.info("Dependency health monitor task completed"))
    
    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        await self._client.aclose()
        logger.info("Dependency Health Monitor stopped")
    
    async def _monitor_loop(self):
        """Continuous health check loop"""
        while self._running:
            await self._check_all_dependencies()
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _check_all_dependencies(self):
        """Check health of all registered dependencies and apply degradation policies"""
        for dep_name in self._degradation_policies.keys():
            previous_status = self._health_status.get(dep_name, DependencyStatus.HEALTHY)
            status = await self._check_dependency(dep_name)
            self._health_status[dep_name] = status
            
            # Apply degradation policy on status change
            if status != previous_status:
                if status == DependencyStatus.DOWN:
                    self._apply_degradation_policy(dep_name)
                elif previous_status == DependencyStatus.DOWN and status == DependencyStatus.HEALTHY:
                    self._restore_from_degradation(dep_name)
            
            if status == DependencyStatus.DOWN:
                policy = self._degradation_policies[dep_name]
                if not policy.silent_fail:
                    logger.error(f"Critical dependency {dep_name} is DOWN")
                else:
                    logger.warning(f"Dependency {dep_name} is DOWN, using fallback")
    
    async def _check_dependency(self, dep_name: str) -> DependencyStatus:
        """Check health of a specific dependency"""
        try:
            if dep_name == "postgres":
                return await self._check_postgres()
            elif dep_name == "kafka":
                return await self._check_kafka()
            elif dep_name == "qmind":
                return await self._check_qmind()
            elif dep_name == "vault":
                return await self._check_vault()
            elif dep_name == "redis":
                return await self._check_redis()
            elif dep_name == "abuseipdb":
                return await self._check_abuseipdb()
            elif dep_name == "groq":
                return await self._check_groq()
            elif dep_name == "certstream":
                return await self._check_certstream()
            elif dep_name == "cloudflare":
                return await self._check_cloudflare()
            else:
                return DependencyStatus.UNKNOWN
        except Exception as e:
            logger.error(f"Health check failed for {dep_name}: {e}")
            return DependencyStatus.DOWN
    
    async def _check_postgres(self) -> DependencyStatus:
        """Check PostgreSQL health"""
        try:
            from app.main import app
            if not hasattr(app.state, 'db_pool'):
                return DependencyStatus.DOWN
            
            async with app.state.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            return DependencyStatus.HEALTHY
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_kafka(self) -> DependencyStatus:
        """Check Kafka health"""
        try:
            # Try to connect to Kafka
            response = await self._client.get(f"http://kafka:9092")
            if response.status_code == 200:
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_qmind(self) -> DependencyStatus:
        """Check QMind health"""
        try:
            response = await self._client.get("http://qmind:8001/health")
            if response.status_code == 200:
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_vault(self) -> DependencyStatus:
        """Check Vault health"""
        try:
            response = await self._client.get(f"http://{settings.VAULT_ADDR}/v1/sys/health")
            if response.status_code == 200:
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_redis(self) -> DependencyStatus:
        """Check Redis health"""
        try:
            response = await self._client.get(f"http://redis:6379/ping")
            if response.status_code == 200:
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_abuseipdb(self) -> DependencyStatus:
        """Check AbuseIPDB feed health"""
        try:
            response = await self._client.get("https://api.abuseipdb.com/api/v2/check")
            if response.status_code in [200, 401, 403]:  # API is up even if auth fails
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_groq(self) -> DependencyStatus:
        """Check Groq API health"""
        try:
            response = await self._client.get("https://api.groq.com/openai/v1/models")
            if response.status_code in [200, 401]:
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_certstream(self) -> DependencyStatus:
        """Check CertStream health"""
        try:
            response = await self._client.get("https://certstream.calidog.io/")
            if response.status_code == 200:
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    async def _check_cloudflare(self) -> DependencyStatus:
        """Check Cloudflare health"""
        try:
            response = await self._client.get("https://1.1.1.1/")
            if response.status_code == 200:
                return DependencyStatus.HEALTHY
            return DependencyStatus.DOWN
        except Exception:
            return DependencyStatus.DOWN
    
    def _apply_degradation_policy(self, dep_name: str):
        """
        Apply degradation policy when a dependency goes down.
        Policies persist until the dependency recovers.
        """
        DEGRADED_POLICIES = {
            "abuseipdb_down": lambda: logger.warning("AbuseIPDB down — continuing with 7 remaining feeds, reduced confidence"),
            "all_feeds_down": lambda: setattr(self, 'max_confidence_cap', 0.65),
            "groq_down": lambda: setattr(self, 'soc_report_mode', 'jinja2_only'),
            "vault_down": lambda: setattr(self, 'read_only_mode', True),
            "kafka_down": lambda: setattr(self, 'qmind_transport', 'http'),
            "redis_down": lambda: setattr(self, 'rate_limit_backend', 'db'),
            "qmind_down": lambda: setattr(self, 'max_confidence_cap', 0.60),
            "certstream_down": lambda: setattr(self, 'ct_monitor_mode', 'whoisxml_fallback'),
            "cloudflare_down": lambda: logger.warning("Cloudflare down — direct-to-origin active"),
        }
        
        policy_key = f"{dep_name}_down"
        if policy_key in DEGRADED_POLICIES:
            logger.warning(f"Applying degradation policy for {dep_name}")
            DEGRADED_POLICIES[policy_key]()
    
    def _restore_from_degradation(self, dep_name: str):
        """
        Restore normal settings when a dependency recovers.
        """
        logger.info(f"Dependency {dep_name} recovered — restoring normal settings")
        
        # Restore settings based on which dependency recovered
        if dep_name == "all_feeds" or dep_name == "qmind":
            self.max_confidence_cap = 1.0
        elif dep_name == "groq":
            self.soc_report_mode = "normal"
        elif dep_name == "vault":
            self.read_only_mode = False
        elif dep_name == "kafka":
            self.qmind_transport = "kafka"
        elif dep_name == "redis":
            self.rate_limit_backend = "redis"
        elif dep_name == "certstream":
            self.ct_monitor_mode = "certstream"
        
        # Special case: check if all feeds are back up
        feed_deps = ["abuseipdb"]
        all_feeds_healthy = all(
            self._health_status.get(dep) == DependencyStatus.HEALTHY
            for dep in feed_deps
        )
        if all_feeds_healthy and self.max_confidence_cap == 0.65:
            self.max_confidence_cap = 1.0
            logger.info("All feeds recovered — restored max_confidence_cap to 1.0")
    
    def get_health_status(self) -> Dict[str, DependencyStatus]:
        """Get current health status of all dependencies"""
        return self._health_status.copy()
    
    def is_healthy(self) -> bool:
        """Check if all critical dependencies are healthy"""
        for dep_name, status in self._health_status.items():
            policy = self._degradation_policies.get(dep_name)
            if policy and not policy.silent_fail and status != DependencyStatus.HEALTHY:
                return False
        return True
    
    def check_all_feeds_status(self) -> bool:
        """Check if all feed dependencies are down"""
        feed_deps = ["abuseipdb"]
        return all(
            self._health_status.get(dep) == DependencyStatus.DOWN
            for dep in feed_deps
        )
    
    async def execute_with_fallback(self, dep_name: str, func: Callable, *args, **kwargs):
        """
        Execute a function with fallback if dependency is down.
        
        If dependency is DOWN and has a fallback, use fallback.
        If dependency is DOWN and silent_fail is False, raise exception.
        """
        status = self._health_status.get(dep_name, DependencyStatus.HEALTHY)
        policy = self._degradation_policies.get(dep_name)
        
        if status == DependencyStatus.HEALTHY:
            return await func(*args, **kwargs)
        
        if status == DependencyStatus.DOWN:
            if policy and policy.fallback:
                logger.info(f"Using fallback for {dep_name}")
                return policy.fallback()
            
            if policy and not policy.silent_fail:
                raise Exception(f"Critical dependency {dep_name} is DOWN")
            
            logger.warning(f"Dependency {dep_name} is DOWN, skipping silently")
            return None


# Singleton instance
_dependency_monitor: Optional[DependencyHealthMonitor] = None


def get_dependency_health_monitor() -> DependencyHealthMonitor:
    """Get or create the singleton DependencyHealthMonitor instance"""
    global _dependency_monitor
    if _dependency_monitor is None:
        _dependency_monitor = DependencyHealthMonitor()
    return _dependency_monitor
