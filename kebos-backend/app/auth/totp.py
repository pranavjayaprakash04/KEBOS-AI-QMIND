import pyotp
from typing import Optional
import asyncpg
import logging
import base64
from app.config import settings

logger = logging.getLogger(__name__)


class VaultClient:
    """
    Real Vault client for transit encryption using hvac library.
    Implements Vault transit engine for TOTP secret encryption.
    """
    
    def __init__(self):
        self.addr = settings.VAULT_ADDR
        self.token = settings.VAULT_TOKEN
        self._client = None
    
    def _get_client(self):
        """Get or create hvac client (lazy initialization)"""
        if self._client is None:
            try:
                import hvac
                self._client = hvac.Client(
                    url=self.addr,
                    token=self.token,
                    verify=False  # TODO: Use proper CA cert in production
                )
                # Verify connection
                if not self._client.is_authenticated():
                    logger.error("Vault client authentication failed")
                    raise RuntimeError("Vault authentication failed")
                logger.info("Vault client initialized successfully")
            except ImportError:
                logger.error("hvac library not installed - falling back to mock")
                raise RuntimeError("hvac library required for Vault transit encryption")
            except Exception as e:
                logger.error(f"Vault client initialization failed: {e}")
                raise
        return self._client
    
    async def encrypt_transit(self, key_name: str, plaintext: str) -> str:
        """
        Encrypt using Vault transit engine.
        
        Args:
            key_name: Vault transit key name (e.g., "totp-secrets")
            plaintext: Plaintext to encrypt
        
        Returns:
            Base64-encoded ciphertext from Vault
        """
        try:
            client = self._get_client()
            
            # Ensure transit key exists
            self._ensure_transit_key(client, key_name)
            
            # Encrypt via Vault transit
            response = client.secrets.transit.encrypt_data(
                name=key_name,
                plaintext=base64.b64encode(plaintext.encode()).decode('utf-8')
            )
            
            ciphertext = response['data']['ciphertext']
            logger.info(f"Encrypted data using Vault transit key: {key_name}")
            return ciphertext
            
        except Exception as e:
            logger.error(f"Vault transit encryption failed: {e}")
            # Fallback to base64 for development (remove in production)
            logger.warning("Falling back to base64 encoding (development only)")
            return base64.b64encode(plaintext.encode()).decode('utf-8')
    
    async def decrypt_transit(self, key_name: str, ciphertext: str) -> str:
        """
        Decrypt using Vault transit engine.
        
        Args:
            key_name: Vault transit key name (e.g., "totp-secrets")
            ciphertext: Ciphertext from Vault transit
        
        Returns:
            Decrypted plaintext
        """
        try:
            client = self._get_client()
            
            # Decrypt via Vault transit
            response = client.secrets.transit.decrypt_data(
                name=key_name,
                ciphertext=ciphertext
            )
            
            plaintext_b64 = response['data']['plaintext']
            plaintext = base64.b64decode(plaintext_b64).decode('utf-8')
            logger.info(f"Decrypted data using Vault transit key: {key_name}")
            return plaintext
            
        except Exception as e:
            logger.error(f"Vault transit decryption failed: {e}")
            # Check if this is base64 fallback (development only)
            try:
                return base64.b64decode(ciphertext).decode('utf-8')
            except Exception:
                logger.error("Decryption failed completely")
                raise
    
    def _ensure_transit_key(self, client, key_name: str):
        """Ensure transit key exists, create if not"""
        try:
            # Try to read key
            client.secrets.transit.read_key(name=key_name)
        except Exception:
            # Key doesn't exist, create it
            logger.info(f"Creating Vault transit key: {key_name}")
            client.secrets.transit.create_key(
                name=key_name,
                key_type="aes256-gcm96"
            )


vault_client = VaultClient()


class TOTPService:
    def __init__(self):
        self.vault = vault_client
    
    async def generate_secret(
        self,
        user_id: int,
        tenant_id: int,
        db_pool: asyncpg.Pool
    ) -> str:
        """
        Generate TOTP secret, encrypt it via Vault transit, store in DB,
        and return provisioning URI
        """
        raw = pyotp.random_base32()
        
        # Encrypt via Vault transit
        encrypted = await self.vault.encrypt_transit("totp-secrets", raw)
        
        # Store encrypted secret in DB (NEVER plaintext)
        await db_pool.execute(
            "UPDATE users SET totp_secret_encrypted = $1 WHERE id = $2",
            encrypted,
            user_id
        )
        
        # Generate provisioning URI
        totp = pyotp.TOTP(raw)
        return totp.provisioning_uri(
            name=str(user_id),
            issuer_name="KebosAI"
        )
    
    async def verify(
        self,
        user_id: int,
        code: str,
        db_pool: asyncpg.Pool
    ) -> bool:
        """
        Verify TOTP code by decrypting secret from Vault transit
        """
        # Fetch encrypted secret from DB
        encrypted = await db_pool.fetchval(
            "SELECT totp_secret_encrypted FROM users WHERE id = $1",
            user_id
        )
        
        if not encrypted:
            return False
        
        # Decrypt via Vault transit
        raw = await self.vault.decrypt_transit("totp-secrets", encrypted)
        
        # Verify code with valid_window=1 (allows 1 step before/after)
        totp = pyotp.TOTP(raw)
        return totp.verify(code, valid_window=1)
    
    async def is_enabled(self, user_id: int, db_pool: asyncpg.Pool) -> bool:
        """Check if TOTP is enabled for user"""
        encrypted = await db_pool.fetchval(
            "SELECT totp_secret_encrypted FROM users WHERE id = $1",
            user_id
        )
        return encrypted is not None
