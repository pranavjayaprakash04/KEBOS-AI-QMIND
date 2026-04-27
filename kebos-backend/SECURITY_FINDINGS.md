# Kebos/QMind Security Audit Report

**Audit Date:** 2026-04-27
**Auditor:** Static analysis — Phase 2 and Phase 6 findings
**Scope:** kebos-backend (all auth, signals, cases) + qmind_enterprise + docker-compose.yml
**Method:** Full static file review. No live containers accessed.

---

## Executive Summary

The Kebos/QMind backend was audited across 14 source files and infrastructure configuration. The system's authentication layer is non-functional in three independent ways simultaneously: database authentication is replaced by a hardcoded mock, logout does not invalidate tokens (Redis client is unconditionally set to None), and cookie-based auth always fails because a "Bearer " prefix is stored in the cookie. Row-Level Security, the primary tenant isolation mechanism, is set on a connection that is immediately released before any actual query runs — every tenant can currently read every other tenant's data. The most urgent risk before any external demo is the hardcoded `admin/admin123` credential pair printed in plaintext on every login attempt, which ships to every connected log aggregator.

---

## Critical Findings

### SEC-001 — Plaintext Password Logged on Every Login

**File:** `kebos-backend/app/auth/router.py:79`
**Also:** `kebos-backend/app/auth/services.py:78–79`

**Description:** Two separate statements print or log the submitted password verbatim on every login attempt.

```python
# router.py:79
print(f"DEBUG: Login attempt: username={login_request.username}, password={login_request.password}")

# services.py:78–79
print(f"AUTH DEBUG: username={repr(username)}, password={repr(password)}")
logger.info(f"Mock auth attempt: username={username}, password={password}")
```

The `logger.info` line is shipped to TLS syslog and Splunk HEC per `main.py:234–247`. Every password ever submitted is in every log sink.

**Impact:** Any operator, log viewer, SIEM analyst, or attacker with log access has a complete record of every credential submitted since deployment.

**Reproduction:**
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
docker-compose logs kebos-backend | grep "DEBUG"
# Output: DEBUG: Login attempt: username=admin, password=admin123
```

**Fix:**
```python
# router.py — remove line 79 entirely
# services.py — remove line 78 entirely; change line 79 to:
logger.info(f"Auth attempt: username={username}")
```

---

### SEC-002 — Database Authentication Bypassed by Hardcoded Mock

**File:** `kebos-backend/app/auth/services.py:74–106`

**Description:** The `authenticate_user` method does not query the database. It compares credentials against two hardcoded accounts:
- `admin / admin123` — role=admin, fixed UUID
- `gov_user / gov` — role=ANALYST, tenant_id="2" (not a UUID)

The method has a comment: `# TEMPORARY: Use mock authentication for demo loop validation`.

**Impact:** Any attacker who reads the source (GitHub, container image layer, leaked backup) has permanent admin credentials that survive any DB password rotation, user deletion, or LDAP change. There is no account lockout and no bcrypt comparison.

**Reproduction:** `curl -X POST http://localhost:8000/api/v1/auth/login -d '{"username":"admin","password":"admin123"}'` — always returns 200 regardless of what is in the database.

**Fix:** Restore the real DB auth path. Query the `users` table, use `bcrypt.checkpw(password.encode(), hashed_password.encode())`. Use `hmac.compare_digest` for constant-time comparison. Remove both hardcoded accounts entirely.

---

### SEC-003 — Row-Level Security Tenant Isolation Broken

**File:** `kebos-backend/app/auth/dependencies.py:40–46`

**Description:** The RLS tenant variable is set on a connection that is immediately released back to the pool. All subsequent DB queries in route handlers acquire different connections where `app.current_tenant` is not set. With PostgreSQL's `SET LOCAL`, the variable is scoped to the current transaction — once the connection is returned, the setting is gone.

