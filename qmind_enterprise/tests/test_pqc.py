"""
Tests for Post-Quantum Cryptography module.
Tests real liboqs implementation of Kyber-768 and Dilithium-3.
"""
import pytest
import os
import logging
from pqc import _REAL_PQC_AVAILABLE
from pqc.hybrid_encryption import generate_keypair, encrypt, decrypt
from pqc.dilithium_sign import generate_keypair as dilithium_generate_keypair, sign, verify

logger = logging.getLogger(__name__)


class TestHybridEncryption:
    """Tests for Kyber-768 + AES-256-GCM hybrid encryption."""
    
    def test_generate_keypair_returns_two_bytes_objects(self):
        """Test that generate_keypair() returns two non-empty bytes objects."""
        if not _REAL_PQC_AVAILABLE:
            pytest.skip("liboqs not installed - skipping real PQC tests")
        
        public_key, secret_key = generate_keypair()
        
        assert isinstance(public_key, bytes)
        assert isinstance(secret_key, bytes)
        assert len(public_key) > 0
        assert len(secret_key) > 0
    
    def test_encrypt_decrypt_round_trip(self):
        """Test that decrypt(encrypt(pk, plaintext)) == plaintext."""
        if not _REAL_PQC_AVAILABLE:
            pytest.skip("liboqs not installed - skipping real PQC tests")
        
        public_key, secret_key = generate_keypair()
        plaintext = b"Hello, Post-Quantum World!"
        
        kem_ciphertext, iv, aes_ciphertext = encrypt(public_key, plaintext)
        decrypted = decrypt(secret_key, kem_ciphertext, iv, aes_ciphertext)
        
        assert decrypted == plaintext
    
    def test_hybrid_scheme_returns_3_tuple(self):
        """Test that hybrid scheme returns 3-tuple (kem_ct, iv, aes_ct) — never just 2."""
        if not _REAL_PQC_AVAILABLE:
            pytest.skip("liboqs not installed - skipping real PQC tests")
        
        public_key, secret_key = generate_keypair()
        plaintext = b"Test message"
        
        result = encrypt(public_key, plaintext)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        kem_ciphertext, iv, aes_ciphertext = result
        assert isinstance(kem_ciphertext, bytes)
        assert isinstance(iv, bytes)
        assert isinstance(aes_ciphertext, bytes)
        assert len(iv) == 12  # GCM nonce is 96 bits


class TestDilithiumSigning:
    """Tests for Dilithium-3 digital signatures."""
    
    def test_dilithium_generate_keypair_returns_two_bytes_objects(self):
        """Test that generate_keypair() returns two non-empty bytes objects."""
        if not _REAL_PQC_AVAILABLE:
            pytest.skip("liboqs not installed - skipping real PQC tests")
        
        public_key, secret_key = dilithium_generate_keypair()
        
        assert isinstance(public_key, bytes)
        assert isinstance(secret_key, bytes)
        assert len(public_key) > 0
        assert len(secret_key) > 0
    
    def test_dilithium_sign_verify_round_trip(self):
        """Test that verify(pk, msg, sign(sk, msg)) == True."""
        if not _REAL_PQC_AVAILABLE:
            pytest.skip("liboqs not installed - skipping real PQC tests")
        
        public_key, secret_key = dilithium_generate_keypair()
        message = b"Audit log entry for verification"
        
        signature = sign(secret_key, message)
        is_valid = verify(public_key, message, signature)
        
        assert is_valid is True
    
    def test_tampered_message_fails_verification(self):
        """Test that tampered message fails verification."""
        if not _REAL_PQC_AVAILABLE:
            pytest.skip("liboqs not installed - skipping real PQC tests")
        
        public_key, secret_key = dilithium_generate_keypair()
        original_message = b"Original audit log entry"
        tampered_message = b"Tampered audit log entry"
        
        signature = sign(secret_key, original_message)
        is_valid = verify(public_key, tampered_message, signature)
        
        assert is_valid is False


class TestPQCConfiguration:
    """Tests for PQC configuration and startup checks."""
    
    def test_use_real_pqc_false_logs_critical_warning(self, caplog):
        """Test that USE_REAL_PQC=false logs CRITICAL warning."""
        # This test verifies the logging behavior in __init__.py
        # The CRITICAL log is emitted when liboqs is not installed
        if _REAL_PQC_AVAILABLE:
            pytest.skip("liboqs is installed - cannot test missing liboqs behavior")
        
        # The CRITICAL log should have been emitted at import time
        # Check if it's in the logs
        critical_logs = [record for record in caplog.records if record.levelname == "CRITICAL"]
        assert any("liboqs not installed" in record.message for record in critical_logs)
    
    def test_real_pqc_available_flag(self):
        """Test that _REAL_PQC_AVAILABLE flag is correctly set."""
        # This just verifies the flag exists and is a boolean
        assert isinstance(_REAL_PQC_AVAILABLE, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
