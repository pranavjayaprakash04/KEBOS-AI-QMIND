# Kebos/QMind Technical Debt Register

**Date:** 2026-04-27
**Source:** Phases 1, 2, and 6 static analysis

---

## Stubs and Fakes

Things that look real in the codebase but are not implemented.

| Component | What It Claims to Do | What It Actually Does | Effort to Fix |
|-----------|---------------------|----------------------|---------------|
| `auth/services.py:authenticate_user` | Authenticate users against the database with bcrypt | Compares credentials against two hardcoded strings: `admin/admin123` and `gov_user/gov` | 4h — restore DB query + bcrypt check |
| `auth/services.py:redis_client` | JTI blacklist for token revocation | Always `None`; JTI check skipped, logout crashes | 2h — restore redis.from_url() in `__init__` |
| `auth/router.py:verify_totp` | Complete TOTP MFA verification | Calls `authenticate_user("","")` which always returns `None`; crashes with `AttributeError` at `create_access_token(None)` | 6h — fetch user by ID from DB, not by credential |
| `auth/router.py:fido2_authenticate_complete` | Verify FIDO2 assertion and issue session | Uses `request.username` (FastAPI Request, not Pydantic model) → `AttributeError` crash on every call | 3h — fix variable reference, add real user lookup |
| `auth/router.py:security/emergency-rotation` | Verify FIDO2 assertion before rotation | Checks header presence only; any string bypasses | 4h — implement `verify_authentication_response()` |
| `cases/manager.py:_generate_cert_in_report` | Generate CERT-In PDF when a case is created | Logs "Generated CERT-In report" and returns; no PDF is created | 8h — integrate with `CERTInReportGenerator` |
| `ueba/baseline_engine.py:_mahalanobis_distance` | Compute behavioral anomaly score | Always returns `0.0` because `float(current[k])` raises `ValueError` for string features (source_ip, endpoint, user_agent) — caught silently | 8h — encode string features numerically |
| `auth/dependencies.py:step_up_auth` | Challenge user to re-authenticate when device changes | `pass` statement — request proceeds normally | 12h — issue challenge token, require TOTP re-entry |
| `qmind/kafka_consumer.py:_process_analyst_feedback` | Feed analyst corrections into ML retraining loop | Returns static Benign result; ignores all feedback data | 16h — store corrections to DB, implement retraining trigger |
| `qmind/kafka_consumer.py:category_scores` | Return multi-class probability distribution across 10 threat categories | Returns 1 for the winning category, 0 for all others — binary indicator, not probability | 4h — use real model output scores from SignalScorer |
| `auth/totp.py:VaultClient` | Use HashiCorp Vault transit engine in production | Works but `verify=False` on TLS; falls back to Fernet with ephemeral key if `VAULT_DEV_FERNET_KEY` unset | 4h — add CA cert path, require Fernet key to be set |
| `reporting/cert_in_generator.py:_render_pdf` | Generate structured PDF from Jinja2 template | Strips all HTML tags, writes plaintext with period-split fragmentation | 8h — replace with WeasyPrint or xhtml2pdf |

---

## Schema Debt

Mismatches between code assumptions and the database.

| Issue | Code Location | Database Reality | Risk |
|-------|--------------|-----------------|------|
| `User.id` is `Integer` in ORM model | `auth/models.py:10` | Should be UUID to match mock auth (which uses UUID strings) | Type mismatch breaks any real DB auth attempt |
| `User.tenant_id` is `Integer` in ORM model | `auth/models.py:15` | Should be UUID FK to `tenants.id` | Same — integer FK on a UUID-keyed table |
| `threat_events` updated by `indicator_value` not UUID | `qmind_consumer.py:100–102` | Correct primary key is `id` (UUID) | Same indicator from two tenants updates both rows |
| Cases `threat_id` FK gets indicator_value string | `cases/manager.py:84` when `threat_id` is missing from QMind result | FK points to `threat_events.id` (UUID) — string would fail FK constraint | Cases fail to insert silently |
| `ueba_baselines` conflict target is `(user_id)` alone | `ueba/baseline_engine.py:215` | Correct unique key should be `(user_id, tenant_id)` | Wrong user's baseline overwritten |
| `audit_log` table referenced in `cases/router.py:270` | `cases/router.py:270–282` | Schema has `audit_entries` not `audit_log` | Timeline endpoint always returns 0 events |

---

## Missing Features

Features the product claims or implies but that are not built.

| Feature | Where Claimed | What Is Missing | Estimated Effort |
|---------|--------------|----------------|-----------------|
| Real database authentication | `auth/services.py:74` comment | DB query, bcrypt verify, account lockout | 4h |
| TOTP enable flow | `auth/router.py:197–203` | Endpoint returns 501; no provisioning URI generation | 4h |
| FIDO2 full flow | `auth/router.py:207–441` | Register works partially; authenticate crashes (AttributeError) | 6h |
| Step-up authentication | `auth/dependencies.py:96–99` | TODO pass statement | 12h |
| Analyst feedback retraining | `qmind/kafka_consumer.py:300–335` | Stub returns static Benign result | 16h |
| PDF-quality CERT-In reports | `cert_in_generator.py` | Regex-stripped plaintext instead of structured PDF | 8h |
| HoneyGrid Docker deployment | `honeygrid.py` (not reviewed) | Depends on docker-proxy availability | Unknown |
| Playbook execution engine | `cases/router.py:135` | `TODO: Integrate with PlaybookEngine` | Unknown |
| UEBA anomaly detection | `ueba/baseline_engine.py` | Silent float conversion crash prevents any anomaly from firing | 8h |
| GenAI SOC narrative | `main.py:198–202` | SOCReportGenerator wired but LLM calls not reviewed | Unknown |
| NTA (network traffic analysis) | `main.py:10–11` | Router imported; implementation not reviewed | Unknown |