```python
# dependencies.py:40–46 — tenant set, connection released
async with app.state.db_pool.acquire() as conn:
    await conn.execute("SELECT set_config('app.current_tenant', $1, true)", tenant_id)
# connection returned to pool HERE — setting is gone

# cases/router.py:179 — NEW connection acquired, no tenant set
async with app.state.db_pool.acquire() as db:
    case = await db.fetchrow("SELECT * FROM cases WHERE id=$1 ...", ...)
    # RLS policy checking app.current_tenant → empty string → no filter → all tenants visible
```

**Impact:** Tenant A's analyst calling `GET /api/v1/cases/` receives cases from all tenants. All RLS-protected tables are affected: `threat_events`, `cases`, `ueba_events`, `users`.

**Fix:** Either (a) use a request-scoped connection passed through FastAPI dependency injection, setting the tenant variable once per connection before any query; or (b) use `SET` (not `SET LOCAL`) and reset to an empty string in a connection pool `on_acquire`/`on_release` hook.

```python
# Correct approach: connection-scoped dependency
async def get_db_with_tenant(
    current_user: UserProfile = Depends(get_current_user),
    pool = Depends(get_pool)
) -> asyncpg.Connection:
    async with pool.acquire() as conn:
        await conn.execute("SELECT set_config('app.current_tenant', $1, false)", current_user.tenant_id)
        yield conn
```

---

### SEC-004 — Ephemeral RSA Signing Keys — All Sessions Invalidated on Restart

**File:** `kebos-backend/app/auth/services.py:12–24`

**Description:** RSA-2048 key pair is generated at module import time and stored only in process memory. Every container restart generates a new key pair, making all previously issued JWTs unverifiable.

```python
_RSA_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
# No persistence. New key on every restart.
```

**Impact:** (1) A forced restart logs out every analyst mid-investigation — effective DoS on incident response. (2) If `VAULT_DEV_RSA_PRIVATE_KEY` is set in the environment, it overrides the generated key — if this env var is leaked, all future tokens can be forged offline.

**Fix:** Load the private key from Vault at startup. The configuration scaffolding already exists (`settings.VAULT_DEV_RSA_PRIVATE_KEY`, `settings.VAULT_PKI_ENABLED`). Use the Vault PKI secrets engine or Vault KV to store the key, and load it once during `lifespan()`.

---

### SEC-005 — Redis Disabled — JTI Blacklist and Logout Non-Functional

**File:** `kebos-backend/app/auth/services.py:54`

**Description:** `AuthService.__init__` unconditionally sets `self.redis_client = None`. This disables three security controls:
1. JTI blacklist check in `verify_token` (line 142) — skipped when `redis_client is None`
2. Emergency session rotation check in `dependencies.py:52–58` — skipped when `redis_client is None`
3. `logout_user` at line 154 calls `self.redis_client.setex(...)` on `None` → `AttributeError` crash

**Impact:** Stolen or leaked JWTs remain valid for the full 15-minute window even after the user explicitly logs out. Emergency rotation signals are ignored.

**Fix:** Restore Redis connection in `__init__`. If Redis is unavailable, log a warning and fail gracefully on each operation rather than disabling the feature globally.

```python
def __init__(self):
    try:
        self.redis_client = redis.from_url(settings.REDIS_URL)
    except Exception as e:
        logger.error(f"Redis unavailable: {e} — JTI blacklist disabled")
        self.redis_client = None
```

Also add a None guard in `logout_user`:
```python
async def logout_user(self, user: UserProfile, jti: str):
    if not self.redis_client:
        logger.error("Cannot blacklist JTI — Redis unavailable")
        return
    await self.redis_client.setex(...)
```

---

### SEC-006 — Cookie Authentication Always Fails ("Bearer " Prefix Bug)

**File:** `kebos-backend/app/auth/router.py:116`

