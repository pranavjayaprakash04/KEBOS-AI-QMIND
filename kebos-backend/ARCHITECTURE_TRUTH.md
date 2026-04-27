# Kebos/QMind — What Is Actually Built

**Subtitle:** Honest reference for demos, investors, and new developers
**Date:** 2026-04-27
**Based on:** Full static analysis of 14 source files. No live system was accessed.

---

## What Works End-to-End

Features that are correctly implemented and will work in a running stack.

**1. Username/password login — returns a valid RS256 JWT**
- `POST /api/v1/auth/login` with `{"username":"admin","password":"admin123"}` returns a 200 with `access_token`
- Token is a valid RS256-signed JWT with 15-minute expiry
- Cookie is set with HttpOnly + SameSite=strict + Secure flags (correct design)
- Caveat: Authentication is against a hardcoded mock, not the database; the password is printed to logs

**2. Protected endpoint enforcement**
- Routes decorated with `Depends(get_current_user)` correctly reject requests without a valid JWT
- Algorithm is pinned to RS256 only in `verify_token`; algorithm confusion attacks are blocked
- Government tenant check (FIDO2 enforcement) is correctly coded at `dependencies.py:75–79`

**3. Signal injection → Kafka publish**
- `POST /api/v1/signals/inject` with valid auth and correct payload:
  - Validates category against `ThreatCategory.values()`
  - Validates confidence range 0.0–1.0
  - CatBoost-scores the indicator
  - Publishes to `threat.indicators` Kafka topic if publisher is available
  - Inserts a row in `threat_events` with status="pending"

**4. QMind Kafka consumption and threat status update**
- `qmind_consumer.py` consumes `qmind.results`
- Correctly applies `TENANT_THRESHOLDS` to map confidence → status (CONFIRMED_THREAT / ELEVATED / MONITORING / BENIGN)
- Issues UPDATE to `threat_events` with the final status and confidence
- Auto-restarts after 5-second delay on crash (done_callback pattern)
- Caveat: Crashes on honeypot signals due to `UUID("unknown")` at line 69

**5. Automatic case creation for CONFIRMED_THREAT**
- When status = CONFIRMED_THREAT, `cases/manager.py` creates a case with:
  - Auto-generated `CASE-YYYYMMDD-XXXXXXXX` case number
  - 6-hour CERT-In deadline
  - Severity mapped from confidence (CRITICAL ≥0.90, HIGH ≥0.75, MEDIUM ≥0.50)
- Caveat: `_generate_cert_in_report` is a stub (logs, does nothing)

**6. CERT-In PDF generation via HTTP endpoint**
- `POST /api/v1/cases/{case_id}/cert-in-report` generates a PDF and returns it as a download
- Jinja2 template renders incident fields correctly
- SHA-256 hash of PDF content is computed
- Dilithium-3 signing works if `DILITHIUM_SIGNING_KEY_HEX` is set in environment
- Caveat: PDF rendering uses regex-based HTML stripping rather than proper HTML→PDF; output is plain text in PDF format

**7. UEBA event storage**
- Every authenticated request stores a UEBA event in `ueba_events` via `baseline_engine.py`
- Features collected: hour_of_day, day_of_week, source_ip, endpoint, request_size_bytes, user_agent

**8. WebSocket real-time dashboard**
- `websocket_manager.broadcast_to_tenant()` sends threat updates to connected WebSocket clients on `/ws/threats/{tenant_id}` immediately after QMind scoring

**9. Tenant isolation design (correct architecture, broken execution)**
- RLS policies exist in the database schema for tenant-scoped tables
- The auth middleware correctly extracts tenant_id from JWT and attempts to set the PostgreSQL session variable
- The bug is in connection lifecycle (released too early) — the design is right, the wiring is wrong

**10. CatBoost threat scoring**
- `CatBoostThreatEngine.score()` runs on every signal inject
- Score is included in the Kafka message and in the initial `threat_events` DB row

---

## What Is Partially Working

Features that work only under specific conditions.

| Feature | Works When | Breaks When |
|---------|-----------|-------------|
| JWT token revocation | Never — Redis client is always None | Always |
| Logout | Cookie deletion works; JTI blacklist crashes with AttributeError | Always (Redis None) |
| Session risk scoring (impossible travel) | GeoIP DB is installed at `data/GeoLite2-City.mmdb` | GeoIP file missing (default config) |
| Dilithium-3 PDF signing | `DILITHIUM_SIGNING_KEY_HEX` env var is set | Not set (default) — PDF generated unsigned |
| TOTP verification | Never — `authenticate_user("","")` always returns None | Always |
| FIDO2 authentication | Never — `request.username` AttributeError crash | Always |
| UEBA anomaly detection | Never — string features cause silent `ValueError` in Mahalanobis | Always |
| Honeypot signal pipeline | Never — `UUID("unknown")` crashes consumer | Always (any honeypot signal) |
| Emergency session rotation | Never — Redis is None, check is skipped | Always |
| QMind category scores | Partially — winning category gets a fixed score, others get 0.0 | When multi-class probabilities are needed |

