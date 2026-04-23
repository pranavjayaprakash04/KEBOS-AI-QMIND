#!/usr/bin/env python3
import os
import sys

print("USE_REAL_PQC:", os.getenv("USE_REAL_PQC", "false"))

try:
    from pqc.hybrid_encryption import encrypt, decrypt, generate_keypair
    from pqc.dilithium_sign import sign, verify
    
    print("PQC modules loaded successfully")
    
    # Test hybrid encryption
    try:
        pub, priv = generate_keypair()
        print("Key generation: SUCCESS")
    except Exception as e:
        print(f"Key generation: {e}")
        print("Expected: liboqs not available (USE_REAL_PQC=false)")
    
    # Test signing
    try:
        data = b'test message'
        sig = sign(b'key', data)
        print(f"Signing: SUCCESS (signature length: {len(sig)} bytes)")
        
        # Verify signature
        if verify(b'key', data, sig):
            print("Signature verification: SUCCESS")
        else:
            print("Signature verification: FAILED")
    except Exception as e:
        print(f"Signing: {e}")
        
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