---

## Test Coverage Gaps

| Area | What Has No Test |
|------|-----------------|
| Auth | TOTP flow end-to-end; FIDO2 register + authenticate; logout JTI blacklisting; cookie-based auth; government tenant FIDO2 enforcement |
| Signals | Signal inject with Kafka unavailable; DB unavailable; confidence boundary values (0.0, 1.0, exactly); all 8 source types; unauthorized access |
| Cases | CERT-In PDF generation; timeline with zero events; action approval audit failure; duplicate case creation prevention |
| Pipeline | QMind consumer crash and restart; honeypot signal with unknown tenant_id; case creation FK failure |
| UEBA | String feature in Mahalanobis; baseline ramp-up period (<50 samples); QMind signal injection failure |
| Infrastructure | Redis connection failure graceful degradation; Vault unavailable during startup; Kafka consumer poison message |

---

## Known Bugs Not Yet Fixed

| Bug | File | Line | Severity | Workaround |
|-----|------|------|----------|------------|
| `json` not imported in auth/router.py; FIDO2 endpoints raise NameError | `auth/router.py` | 244, 267 | CRITICAL — FIDO2 completely broken | Do not use FIDO2 endpoints |
| Cookie stored with "Bearer " prefix; cookie auth always fails | `auth/router.py` | 116 | CRITICAL | Use Authorization header only |
| `authenticate_user("","")` in verify_totp crashes at create_access_token | `auth/router.py` | 157, 185 | CRITICAL — TOTP broken | Do not use TOTP |
| `request.username` on FastAPI Request in fido2_authenticate_complete | `auth/router.py` | 419, 426 | CRITICAL — FIDO2 auth broken | Do not use FIDO2 |
| `self.redis_client.setex()` on None in logout_user | `auth/services.py` | 154 | HIGH — logout crashes | Do not call logout |
| `UUID("unknown")` in qmind_consumer on honeypot signals | `qmind_consumer.py` | 69 | HIGH — consumer crashes on every honeypot signal | Do not inject honeypot signals |
| `float(current[k])` fails for string features in Mahalanobis | `ueba/baseline_engine.py` | 237 | HIGH — UEBA anomaly detection never fires | None — silent failure |
| `audit_log` table doesn't exist (schema has `audit_entries`) | `cases/router.py` | 270 | MEDIUM — timeline always returns 0 events | None |
| `asyncio.get_event_loop()` deprecated in Python 3.10+ | `qmind_consumer.py` | 197; `kafka_consumer.py` | MEDIUM — may fail in Python 3.12 | None |
| `ON CONFLICT (user_id)` wrong conflict target for `ueba_baselines` | `ueba/baseline_engine.py` | 215 | MEDIUM — wrong user baseline overwritten | None |
| case_id str not UUID → 500 on invalid input | `cases/router.py` | 67, 236 | MEDIUM | Validate UUIDs in client |
| Duplicate cases from Kafka at-least-once delivery | `cases/manager.py` | 78 | MEDIUM — multiple cases per threat | None |

---

## Architecture Shortcuts

| Shortcut | Where | What Was Done Quickly | What Should Be Done Instead |
|----------|-------|----------------------|----------------------------|
| Global mutable state for consumer dependencies | `qmind_consumer.py:17–20` | Module-level `_db_pool`, `_case_manager` set via `set_qmind_dependencies()` | Pass dependencies through constructor or FastAPI DI |
| Singleton without lifecycle management | `cases/manager.py:191–196` | First call wins; stale pool cached forever | Add `reset()` method; handle pool replacement on reconnect |
| `from app.main import app` inside route handlers | `cases/router.py:57, 77, 255` | Circular import workaround | Pass db_pool via FastAPI dependency injection |
| Category scores hardcoded, not from model | `qmind/kafka_consumer.py`, `enterprise_api.py` | Binary 1.0/0.0 for winning category | Return actual probability vector from SignalScorer |
| HTML-to-PDF via regex strip | `cert_in_generator.py:131–172` | `re.sub(r'<[^>]+>', ' ', html)` + ReportLab text | Use WeasyPrint for proper HTML→PDF conversion |
| `asyncio.get_event_loop()` instead of `get_running_loop()` | `qmind_consumer.py:197` | Deprecated API | Replace with `asyncio.get_running_loop()` |
| `SessionRiskScorer` instantiated per-request | `auth/dependencies.py:84` | New instance including GeoIP reader per request | Initialize once at startup in `lifespan()`, share via `app.state` |
| `CatBoostThreatEngine` instantiated per-request | `threat_detection/router.py:133` | New instance every signal inject | Initialize once at startup |
| Double render of CERT-In template | `cert_in_generator.py:50–118` | Render with "COMPUTING..." then render again with real values | Hash and sign the first render; embed signature without re-rendering |
| Kafka offset committed even on failed messages | `qmind/kafka_consumer.py:109` | `commit()` in `finally` block | Only commit on successful processing; use a dead-letter topic for failures |
