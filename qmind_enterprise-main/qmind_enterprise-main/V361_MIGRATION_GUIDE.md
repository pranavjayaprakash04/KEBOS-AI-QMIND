"""
================================================================================
Q-MIND ENTERPRISE v3.6.1 - MIGRATION GUIDE & DEPLOYMENT HANDBOOK
================================================================================

Document: V361_MIGRATION_GUIDE.md
Status: DEPLOYMENT-READY
Version: 1.0
Date: January 25, 2026

================================================================================
QUICK START: v3.6 → v3.6.1 UPGRADE
================================================================================

ESTIMATED TIME: 2-4 hours (testing + deployment)


STEP 1: PRE-DEPLOYMENT CHECKLIST
────────────────────────────────

[ ] Review PQC_ARCHITECTURE_V361.md (this document assumes familiarity)
[ ] Backup existing v3.6 deployment
[ ] Notify security/compliance team
[ ] Schedule maintenance window (if required)
[ ] Identify test environment(s)


STEP 2: TESTING IN STAGING
──────────────────────────

  2a. Deploy v3.6.1 code to staging:
      
      git clone https://github.com/qmind/qmind-enterprise.git
      cd qmind_enterprise
      git checkout v3.6.1
      
  2b. Install dependencies:
      
      pip install -r requirements.txt
      # Also install liboqs for production (not in requirements for now):
      # pip install liboqs-python
      
  2c. Configure environment:
      
      export QMIND_ENV=staging
      export QMIND_PQC_ENABLED=true
      export QMIND_MASTER_KEY_SEED=$(openssl rand -hex 32)
      
  2d. Run full test suite:
      
      cd qmind_enterprise
      python -m pytest tests/test_v361_crypto.py -v
      
      Expected output:
      ✓ TestCryptoAbstractionLayer (all tests pass)
      ✓ TestHybridKeyEstablishment (all tests pass)
      ✓ TestDilithiumSignatures (all tests pass)
      ✓ TestIntegratedV361Encryption (all tests pass)
      ✓ TestBackwardCompatibility (all tests pass)
      ✓ TestPerformanceImpact (overhead < 10%)
      ✓ TestMetadataAuditability (metadata complete)
      
      Total: 40+ tests, 0 failures
      
  2e. Verify backward compatibility with v3.6 artifacts:
      
      python tests/test_backward_compat.py -v
      
      Expected: All v3.6 artifacts decrypt successfully
      
  2f. Run performance benchmarks:
      
      python tests/benchmark_v361.py
      
      Expected: <10% throughput degradation vs v3.6
      
  2g. Check crypto status report:
      
      python -c "
      from qmind_enterprise.crypto.enterprise_encryption_v3_6_1 import EnterpriseEncryptionV361
      enc = EnterpriseEncryptionV361(enable_pqc=True)
      import json
      print(json.dumps(enc.get_crypto_status(), indent=2))
      "
      
      Expected output shows:
      {
        \"version\": \"v3.6.1\",
        \"pqc_enabled\": true,
        \"crypto_profile\": {...},
        \"timestamp\": ...
      }


STEP 3: VALIDATE IN PRODUCTION-LIKE ENVIRONMENT
────────────────────────────────────────────────

  3a. Deploy to pre-production with PQC enabled:
      
      # Similar to step 2, but with prod-like config
      export QMIND_ENV=pre-production
      
  3b. Run extended soak test (4-8 hours):
      
      python tests/soak_test_v361.py --duration 8h
      
      Monitors:
      - Encryption/decryption correctness
      - Signature generation/verification
      - Memory usage stability
      - CPU usage patterns
      - No memory leaks
      
  3c. Inspect audit logs:
      
      # All crypto operations should be logged with metadata
      # Check that metadata shows:
      # - data_encryption: "AES-256-GCM"
      # - key_exchange: "Hybrid-Kyber-HKDF"
      # - signature: "CRYSTALS-Dilithium-3"
      # - nist_profile: "2024-2025"
      
      grep -l "nist_profile" /var/log/qmind/*.log
      
  3d. Verify no regressions vs v3.6:
      
      # Run same workload on v3.6 and v3.6.1
      # Compare results (should be identical for data operations)


STEP 4: GRADUAL PRODUCTION ROLLOUT
──────────────────────────────────

  STRATEGY: Canary deployment (5% → 25% → 50% → 100%)

  4a. Deploy v3.6.1 to 5% of production instances:
      
      kubectl set image deployment/qmind-api \
        qmind-api=qmind:v3.6.1 \
        --record
      
      Monitor:
      - Error rates (should be 0)
      - Latency p95 (should be <10% increase)
      - Signature verification success rate (should be 100%)
      - Memory usage (should be stable)
      
  4b. After 1 hour, expand to 25%:
      
      kubectl patch deployment qmind-api \
        -p '{"spec":{"replicas": 4}}'  # 1 of 4 is canary
      
  4c. After 4 hours, expand to 50%
  
  4d. After 8 hours, full rollout to 100%


STEP 5: POST-DEPLOYMENT VALIDATION
──────────────────────────────────

  5a. Generate compliance report:
      
      python tools/generate_compliance_report.py --version v3.6.1
      
      Report should document:
      - NIST PQC alignment (FIPS 203, 204)
      - Crypto algorithms used
      - Security assumptions
      - Threat model coverage
      
  5b. Audit all encrypted artifacts:
      
      # Sample: Extract metadata from 1000 random artifacts
      python tools/audit_metadata.py --sample 1000
      
      Expected:
      - 100% have metadata
      - 100% show AES-256-GCM for data encryption
      - 100% show Hybrid-Kyber-HKDF or classical (backward compat)
      - 100% show NIST profile marker
      
  5c. Verify signature coverage:
      
      python tools/verify_signature_coverage.py --entity-types all
      
      Check coverage for:
      - Threat reports: 100% signed
      - Audit logs: 100% signed
      - Feedback artifacts: 100% signed
      - Model updates: 100% signed
      
  5d. Check key rotation schedule:
      
      python tools/check_key_rotation.py
      
      Expected:
      - Keys rotated on schedule (default 90 days)
      - Old key versions retained for verification
      - No key reuse across contexts


================================================================================
CONFIGURATION OPTIONS
================================================================================

ENVIRONMENT VARIABLES:

  QMIND_ENV
    Values: development | staging | production
    Default: production
    Purpose: Deployment environment for context binding

  QMIND_PQC_ENABLED
    Values: true | false
    Default: true
    Purpose: Enable/disable PQC features (graceful fallback)

  QMIND_MASTER_KEY_SEED
    Values: hex-encoded 32-byte value
    Default: (must be provided)
    Purpose: Master seed for key derivation (never in code!)

  QMIND_KEY_ROTATION_DAYS
    Values: 1-365
    Default: 90
    Purpose: Key rotation frequency

  QMIND_SIGNATURE_ALGORITHM
    Values: dilithium | classical
    Default: dilithium
    Purpose: Select signature algorithm

  QMIND_LOG_CRYPTO_OPERATIONS
    Values: true | false
    Default: true
    Purpose: Log all crypto operations (for audit)


CONFIGURATION FILE (config.yaml):

  crypto:
    version: v3.6.1
    pqc_enabled: true
    data_encryption:
      algorithm: AES-256-GCM
      key_size_bits: 256
    key_establishment:
      algorithm: Hybrid-Kyber-HKDF
      kyber_enabled: true
      fallback_to_classical: true
    signatures:
      algorithm: CRYSTALS-Dilithium-3
      verify_all_artifacts: true
    key_rotation:
      enabled: true
      interval_days: 90
      retain_old_keys_days: 30
    audit:
      log_all_operations: true
      include_metadata: true


DEPLOYMENT PATTERNS:

  Pattern 1: Backward Compatible (v3.6 + v3.6.1 coexistence)
  ─────────────────────────────────────────────────────────
  
    Scenario: Gradual migration, support both versions
    
    Configuration:
    • PQC_ENABLED=true
    • Kyber graceful fallback enabled
    • Accept both signed and unsigned artifacts
    
    Behavior:
    • New artifacts encrypted with Kyber + AES
    • Old artifacts still decrypt with AES
    • Signatures verified where present
    • Full backward compatibility

  Pattern 2: Full PQC (v3.6.1 only)
  ──────────────────────────────────
  
    Scenario: Full migration, v3.6 sunset
    
    Configuration:
    • PQC_ENABLED=true
    • Require signatures on all artifacts
    • Reject unsigned artifacts (optional)
    
    Behavior:
    • All new data encrypted with Hybrid-Kyber
    • All artifacts signed with Dilithium
    • No v3.6 support required
    • Maximum quantum-safety

  Pattern 3: Hybrid Support (Mixed environments)
  ──────────────────────────────────────────────
  
    Scenario: Different environments have different capabilities
    
    Configuration (production):
    • PQC_ENABLED=true
    • Full encryption + signatures
    
    Configuration (development):
    • PQC_ENABLED=false
    • Classical HKDF, no signatures (faster testing)
    
    Behavior:
    • Production: Full PQC security
    • Development: Classical (no PQC overhead)
    • Graceful fallback between environments


================================================================================
TROUBLESHOOTING
================================================================================

ISSUE: "Kyber encapsulation failed"
──────────────────────────────────

Cause:    liboqs library not installed or incompatible
Solution: 
  • Install: pip install liboqs-python
  • Or: Set QMIND_PQC_ENABLED=false to use classical fallback
  • Check: python -c "import liboqs; print(liboqs.OQS_STATUS)"

Impact:   System automatically falls back to classical HKDF
Audit:    Downgrade event logged with timestamp


ISSUE: "Signature verification failed"
──────────────────────────────────────

Cause:    Artifact tampering, wrong key version, or clock skew
Solution:
  • Check if artifact modified (bytes changed)
  • Verify signature key version matches
  • Sync server clocks (check NTP status)
  • Review audit logs for context

Impact:   Artifact rejected, operation fails safely
Security: Tampering detected, no data corruption


ISSUE: "Performance degradation >10%"
──────────────────────────────────────

Cause:    Kyber encapsulation overhead, inadequate hardware
Solution:
  • Enable hardware crypto acceleration (AES-NI)
  • Profile with: python -m cProfile tests/benchmark_v361.py
  • Consider: Reduce signature scope (only critical artifacts)
  • Check: CPU/memory/network utilization

Impact:   Throughput <8000 indicators/sec
Mitigation: Scale horizontally (more instances)


ISSUE: "Memory usage increased after upgrade"
──────────────────────────────────────────────

Cause:    Kyber/Dilithium keypairs, metadata tracking
Solution:
  • Expected overhead: ~100 KB (negligible)
  • Check for memory leaks: python tools/check_memory.py
  • Monitor: ps aux | grep qmind (check RSS growth)

Impact:   Minimal (<1% increase for typical deployment)
Normal:   First run loads cryptographic structures


ISSUE: "Backward compatibility broken - can't decrypt v3.6 artifacts"
──────────────────────────────────────────────────────────────────────

Cause:    Master key seed mismatch, environment mismatch
Solution:
  • Verify QMIND_MASTER_KEY_SEED matches v3.6
  • Verify QMIND_ENV matches deployment environment
  • Ensure context (tenant, zone) reconstruction is correct
  • Check: python tests/test_backward_compat.py -v

Impact:   Old artifacts unrecoverable
Prevention: Always preserve master seed, never regenerate


================================================================================
ROLLBACK PROCEDURE
================================================================================

If critical issues discovered post-deployment:

STEP 1: Immediately revert to v3.6
────────────────────────────────

  kubectl set image deployment/qmind-api \
    qmind-api=qmind:v3.6 \
    --record

STEP 2: Monitor for data integrity
─────────────────────────────────

  # All v3.6.1 encrypted artifacts are still recoverable
  # (AES-256-GCM is unchanged)
  # Signatures will not verify (v3.6 doesn't verify)
  # No data loss

STEP 3: Investigate root cause
──────────────────────────────

  • Review logs during failure window
  • Check CPU/memory/network during incident
  • Test suspected scenario in staging
  • Review code changes (if any)

STEP 4: Fix and re-test
──────────────────────

  • Address root cause
  • Run full test suite again
  • Validate in staging
  • Re-deploy with caution


NOTE: Rollback preserves all data
        v3.6.1 artifacts remain encrypted
        v3.6 can decrypt (AES-256-GCM unchanged)
        Signatures simply won't verify (non-critical)


================================================================================
MONITORING & OBSERVABILITY
================================================================================

METRICS TO TRACK:

  Encryption Metrics:
  • qmind_encryption_operations_total (gauge: encrypt/decrypt/sign/verify)
  • qmind_encryption_latency_ms (histogram)
  • qmind_encryption_errors_total (counter)

  PQC Metrics:
  • qmind_kyber_encapsulation_total (counter)
  • qmind_dilithium_signatures_total (counter)
  • qmind_pqc_failures_total (counter: fallback to classical)

  Metadata Metrics:
  • qmind_artifacts_with_metadata_total (should be 100%)
  • qmind_signatures_verified_total
  • qmind_signature_verification_failures_total

  Security Metrics:
  • qmind_key_rotation_events (counter: when keys rotated)
  • qmind_compromised_keys_detected (counter: alert if >0)
  • qmind_tampering_detected_total (counter: signatures failed)


ALERTS TO SET UP:

  [ ] Signature verification failure rate >0.1%
  [ ] Kyber fallback events (PQC unavailable)
  [ ] Key rotation missed (>100 days since last rotation)
  [ ] Metadata missing from artifacts
  [ ] Encryption latency p95 >100ms (10x normal)
  [ ] Memory usage >20% (potential leak)


DASHBOARDS:

  Create Grafana/CloudWatch dashboard showing:
  • Encryption operations per second (should match baseline)
  • Signature verification success rate (should be 100%)
  • PQC algorithm coverage (% using Kyber vs classical)
  • Metadata completeness (% with all fields)
  • Key rotation status (last rotation, next rotation)


LOGGING:

  Every crypto operation should log:
  {
    "timestamp": "2026-01-25T10:30:00Z",
    "operation": "encrypt|decrypt|sign|verify",
    "entity_id": "threat-123",
    "entity_type": "threat_report",
    "algorithm": "AES-256-GCM|Hybrid-Kyber|Dilithium-3",
    "key_version": 1,
    "status": "success|failure",
    "duration_ms": 2.5,
    "metadata_hash": "sha256(...)"
  }

  Audit log processing:
  • Verify no gaps in sequence
  • Check all signatures present
  • Validate metadata consistency


================================================================================
COMPLIANCE & AUDIT
================================================================================

NIST COMPLIANCE CHECKLIST:

  [ ] Using FIPS 203 approved algorithm (Kyber-768)
  [ ] Using FIPS 204 approved algorithm (Dilithium-3)
  [ ] Documenting NIST profile in metadata (2024-2025)
  [ ] No custom cryptography
  [ ] No key reuse across contexts
  [ ] Proper key rotation (90 day default)
  [ ] Audit trail preservation
  [ ] Metadata immutability
  [ ] Graceful fallback documented

AUDIT EVIDENCE:

  Provide to auditors:
  
  1. Cryptographic Architecture Document
     → PQC_ARCHITECTURE_V361.md
  
  2. Test Results
     → test_v361_crypto.py (40+ tests pass)
  
  3. Performance Report
     → Encryption overhead <10%
     → Signature latency <10ms per artifact
  
  4. Metadata Samples
     → 100 randomly selected artifacts
     → All showing complete metadata
     → All showing NIST profile marker
  
  5. Key Rotation Records
     → Timestamp of each rotation
     → Key version increments
     → No unexpected rotations
  
  6. Incident Log
     → Zero cryptographic failures
     → Zero tampering detected
     → Zero unauthorized key access


COMPLIANCE STATEMENT:

  "Q-MIND Enterprise v3.6.1 implements Post-Quantum Cryptography in
   compliance with NIST 2024-2025 guidance. The system uses:
   
   - FIPS 203 Kyber-768 for hybrid key establishment
   - FIPS 204 Dilithium-3 for digital signatures
   - FIPS 197 AES-256-GCM for data encryption (unchanged)
   
   All cryptographic operations are auditable, documented, and aligned
   with NIST standards. No custom cryptography is used. The system
   maintains full backward compatibility with v3.6 artifacts while
   providing quantum-safe key establishment and signatures for future-proofing."


================================================================================
SUPPORT & ESCALATION
================================================================================

TIER 1: Self-Service
────────────────────

Check these resources first:
• PQC_ARCHITECTURE_V361.md (architecture details)
• This document (migration guide)
• test_v361_crypto.py (working examples)
• Logs and metrics (diagnose issues)


TIER 2: Internal Support
────────────────────────

Contact: security-team@qmind.dev

Include:
• Deployment environment
• Error logs (last 100 lines)
• Metrics snapshot (throughput, latency, errors)
• Steps to reproduce issue
• Severity assessment


TIER 3: Vendor Support
──────────────────────

For liboqs or cryptographic library issues:
• Open issue: https://github.com/open-quantum-safe/liboqs-python
• Provide: Version, environment, reproducer


================================================================================
SUCCESS CRITERIA
================================================================================

v3.6.1 deployment is successful if:

✓ All tests pass (100% coverage)
✓ Backward compatibility with v3.6 verified
✓ Performance overhead <10%
✓ Throughput maintained >8,000 indicators/sec
✓ Zero encryption failures in 24-hour soak test
✓ Zero signature verification failures (or all explained)
✓ Metadata complete on 100% of new artifacts
✓ No memory leaks detected
✓ No regressions in data operations
✓ Audit trail preserved and auditable
✓ NIST compliance documented
✓ Team trained and comfortable with v3.6.1

Once all criteria met → Safe to declare general availability


================================================================================
CONCLUSION
================================================================================

Q-MIND v3.6.1 represents a mature, production-ready upgrade that brings
post-quantum cryptographic capabilities to a proven enterprise system.

The migration is:
✓ Low-risk (full backward compatibility)
✓ Well-tested (40+ unit tests)
✓ Performant (minimal overhead)
✓ Auditable (full metadata tracking)
✓ Standards-aligned (NIST-approved algorithms)

Recommended next steps:
1. Review PQC_ARCHITECTURE_V361.md
2. Deploy to staging and run tests (2-4 hours)
3. Validate backward compatibility
4. Plan production rollout (canary 5% → 100%)
5. Monitor metrics and audit logs
6. Generate compliance report

Expected timeline: 2-3 weeks from staging to full production

================================================================================
"""
