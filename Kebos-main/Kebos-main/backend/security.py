"""
Security configuration and utilities for the AI CTP Platform.
"""
import os
import re
import secrets
from typing import List, Optional
from pathlib import Path

# Security constants
MIN_SECRET_KEY_LENGTH = 32
ALLOWED_FILE_EXTENSIONS = {'.pkl', '.joblib', '.h5', '.onnx', '.pb', '.pt', '.pth'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_PROMPT_LENGTH = 10 * 1024  # 10KB

def validate_secret_key(key: str) -> bool:
    """Validate that the secret key meets security requirements."""
    if not key:
        return False
    if len(key) < MIN_SECRET_KEY_LENGTH:
        return False
    # Check for sufficient entropy
    if len(set(key)) < len(key) * 0.5:
        return False
    return True

def generate_secure_secret_key() -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(32)

def validate_filename(filename: str) -> str:
    """Validate and sanitize filename to prevent path traversal attacks."""
    if not filename:
        raise ValueError("Filename is required")
    
    # Remove any path separators and normalize
    safe_filename = os.path.basename(filename)
    
    # Check for valid file extensions
    file_ext = Path(safe_filename).suffix.lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}")
    
    # Additional validation: only alphanumeric, dots, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9._-]+$', safe_filename):
        raise ValueError("Filename contains invalid characters")
    
    return safe_filename

def validate_file_size(content: bytes) -> bool:
    """Validate file size against maximum allowed size."""
    return len(content) <= MAX_FILE_SIZE

def validate_prompt(prompt: str) -> str:
    """Validate and sanitize prompt input."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ValueError(f"Prompt too long (max {MAX_PROMPT_LENGTH} characters)")
    
    return prompt.strip()

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def validate_origin(origin: str, allowed_origins: List[str]) -> bool:
    """Validate if an origin is in the allowed list."""
    return origin in allowed_origins

def get_security_headers() -> dict:
    """Get recommended security headers."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    }

def validate_environment() -> List[str]:
    """Validate that all required environment variables are set and secure."""
    errors = []
    
    # Check required variables
    required_vars = [
        "SECRET_KEY",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate secret key
    secret_key = os.getenv("SECRET_KEY")
    if secret_key and not validate_secret_key(secret_key):
        errors.append("SECRET_KEY does not meet security requirements")
    
    # Validate CORS origins
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    if not any(origin.strip() for origin in allowed_origins):
        errors.append("ALLOWED_ORIGINS must be configured")
    
    return errors 