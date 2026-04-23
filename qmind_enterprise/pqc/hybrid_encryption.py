import os
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)

# Check USE_REAL_PQC before attempting to import oqs
USE_REAL_PQC = os.environ.get("USE_REAL_PQC", "false").lower() == "true"

# Import liboqs if available and USE_REAL_PQC is true
_LIBOQS_AVAILABLE = False
if USE_REAL_PQC:
    try:
        import oqs
        _LIBOQS_AVAILABLE = True
    except ImportError:
        logger.warning("liboqs not available - Kyber-768 hybrid encryption disabled")
else:
    logger.info("USE_REAL_PQC=false - skipping oqs import in hybrid_encryption")


def generate_keypair() -> tuple[bytes, bytes]:
    """Returns (public_key_bytes, secret_key_bytes)."""
    if not _LIBOQS_AVAILABLE:
        raise RuntimeError("liboqs not available - cannot generate Kyber-768 keypair")
    kem = oqs.KeyEncapsulation("Kyber768")
    public_key = kem.generate_keypair()
    return public_key, kem.export_secret_key()


def encrypt(public_key_bytes: bytes, plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    """
    HYBRID ENCRYPTION: Kyber-768 + AES-256-GCM.
    NEVER use Kyber alone — not NIST-certified standalone.
    Returns: (kem_ciphertext, iv, aes_ciphertext_with_tag)
    """
    if not _LIBOQS_AVAILABLE:
        raise RuntimeError("liboqs not available - cannot perform Kyber-768 encryption")
    kem = oqs.KeyEncapsulation("Kyber768")
    kem_ciphertext, shared_secret = kem.encap_secret(public_key_bytes)
    # Derive AES key from shared secret via HKDF
    aes_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"kebos-hybrid-v1"
    ).derive(shared_secret)
    # AES-256-GCM encrypt
    iv = os.urandom(12)
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)
    return (kem_ciphertext, iv, ciphertext)


def decrypt(secret_key_bytes: bytes, kem_ciphertext: bytes,
            iv: bytes, aes_ciphertext: bytes) -> bytes:
    if not _LIBOQS_AVAILABLE:
        raise RuntimeError("liboqs not available - cannot perform Kyber-768 decryption")
    kem = oqs.KeyEncapsulation("Kyber768", secret_key=secret_key_bytes)
    shared_secret = kem.decap_secret(kem_ciphertext)
    aes_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"kebos-hybrid-v1"
    ).derive(shared_secret)
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(iv, aes_ciphertext, None)
