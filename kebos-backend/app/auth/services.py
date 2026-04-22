import jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid
import redis.asyncio as redis
from app.config import settings
import bcrypt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class UserProfile:
    def __init__(
        self,
        id: int,
        username: str,
        email: Optional[str],
        role: str,
        tenant_id: int,
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
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # Startup assertion for token expiry
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 15, \
            "ACCESS_TOKEN_EXPIRE_MINUTES must be <= 15"
        
        # Load or generate RSA keys
        self._private_key = None
        self._public_key = None
    
    async def get_rsa_private_key(self) -> str:
        """Get RSA private key from Vault or env var"""
        if self._private_key:
            return self._private_key
        
        if settings.VAULT_PKI_ENABLED:
            # TODO: Implement Vault client to fetch from kebos/rsa-private-key
            pass
        
        if settings.VAULT_DEV_RSA_PRIVATE_KEY:
            self._private_key = settings.VAULT_DEV_RSA_PRIVATE_KEY
            return self._private_key
        
        # Generate a new RSA-4096 key pair for dev
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        self._private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        self._public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return self._private_key
    
    async def get_rsa_public_key(self) -> str:
        """Get RSA public key"""
        if self._public_key:
            return self._public_key
        
        # Derive from private key
        private_key_pem = await self.get_rsa_private_key()
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        self._public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return self._public_key
    
    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserProfile]:
        """Authenticate user with username/password"""
        # TODO: Implement actual DB lookup and password verification
        # For scaffold, return mock user
        if username == "admin" and password == "admin":
            return UserProfile(
                id=1,
                username="admin",
                email="admin@kebos.ai",
                role="ADMIN",
                tenant_id=1,
                tenant_type="enterprise",
                fido2_verified=True,
                fido2_enabled=True
            )
        if username == "gov_user" and password == "gov":
            return UserProfile(
                id=2,
                username="gov_user",
                email="gov@gov.in",
                role="ANALYST",
                tenant_id=2,
                tenant_type="government",
                fido2_verified=False,
                fido2_enabled=False  # Government user without FIDO2
            )
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
            
            # Check JTI blacklist
            jti = payload.get("jti")
            tenant_id = payload.get("tenant_id")
            if jti and tenant_id:
                blacklisted = await self.redis_client.exists(f"jti:{tenant_id}:{jti}")
                if blacklisted:
                    return None
            
            return payload
        except jwt.PyJWTError:
            return None
    
    async def logout_user(self, user: UserProfile, jti: str):
        """Blacklist the user's current JTI"""
        # Add JTI to Redis blacklist with 24h TTL
        await self.redis_client.setex(
            f"jti:{user.tenant_id}:{jti}",
            86400,  # 24 hours
            "1"
        )
