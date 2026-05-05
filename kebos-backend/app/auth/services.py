import jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid
import redis.asyncio as redis
from app.config import settings
import bcrypt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Module-level RSA key singleton - generated once at import time
_RSA_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
_PRIVATE_KEY_PEM = _RSA_PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
_PUBLIC_KEY_PEM = _RSA_PRIVATE_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)


class UserProfile:
    def __init__(
        self,
        id: str,  # UUID as string
        username: str,
        email: Optional[str],
        role: str,
        tenant_id: str,  # UUID as string
        tenant_type: str = "enterprise",
        fido2_verified: bool = False,
        fido2_enabled: bool = False,
        jti: Optional[str] = None
    ):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.tenant_id = tenant_id
        self.tenant_type = tenant_type
        self.fido2_verified = fido2_verified
        self.fido2_enabled = fido2_enabled
        self.jti = jti


class AuthService:
    def __init__(self):
        # Initialize Redis client for token blacklist
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Redis client initialization failed: {e}")
            self.redis_client = None
        
        # Startup assertion for token expiry
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 15, \
            "ACCESS_TOKEN_EXPIRE_MINUTES must be <= 15"
    
    async def get_rsa_private_key(self) -> str:
        """Get RSA private key from module-level singleton"""
        if settings.VAULT_DEV_RSA_PRIVATE_KEY:
            return settings.VAULT_DEV_RSA_PRIVATE_KEY
        return _PRIVATE_KEY_PEM
    
    async def get_rsa_public_key(self) -> str:
        """Get RSA public key from module-level singleton"""
        return _PUBLIC_KEY_PEM
    
    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserProfile]:
        """Authenticate user with username/password (demo credentials — replace with DB lookup)"""
        import logging
        logger = logging.getLogger(__name__)

        if username == "admin" and password == "admin123":
            return UserProfile(
                id="0838c1ce-8874-4885-92b5-38735a990f4a",
                username="admin",
                email="admin@kebos.local",
                role="admin",
                tenant_id="0838c1ce-8874-4885-92b5-38735a990f4a",
                tenant_type="enterprise",
                fido2_verified=False,
                fido2_enabled=False
            )
        if username == "gov_user" and password == "gov":
            return UserProfile(
                id="1b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
                username="gov_user",
                email="gov@gov.in",
                role="ANALYST",
                tenant_id="1b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
                tenant_type="government",
                fido2_verified=False,
                fido2_enabled=False
            )
        logger.warning("Authentication failed for a user")
        return None
    
    async def create_access_token(self, user: UserProfile) -> str:
        """Create RS256 JWT token"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = str(uuid.uuid4())

        payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "tenant_type": user.tenant_type,
            "fido2_enabled": getattr(user, 'fido2_enabled', False),
            "jti": jti,
            "iat": now.timestamp(),
            "exp": expire.timestamp()
        }

        private_key = await self.get_rsa_private_key()
        return jwt.encode(payload, private_key, algorithm="RS256")
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verify RS256 JWT token"""
        try:
            public_key = await self.get_rsa_public_key()
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"]
            )
            
            # Check JTI blacklist (skip if redis_client is None for dev mode)
            jti = payload.get("jti")
            if jti and self.redis_client:
                blacklisted = await self.redis_client.exists(f"blacklist:{jti}")
                if blacklisted:
                    return None
            
            return payload
        except jwt.PyJWTError:
            return None
    
    async def logout_user(self, user: UserProfile, jti: str, exp: int = None):
        """Blacklist the user's current JTI"""
        if not self.redis_client:
            return
        
        # Calculate TTL based on token expiry (default to 15 minutes if not provided)
        if exp:
            ttl = max(0, exp - int(datetime.utcnow().timestamp()))
        else:
            ttl = 900  # 15 minutes default
        
        if ttl > 0:
            await self.redis_client.setex(
                f"blacklist:{jti}",
                ttl,
                "1"
            )

    async def create_challenge_token(
        self,
        user_id: str,
        tenant_id: str,
        jti: str,
        expires_minutes: int = 5
    ) -> str:
        """Create a short-lived challenge token for TOTP verification using RS256"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=expires_minutes)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "jti": jti,
            "type": "challenge",
            "iat": now.timestamp(),
            "exp": expire.timestamp()
        }

        private_key = await self.get_rsa_private_key()
        return jwt.encode(payload, private_key, algorithm="RS256")

    async def decode_challenge_token(self, token: str) -> dict:
        """Decode and verify a challenge token using RS256"""
        try:
            public_key = await self.get_rsa_public_key()
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"]
            )
            if payload.get("type") != "challenge":
                raise ValueError("Not a challenge token")
            return payload
        except jwt.PyJWTError:
            raise ValueError("Invalid challenge token")