**Description:** The access token cookie is stored with the "Bearer " prefix prepended to the JWT:
```python
response.set_cookie(key="access_token", value=f"Bearer {token}", ...)
```
`dependencies.py:19` reads the cookie raw and passes it to `verify_token()`. `jwt.decode("Bearer eyJ...", ...)` fails because the string is not a valid JWT. Cookie-based auth silently falls back to Authorization header on every request. `HttpOnly` cookie protection is therefore non-functional.

**Impact:** The application claims to use `HttpOnly` cookies (correct design) but actually relies on Bearer tokens in headers. The logout endpoint reads the cookie (with "Bearer " prefix), fails `verify_token`, never extracts the JTI, and never blacklists it — logout provides zero token revocation even if Redis were working.

**Fix:**
```python
# router.py:116 — store only the raw token, no prefix
response.set_cookie(key="access_token", value=token, ...)
```
And in `dependencies.py` handle the case where the cookie might have a stale "Bearer " prefix:
```python
token = request.cookies.get("access_token", "")
if token.startswith("Bearer "):
    token = token[7:]
```

---

### SEC-007 — FIDO2 Assertion Not Cryptographically Verified

**File:** `kebos-backend/app/auth/router.py:538`

**Description:** The `/security/emergency-rotation` endpoint checks only that the `X-FIDO2-Assertion` header is present, not that it is a valid signed assertion:
```python
# TODO: Verify FIDO2 assertion
# For scaffold, we just check the header exists
```

**Impact:** Any string value in the header bypasses the FIDO2 requirement and allows an admin with a stolen JWT to trigger emergency key rotation, invalidating all sessions company-wide.

**Reproduction:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/security/emergency-rotation \
  -H "Authorization: Bearer <stolen_admin_jwt>" \
  -H "X-FIDO2-Assertion: anything_at_all" \
  -d '{"reason": "attacker rotation"}'
# Returns 200 — all sessions invalidated
```

**Fix:** Implement actual FIDO2 assertion verification using `verify_authentication_response()` from the `webauthn` library (already imported in `fido2_authenticate_complete`). Do not merge this endpoint until the verification is real.

---

## High Findings

### SEC-008 — No Rate Limiting on /auth/login

**File:** `kebos-backend/app/auth/router.py:69`

Every other sensitive auth endpoint has `@limiter.limit("N/minute")`. The login endpoint, the most-attacked endpoint in any web service, has no decorator. After real DB auth is restored, this enables unlimited password spraying.

**Fix:** Add `@limiter.limit("10/minute")` above `@router.post("/login")`.

---

### SEC-009 — HashiCorp Vault in Dev Mode with Hardcoded Public Token

**File:** `docker-compose.yml:212–213`

```yaml
VAULT_DEV_ROOT_TOKEN_ID=dev-root-token
```
Vault dev mode stores all secrets in memory (lost on restart) and the root token is a well-known string that is publicly documented in HashiCorp's examples. Port 8200 is exposed to the Docker host.

**Fix:** Use Vault server mode. Generate and unseal with a real key. Rotate the root token immediately after init. Remove the host port mapping for 8200 or add network policy.

---

### SEC-010 — Six Internal Services Exposed on Host Ports

**File:** `docker-compose.yml:80, 104, 119, 148, 169, 208`

PostgreSQL (5432), Redis (6379), Kafka (9092), ZooKeeper (2181), InfluxDB (8086), and Vault (8200) are all bound to the Docker host interface. None have TLS or auth appropriate for external exposure.

**Fix:** Remove all host port mappings except `8000` (backend) and `8001` (QMind). Use `docker-compose exec` for admin access.

---

### SEC-011 — Kafka PLAINTEXT (No TLS or Authentication)

**File:** `docker-compose.yml:127`

```yaml
KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
```
All threat intelligence — IOC values, QMind scores, analyst corrections — flows across Kafka in plaintext. Any container on the `data-net` network can produce or consume without credentials.

**Fix:** Configure `SSL` listener with a keystore and truststore. Add `KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=SSL`.

---

### SEC-012 — FIDO2 Credentials Stored in Redis (Ephemeral), Not Database

**File:** `kebos-backend/app/auth/router.py:300–312`

FIDO2 credentials are stored in Redis with a 30-day TTL. The `users.fido2_credentials` JSONB column already exists in the database schema (`models.py:18`) and is the correct storage location. Redis data is volatile — a Redis restart wipes all registered YubiKey credentials.

**Fix:** Store credential data in `users.fido2_credentials` (JSONB). Use Redis only for ephemeral challenges (TTL 5 minutes).

---

### SEC-013 — QMind /analyze and /signals/inject Have No Authentication

**File:** `qmind_enterprise/enterprise_api.py:124, 182`

Both analysis endpoints accept requests without any authentication token, API key, or network policy. Any process on the same Docker network can inject arbitrary signals into the threat pipeline, bypassing all auth controls in the kebos-backend.

**Fix:** Add an API key header check validated against a secret configured at startup:
```python
API_KEY = os.environ.get("QMIND_API_KEY")

