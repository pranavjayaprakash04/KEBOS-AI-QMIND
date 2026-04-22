"""
Post-Quantum Cryptography module for QMind Enterprise.
Implements Kyber-768 (FIPS 203) and Dilithium-3 (FIPS 204) using liboqs.
"""
import logging
import sys

logger = logging.getLogger(__name__)

# Try to import oqs, but handle the case where shared library is not available
_REAL_PQC_AVAILABLE = False
try:
    import oqs
    # Try to access oqs to verify shared library is loaded
    try:
        _ = oqs.get_enabled_kem_mechanisms()
        _REAL_PQC_AVAILABLE = True
    except (RuntimeError, Exception) as e:
        logger.critical(
            f"liboqs shared library not available — PQC is DISABLED. "
            f"Error: {e}. "
            "Install liboqs shared library or set USE_REAL_PQC=false."
        )
except ImportError:
    logger.critical(
        "liboqs-python not installed — PQC is DISABLED. "
        "Install: pip install liboqs-python. "
        "Set USE_REAL_PQC=false until installed."
    )
