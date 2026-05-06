"""
Run inside the qmind container:
docker compose exec qmind python test_pqc.py
All checks must print PASS.
"""
import sys

def test_oqs_import():
    try:
        import oqs
        print(f"PASS — liboqs import OK, KEMs: {oqs.get_enabled_KEMs()[:3]}")
    except ImportError as e:
        print(f"FAIL — liboqs not installed: {e}")
        print("      Set USE_REAL_PQC=false and redeploy if demo is urgent.")
        sys.exit(1)

def test_kyber_roundtrip():
    from qmind_enterprise.pqc.hybrid_encryption import generate_keypair, encrypt, decrypt
    pk, sk = generate_keypair()
    ct_kem, iv, ct_aes = encrypt(pk, b"IAF_2026_TEST")
    pt = decrypt(sk, ct_kem, iv, ct_aes)
    assert pt == b"IAF_2026_TEST", f"Decrypt mismatch: {pt}"
    print("PASS — Kyber-768 + AES-256-GCM round-trip OK")

def test_dilithium_sign():
    from qmind_enterprise.pqc.dilithium_sign import generate_keypair, sign, verify
    pk, sk = generate_keypair()
    msg = b"audit_test_entry"
    sig = sign(sk, msg)
    assert verify(pk, msg, sig), "Signature verification failed"
    print("PASS — Dilithium-3 sign + verify OK")

if __name__ == "__main__":
    print("=== PQC Verification Suite ===")
    test_oqs_import()
    test_kyber_roundtrip()
    test_dilithium_sign()
    print("=== All PQC checks passed ===")
