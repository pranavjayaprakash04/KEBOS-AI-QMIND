import logging

logger = logging.getLogger(__name__)

# Import liboqs if available
try:
    import oqs
    _LIBOQS_AVAILABLE = True
except ImportError:
    _LIBOQS_AVAILABLE = False
    logger.warning("liboqs not available - Dilithium-3 signing disabled")


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
