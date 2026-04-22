# Enhanced utility functions for logging, error handling, validation, and common operations
import logging
import os
import asyncio
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
import psutil
import platform

try:
    from .schemas import ValidationRequest, ValidationResponse, UtilityResponse, SystemInfo
    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False


# Configure logging with better structure
def setup_logging(service_name: str = "cyber_threat_platform") -> logging.Logger:
    """Setup logging configuration with proper formatting and levels."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Setup file handler
    log_dir = os.getenv("LOG_DIR", "./logs")
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"{service_name}_{datetime.now().strftime('%Y%m%d')}.log")
    )
    file_handler.setFormatter(formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Initialize logger
logger = setup_logging()


# Enhanced logging functions with structured data
def log_info(msg: str, **kwargs):
    """Log info message with optional context."""
    context = f" | {kwargs}" if kwargs else ""
    logger.info(f"{msg}{context}")


def log_error(msg: str, **kwargs):
    """Log error message with optional context."""
    context = f" | {kwargs}" if kwargs else ""
    logger.error(f"{msg}{context}")


def log_warning(msg: str, **kwargs):
    """Log warning message with optional context."""
    context = f" | {kwargs}" if kwargs else ""
    logger.warning(f"{msg}{context}")


def log_debug(msg: str, **kwargs):
    """Log debug message with optional context."""
    context = f" | {kwargs}" if kwargs else ""
    logger.debug(f"{msg}{context}")


# Async utility functions
async def async_retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Exceptions to catch and retry on
        
    Returns:
        Function result on success
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
                
        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                log_error(f"Function {func.__name__} failed after {max_retries} retries", error=str(e))
                raise e
            
            wait_time = delay * (backoff ** attempt)
            log_warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__} in {wait_time}s", error=str(e))
            await asyncio.sleep(wait_time)
    
    raise last_exception


async def async_timeout(func: Callable, timeout: float = 30.0) -> Any:
    """
    Execute an async function with a timeout.
    
    Args:
        func: Async function to execute
        timeout: Timeout in seconds
        
    Returns:
        Function result
        
    Raises:
        asyncio.TimeoutError: If function times out
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await asyncio.wait_for(func(), timeout=timeout)
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func),
                timeout=timeout
            )
    except asyncio.TimeoutError:
        log_error(f"Function {func.__name__} timed out after {timeout}s")
        raise


# Data validation utilities
def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format (IPv4 or IPv6)."""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?$'
    return bool(re.match(pattern, url))


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def sanitize_string(text: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Sanitize string input for security.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove or escape HTML if not allowed
    if not allow_html:
        import html
        text = html.escape(text)
    
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """
    Hash password with salt.
    
    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = os.urandom(32).hex()
    
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed.hex(), salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        hashed_password: Stored hash
        salt: Password salt
        
    Returns:
        True if password matches
    """
    test_hash, _ = hash_password(password, salt)
    return test_hash == hashed_password


# File utilities
def safe_file_path(filepath: str, base_dir: str = None) -> Path:
    """
    Ensure file path is safe and within base directory.
    
    Args:
        filepath: File path to validate
        base_dir: Base directory to restrict to
        
    Returns:
        Safe Path object
        
    Raises:
        ValueError: If path is unsafe
    """
    path = Path(filepath).resolve()
    
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise ValueError(f"Path {filepath} is outside base directory {base_dir}")
    
    # Check for dangerous patterns
    dangerous_patterns = ['..', '~', '$']
    for pattern in dangerous_patterns:
        if pattern in str(path):
            raise ValueError(f"Path contains dangerous pattern: {pattern}")
    
    return path


def get_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Calculate file hash.
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)
        
    Returns:
        Hex digest of file hash
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


# System utilities
def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.
    
    Returns:
        Dictionary containing system details
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        info = {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": memory.total,
            "memory_available": memory.available,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_free": disk.free,
            "disk_percent": (disk.used / disk.total) * 100,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return info
        
    except Exception as e:
        log_error(f"Error getting system info: {e}")
        return {"error": str(e)}


def check_disk_space(path: str = "/", min_free_gb: float = 1.0) -> Dict[str, Any]:
    """
    Check available disk space.
    
    Args:
        path: Path to check
        min_free_gb: Minimum free space in GB
        
    Returns:
        Dictionary with disk space information
    """
    try:
        disk = psutil.disk_usage(path)
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
        free_percent = (disk.free / disk.total) * 100
        
        return {
            "path": path,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "free_percent": round(free_percent, 2),
            "percent_used": round((disk.used / disk.total) * 100, 2),
            "has_sufficient_space": free_gb >= min_free_gb,
            "sufficient_space": free_gb >= min_free_gb,
            "min_required_gb": min_free_gb
        }
    except Exception as e:
        log_error(f"Error checking disk space for {path}: {e}")
        return {"error": str(e)}


# Configuration utilities
def load_config_from_env(prefix: str = "CTP_") -> Dict[str, str]:
    """
    Load configuration from environment variables with prefix.
    
    Args:
        prefix: Environment variable prefix
        
    Returns:
        Dictionary of configuration values
    """
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            config[config_key] = value
    
    return config


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> List[str]:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required keys
        
    Returns:
        List of missing keys
    """
    missing_keys = []
    
    for key in required_keys:
        if key not in config or config[key] is None:
            missing_keys.append(key)
    
    return missing_keys