async def verify_api_key(x_api_key: str = Header(...)):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

### SEC-014 — WebSocket Endpoint Has No Authentication

**File:** `kebos-backend/app/main.py:341–349`

`/ws/threats/{tenant_id}` accepts WebSocket connections from any client, unauthenticated. Real-time threat intelligence is broadcast to whoever connects first with a valid tenant UUID.

**Fix:** Require a JWT passed as a query parameter (`?token=...`) and validate it before accepting the WebSocket upgrade.

---

### SEC-015 — TLS Verification Disabled for Vault Client

**File:** `kebos-backend/app/auth/totp.py:41`, `kebos-backend/app/main.py:83`

```python
verify=False  # TODO: Use proper CA cert in production
```
Both the TOTP service Vault client and the Dilithium key loader Vault client disable TLS certificate verification.

**Fix:** Mount the Vault CA certificate into both containers and set `verify="/path/to/vault-ca.pem"`.

---

### SEC-016 — Fernet Key Ephemeral When VAULT_DEV_FERNET_KEY Unset

**File:** `kebos-backend/app/auth/totp.py:59`

```python
dev_key = settings.VAULT_DEV_FERNET_KEY or Fernet.generate_key()
```
If `VAULT_DEV_FERNET_KEY` is not configured, a new key is generated every process start. All TOTP secrets encrypted with the previous key become permanently undecryptable — all TOTP-enabled users are locked out after every container restart.

**Fix:** Fail startup with a clear error if neither `VAULT_ENABLED` nor `VAULT_DEV_FERNET_KEY` is set.

---

## Medium Findings

### SEC-017 — case_id Accepts str Not UUID

**File:** `kebos-backend/app/cases/router.py:67, 236`

`get_case()` and `get_case_timeline()` accept `case_id: str`. Invalid strings cause unhandled asyncpg errors returning 500 with internal DB error details. `generate_cert_in_report()` in the same file correctly uses `case_id: UUID`.

**Fix:** Change both signatures to `case_id: UUID`. FastAPI returns 422 automatically.

---

### SEC-018 — Audit Write Silently Swallowed on Irreversible Action

**File:** `kebos-backend/app/cases/router.py:150–151`

```python
except Exception:
    pass  # Audit logging not available
```
An analyst approving an irreversible action leaves no audit record if the audit chain is unavailable.

**Fix:** At minimum: `logger.error("AUDIT WRITE FAILED: action_id=%s user=%s", ...)`. Consider making audit failure a hard error that rolls back the approval.

---

### SEC-019 — SECRET_KEY Defaults to "change-me-in-production"

**File:** `kebos-backend/app/config.py:37`

**Fix:** Add to `validate_environment()`:
```python
if settings.SECRET_KEY == "change-me-in-production":
    errors.append("CRITICAL: SECRET_KEY must be changed from default value")
```