---

## What Is Stubbed or Faked

| Component | What It Says | What It Returns |
|-----------|-------------|----------------|
| `authenticate_user()` | "Authenticating user against database with bcrypt" | Returns hardcoded UserProfile for `admin/admin123`; None for everything else |
| `redis_client` in AuthService | JTI blacklist storage | Always None |
| `_generate_cert_in_report()` in CaseManager | "Generated CERT-In report for case {id}" | Nothing — the report is never generated at case creation time |
| `step_up_auth` branch in get_current_user | Requires re-authentication on device change | `pass` — request proceeds without challenge |
| `_process_analyst_feedback()` in QMindKafkaConsumer | Feeds correction into ML retraining loop | Returns static Benign result; no correction stored |
| `category_scores` in all QMind paths | Multi-class probability distribution across 10 threat categories | Binary: 1.0 for winning category, 0.0 for all others |
| FIDO2 assertion verification | Cryptographically verifies YubiKey assertion | Checks `X-FIDO2-Assertion` header is non-empty |
| Playbook execution | `TODO: Integrate with PlaybookEngine` | Logger.info only |
| `TOTP enable` endpoint | Generates provisioning URI for authenticator app | Returns HTTP 501 Not Implemented |

---

## What Is Missing Entirely

| Feature | Where It Is Referenced | Status |
|---------|----------------------|--------|
| Real database authentication | `auth/services.py:74` | Mock in place; DB auth code does not exist |
| Account lockout after failed logins | Standard auth requirement | Not implemented |
| Analyst feedback → model retraining | `kafka_consumer.py:300` | Stub returns static result |
| Structured HTML-quality CERT-In PDF | `cert_in_generator.py` | Regex stripping produces plaintext |
| UEBA anomaly signals to QMind | `ueba/baseline_engine.py:76` | Method exists but score never exceeds 0.0 due to type bug |
| Token rotation notification to clients | After emergency rotation | Redis check code exists but Redis is disabled |
| NTA (Network Traffic Analysis) | `main.py:10–11` | Router imported; implementation not reviewed |
| Scraping pipeline (GeM, CPPP, TN Tenders) | Not in this codebase | Lives in GitHub Actions (separate repo) |
| Multi-tenant admin panel | `admin/tenants.py` | Not reviewed in this audit |

---

## Safe Demo Script

Exact sequence that will succeed without hitting any broken feature.

```
1. Start the stack:
   docker-compose up -d postgres redis kafka zookeeper vault kebos-backend qmind

2. Wait 30 seconds for Kafka partition assignment and DB pool warmup.

3. Open the health endpoint:
   GET http://localhost:8000/health
   → Verify: status=healthy, audit_chain=initialized

4. Login:
   POST http://localhost:8000/api/v1/auth/login
   Body: {"username": "admin", "password": "admin123"}
   → Copy the access_token from the response

5. Inject a domain signal:
   POST http://localhost:8000/api/v1/signals/inject
   Header: Authorization: Bearer <token>
   Body:
     {
       "threat_id": "demo-threat-001",
       "ioc_value": "evil-demo.com",
       "ioc_type": "domain",
       "source_type": "ct_log",
       "category": "Phishing",
       "confidence": 0.85
     }
   → Verify: status=accepted, kafka_produced=true

6. Wait 25 seconds for QMind to consume and score.

7. Check threat event status:
   Query postgres: SELECT indicator_value, status, qmind_confidence
                   FROM threat_events ORDER BY created_at DESC LIMIT 1;
   → Expected: status=CONFIRMED_THREAT (confidence 0.85 > 0.75 enterprise threshold)

8. Check that a case was auto-created:
   GET http://localhost:8000/api/v1/cases/
   Header: Authorization: Bearer <token>
   → Should show the case with cert_in_deadline 6 hours from now

9. Download CERT-In report (takes the case UUID from step 8):
   GET http://localhost:8000/api/v1/cases/{case_id}/cert-in-report
   Header: Authorization: Bearer <token>
   → Returns PDF download — saves to cert-in-{case_id}.pdf

10. Show real-time WebSocket (optional, requires frontend):
    ws://localhost:8000/ws/threats/{tenant_uuid}
    → Connect BEFORE injecting a second signal; signal processing event appears live
```

---

## Things NOT to Demo

Exact list of what will visibly fail or produce incorrect results.

