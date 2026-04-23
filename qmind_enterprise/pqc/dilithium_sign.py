import os
import logging

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
        logger.warning("liboqs not available - Dilithium-3 signing disabled")
else:
    logger.info("USE_REAL_PQC=false - skipping oqs import in dilithium_sign")


def generate_keypair() -> tuple[bytes, bytes]:
    """Returns (public_key_bytes, secret_key_bytes)."""
    if not _LIBOQS_AVAILABLE:
        raise RuntimeError("liboqs not available - cannot generate Dilithium-3 keypair")
    signer = oqs.Signature("Dilithium3")
    public_key = signer.generate_keypair()
    return public_key, signer.export_secret_key()


def sign(secret_key_bytes: bytes, message: bytes) -> bytes:
    if not _LIBOQS_AVAILABLE:
        raise RuntimeError("liboqs not available - cannot perform Dilithium-3 signing")
    signer = oqs.Signature("Dilithium3", secret_key=secret_key_bytes)
    return signer.sign(message)


def verify(public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
    if not _LIBOQS_AVAILABLE:
        raise RuntimeError("liboqs not available - cannot perform Dilithium-3 verification")
    verifier = oqs.Signature("Dilithium3")
    return verifier.verify(message, signature, public_key_bytes)