---

### SEC-020 — Step-Up Auth Is a TODO No-Op

**File:** `kebos-backend/app/auth/dependencies.py:97–99`

When `SessionRiskScorer` detects a new device, `action="step_up_auth"` is returned. The handling is:
```python
if risk_result.action == "step_up_auth":
    # TODO: Implement step-up authentication flow
    # For scaffold, allow with warning
    pass
```
The request proceeds normally. Device change detection provides zero security value.

**Fix:** Until implemented, log the step-up event. Do not imply to any customer that device change detection requires re-authentication.

---

## Low Findings

### SEC-021 — Full Signal Data Logged at INFO Level

**File:** `kebos-backend/app/threat_detection/router.py:163`

```python
logger.info(f"Signal injected: {signal_data}")
```
Logs usernames, tenant IDs, and IOC values to the INFO log stream shipped to Splunk.

**Fix:** Log only: `logger.info("Signal injected: %s type=%s source=%s", request.ioc_value, request.ioc_type, request.source_type)`

---

### SEC-022 — Client-Controlled X-Request-ID (Log Injection)

**File:** `kebos-backend/app/main.py:323`

The `X-Request-ID` header is accepted from clients without validation. Crafted values with newlines or ANSI codes could corrupt log streams.

**Fix:** Validate the value matches a UUID pattern before using it.

---

### SEC-023 — X-Dilithium3-Signed Header Leaks Signing Key State

**File:** `kebos-backend/app/cases/router.py:225`

**Fix:** Remove the header or always return `"true"` and fail if the key is absent.

---

## Accepted Risks for Demo

| Risk | Reason Accepted | Condition |
|------|----------------|-----------|
| Ephemeral RSA keys | Demo only, no session persistence needed | Single demo session with no restart |
| Hardcoded admin/admin123 | Demo requires predictable login | Must not be connected to any real network |
| Redis disabled | Logout irrelevant in demo | Demo does not demonstrate logout flow |
| Kafka PLAINTEXT | Demo environment, isolated network | No sensitive data injected during demo |
| InfluxDB admin/admin_password | Demo, no PII in InfluxDB | Metrics only |

---

## What Is Genuinely Well-Built

- **JWT algorithm pinning:** RS256 is hardcoded in both `create_access_token` and `verify_token`. The `algorithms=["RS256"]` list in `jwt.decode()` prevents algorithm confusion attacks.
- **Token expiry enforcement:** A startup assertion (`assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 15`) prevents deployment with long-lived tokens.
- **HttpOnly + SameSite=strict cookie design:** The cookie attributes are correct. The bug is in the value stored (with "Bearer " prefix), not the cookie configuration itself.
- **Kafka consumer auto-restart:** `handle_task_error` correctly schedules a 5-second delayed restart for the consumer — the pipeline recovers from transient failures without manual intervention.
- **Tenant threshold differentiation:** `TENANT_THRESHOLDS` in `qmind_consumer.py` applies different confidence cutoffs for government vs enterprise tenants — this is the correct architecture for a multi-tenant SIEM.
- **Dilithium-3 signing design:** The CERT-In PDF generation correctly hashes the content, attempts Dilithium signing, and embeds both the hash and signature in the final PDF — the design is correct even though the key is ephemeral.
- **Docker user isolation:** Both `kebos-backend` and `kafka` run as UID 1000 (`user: "1000:1000"`). `kebos-backend` has `read_only: true` and `no-new-privileges:true`. These are meaningful hardening steps.
- **CORS allowlist:** CORS is locked to an explicit allowlist (`config.py:53–56`) with no wildcard.
- **Docker socket proxy:** The `docker-proxy` service uses `tecnativa/docker-socket-proxy` to restrict what the honeygrid container can do with the Docker socket — it disables AUTH, SECRETS, and EXEC permissions.