# JSON utilities
def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        log_warning(f"Failed to parse JSON: {e}")
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely serialize object to JSON.
    
    Args:
        obj: Object to serialize
        default: Default JSON string if serialization fails
        
    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(obj, default=str, indent=2)
    except (TypeError, ValueError) as e:
        log_warning(f"Failed to serialize to JSON: {e}")
        return default


# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def check_rate_limit(self, key: str, max_requests: int = None, window_seconds: int = None) -> bool:
        """Check if request is allowed for given key (async version)."""
        max_req = max_requests or self.max_requests
        window_sec = window_seconds or self.window_seconds
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_sec)
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
        else:
            self.requests[key] = []
        
        # Check if under limit
        if len(self.requests[key]) < max_req:
            self.requests[key].append(now)
            return True
        
        return False
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
        else:
            self.requests[key] = []
        
        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False
        
        return False
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if key not in self.requests:
            return self.max_requests
        
        recent_requests = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(recent_requests))


# Error handling utilities
class CommonError(Exception):
    """Base exception class for common module."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "COMMON_ERROR"
        self.details = details or {}
        super().__init__(message)


class ValidationError(CommonError):
    """Validation error exception."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {"field": field, "value": str(value)} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details)


class ConfigurationError(CommonError):
    """Configuration error exception."""
    
    def __init__(self, message: str, missing_keys: List[str] = None):
        details = {"missing_keys": missing_keys} if missing_keys else {}
        super().__init__(message, "CONFIGURATION_ERROR", details)


def handle_error(error: Exception, component: str = "", details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Handle and format error for API responses.
    
    Args:
        error: Exception to handle
        component: Component where error occurred  
        details: Additional error details
        
    Returns:
        Error information dictionary
    """
    error_info = {
        "status": "error",
        "error_type": type(error).__name__,
        "message": str(error),
        "component": component,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        error_info["details"] = details
    
    if isinstance(error, CommonError):
        error_info.update({
            "error_code": error.error_code,
            "details": {**(error_info.get("details", {})), **(error.details or {})}
        })
    
    log_error(f"Error in {component}: {error}", error_type=type(error).__name__)
    
    return error_info


# Generate unique identifiers
def generate_trace_id() -> str:
    """Generate unique trace ID for request tracking."""
    return str(uuid.uuid4())


def generate_api_key() -> str:
    """Generate secure API key."""
    return hashlib.sha256(os.urandom(32)).hexdigest()


def generate_session_id() -> str:
    """Generate secure session ID."""
    return hashlib.sha256(f"{uuid.uuid4()}{datetime.utcnow()}".encode()).hexdigest()[:32]


# Cache utilities (simple in-memory cache)
class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        # Check TTL
        if key in self.timestamps:
            if datetime.utcnow().timestamp() - self.timestamps[key] > self.default_ttl:
                await self.delete(key)
                return None
        
        return self.cache[key]
    
    def get_sync(self, key: str) -> Any:
        """Get value from cache (synchronous version)."""
        if key not in self.cache:
            return None
        
        # Check TTL
        if key in self.timestamps:
            if datetime.utcnow().timestamp() - self.timestamps[key] > self.default_ttl:
                self.delete_sync(key)
                return None
        
        return self.cache[key]
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache."""
        self.cache[key] = value
        self.timestamps[key] = datetime.utcnow().timestamp()
    
    def set_sync(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache (synchronous version)."""
        self.cache[key] = value
        self.timestamps[key] = datetime.utcnow().timestamp()
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def delete_sync(self, key: str) -> None:
        """Delete value from cache (synchronous version)."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
    
    def clear_sync(self) -> None:
        """Clear all cache entries (synchronous version)."""
        self.cache.clear()
        self.timestamps.clear()
    
    async def size(self) -> int:
        """Get cache size."""
        return len(self.cache)
    
    def size_sync(self) -> int:
        """Get cache size (synchronous version)."""
        return len(self.cache)


# Initialize global cache instance
cache = SimpleCache()

# Initialize global rate limiter instance
rate_limiter = RateLimiter()