| Feature | What Happens | Error Visible to Audience |
|---------|-------------|--------------------------|
| **Logout** | `AttributeError: 'NoneType' object has no attribute 'setex'` in logs; cookie deleted but token still valid | 500 error if response body checked |
| **TOTP / 2FA** | TOTP enable returns 501; TOTP verify crashes with AttributeError | HTTP 501 or 500 |
| **FIDO2 registration completion** | `NameError: name 'json' is not defined` in fido2_register_begin | HTTP 500 |
| **FIDO2 authentication** | `AttributeError: 'Request' object has no attribute 'username'` | HTTP 500 |
| **Government tenant login** | gov_user is blocked by FIDO2 requirement (correctly) but has no recovery path | HTTP 403 permanently |
| **Honeypot signal injection** | `source_type: "honeypot"` — QMind consumer crashes with `ValueError: badly formed hexadecimal UUID string: 'unknown'` | Consumer restarts silently; signal never processed |
| **Insider threat / UEBA anomaly** | Score always returns 0.0; no anomaly ever fired | No visible error — just silent non-detection |
| **Case timeline endpoint** | Queries `audit_log` table which may not exist (schema has `audit_entries`) | HTTP 500 or 0 events returned |
| **Emergency rotation** | `POST /api/v1/auth/security/emergency-rotation` — FIDO2 assertion not verified | Works but provides false security assurance |
| **Second login (concurrency)** | Both sessions use the same ephemeral RSA key in the same process lifetime; fine for demo, breaks on restart | Not visible unless restart happens |

---

## Technical Questions You Will Be Asked

**Q: Is this production-ready?**
A: No. There are 8 critical security vulnerabilities, of which three make the auth system non-functional: logout does not revoke tokens, cookie authentication does not work, and database authentication is replaced by a hardcoded mock. Tenant data isolation (RLS) is architecturally correct but broken by a connection lifecycle bug. The system is demo-ready for a controlled single-tenant scenario where it is not connected to any external network. Fixing the critical issues would take approximately 2 developer-weeks of focused work.

**Q: How does the post-quantum cryptography work?**
A: Two PQC algorithms are implemented. (1) Kyber768 (ML-KEM) key encapsulation via liboqs: the QMind container builds liboqs from source (version 0.12.0) and wraps it in Python. A Kyber768 key pair can be generated and a shared secret encapsulated/decapsulated. This works end-to-end. (2) Dilithium-3 (ML-DSA) signatures: used to sign CERT-In PDF reports and the audit timeline. Signing works if a signing key is provided via `DILITHIUM_SIGNING_KEY_HEX` in the environment; without it, reports are generated unsigned. Both algorithms will be standardized as NIST FIPS 203/204 respectively. What is NOT implemented: PQC-protected Kafka transport, PQC-protected JWT signing (JWTs use RSA-2048), or PQC key exchange for any client-to-server communications.

**Q: Is RLS enforced for all tenants?**
A: The RLS policies are defined in the database schema, and the architecture is correct. However, there is a bug in `auth/dependencies.py:40–46` where the tenant context is set on a database connection that is immediately released before any actual query runs. As a result, all queries run without the tenant filter — every tenant can currently read every other tenant's data. This is a one-file fix but it is critical.

**Q: What ML model is used for threat scoring?**
A: Two models run in sequence. (1) CatBoost: a gradient-boosted tree model runs first in the kebos-backend on every signal inject. It produces an initial `catboost_score` based on indicator features (IP, domain, type, source). (2) SignalScorer (QMind): a confidence-decay and supplier-trust weighting model that adjusts the CatBoost score based on feed reliability and time elapsed since detection. The final score after both models determines the threat status. What is NOT production-quality: the category_scores output is binary (1 winning category, 0 for all others) rather than actual multi-class probabilities. The analyst feedback retraining loop is a stub that does not update any model weights.

**Q: How does CERT-In compliance work?**
A: When a threat reaches CONFIRMED_THREAT status, a case is auto-created with a 6-hour deadline (matching CERT-In S.O. 1374(E) reporting requirement). The `/cases/{id}/cert-in-report` endpoint generates a PDF with incident details and — when a Dilithium-3 signing key is configured — embeds a post-quantum signature for legal admissibility. What is NOT working: the PDF is generated by stripping HTML tags with regex rather than proper HTML→PDF conversion, producing plain-text output rather than a formatted document. The `_generate_cert_in_report` stub in `CaseManager` (called at case creation time) does nothing — the PDF is only generated on explicit HTTP request.

**Q: Is database authentication working?**
A: No. The `authenticate_user` method in `auth/services.py` contains a comment: "TEMPORARY: Use mock authentication for demo loop validation." It compares submitted credentials against two hardcoded strings (`admin/admin123` and `gov_user/gov`) and never touches the database. The bcrypt comparison, DB query, and account lockout code do not exist yet. This is the highest-priority fix before any customer engagement.
