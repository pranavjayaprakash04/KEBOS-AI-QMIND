# Kebos AI + QMind — Full Test Report

**Generated:** 2026-04-27  
**Platform:** Python 3.14.4 / Windows 11 / pytest 9.0.3  
**Working directory:** `kebos-backend/`  
**Excluded (cross-service imports):** `test_phase5_6.py`, `test_qmind.py`, `test_session22.py`

---

## Executive Summary

| Status  | Count | Pct   |
|---------|------:|------:|
| PASSED  |   160 |  66.7% |
| FAILED  |    60 |  25.0% |
| ERROR   |    16 |   6.7% |
| SKIPPED |     4 |   1.7% |
| **Total collected** | **240** | |

---

## Results by Test File

### `test_audit_chain.py` — 3 PASSED / 8 ERROR

| Test | Result |
|------|--------|
| TestAuditEntry::test_entry_defaults | ✅ PASSED |
| TestAuditEntry::test_entry_with_values | ✅ PASSED |
| TestAuditChain::test_compute_entry_hash | ❌ ERROR |
| TestAuditChain::test_append_creates_entry_with_signature | ❌ ERROR |
| TestAuditChain::test_hash_chain_links_correctly | ❌ ERROR |
| TestAuditChain::test_last_hash_updates_after_append | ❌ ERROR |
| TestVerifyChain::test_verify_chain_returns_true_for_valid_chain | ❌ ERROR |
| TestVerifyChain::test_verify_chain_returns_false_if_hash_link_broken | ❌ ERROR |
| TestVerifyChain::test_verify_chain_returns_false_if_tampered | ❌ ERROR |
| TestPQCSigning::test_dilithium_signature_non_empty_when_liboqs_available | ❌ ERROR |
| TestPQCSigning::test_pqc_signing_flag_is_boolean | ✅ PASSED |

**Root cause:** `generate_keypair()` (from `liboqs-python`) returns an empty tuple on this machine because `liboqs` (the C library) is not installed in the local venv. It is only available inside the `qmind` Docker container. All 8 ERRORs are fixture setup failures — `signing_key` fixture calls `generate_keypair()` and gets `ValueError: not enough values to unpack (expected 2, got 0)`.

**Fix:** Install `liboqs` natively, or mock `generate_keypair` in the fixture to return synthetic bytes for unit-testing purposes.

---

### `test_auth.py` — 10 PASSED / 20 FAILED

| Test | Result |
|------|--------|
| TestPhase11Auth::test_login_returns_httponly_cookie | ❌ FAILED |
| TestPhase11Auth::test_auth_me_returns_401_without_cookie | ✅ PASSED |
| TestPhase11Auth::test_auth_me_returns_user_with_valid_cookie | ❌ FAILED |
| TestPhase11Auth::test_logout_invalidates_token | ❌ FAILED |
| TestPhase11Auth::test_hs256_token_is_rejected | ✅ PASSED |
| TestPhase11Auth::test_expired_token_is_rejected | ❌ FAILED |
| TestPhase11Auth::test_endpoint_rejects_request_without_valid_jwt | ✅ PASSED |
| TestPhase12TotpAndGovernment::test_totp_secret_stored_encrypted | ❌ FAILED |
| TestPhase12TotpAndGovernment::test_totp_verification_methods_exist | ✅ PASSED |
| TestPhase12TotpAndGovernment::test_government_tenant_without_fido2_gets_403 | ❌ FAILED |
| TestPhase12TotpAndGovernment::test_fido2_skeleton_endpoints_exist | ❌ FAILED |
| TestPhase13SessionRiskAndSecurityHeaders::test_impossible_travel_triggers_401 | ❌ FAILED |
| TestPhase13SessionRiskAndSecurityHeaders::test_security_headers_present_on_every_response | ✅ PASSED |
| TestPhase13SessionRiskAndSecurityHeaders::test_x_pqc_status_header_present_on_every_response | ✅ PASSED |
| TestPhase13SessionRiskAndSecurityHeaders::test_validate_environment_succeeds_with_correct_settings | ✅ PASSED |
| TestPhase13SessionRiskAndSecurityHeaders::test_validate_environment_raises_systemexit_on_hs256 | ✅ PASSED |
| TestPhase13SessionRiskAndSecurityHeaders::test_validate_environment_raises_systemexit_on_gt_15min_expiry | ✅ PASSED |
| TestPhase13bEmergencyRotation::test_non_admin_gets_403_on_emergency_rotation | ❌ FAILED |
| TestPhase13bEmergencyRotation::test_emergency_rotation_requires_fido2_header | ❌ FAILED |
| TestPhase13bEmergencyRotation::test_emergency_rotation_flushes_jti_tokens | ❌ FAILED |
| TestPhase13bEmergencyRotation::test_emergency_rotation_completes_under_5_min | ❌ FAILED |
| TestPhase13bEmergencyRotation::test_jti_blacklist_key_uses_tenant_id_namespace | ❌ FAILED |
| TestFido2Implementation::test_fido2_register_begin_returns_challenge | ❌ FAILED |
| TestFido2Implementation::test_fido2_register_complete_stores_credential | ❌ FAILED |
| TestFido2Implementation::test_geoip_lookup_returns_lat_lon | ❌ FAILED |
| TestFido2Implementation::test_impossible_travel_raises_401_when_speed_gt_900_kmh | ❌ FAILED |
| TestEmergencyRotation::test_emergency_rotation_completes_under_5_minutes | ✅ PASSED |
| TestEmergencyRotation::test_emergency_rotation_flushes_all_jti_keys | ❌ FAILED |
| TestEmergencyRotation::test_tokens_issued_before_rotation_timestamp_are_rejected | ❌ FAILED |
| TestEmergencyRotation::test_emergency_rotation_endpoint_returns_403_without_admin_role | ❌ FAILED |

**Root causes (5 categories):**

1. **No seeded test user** (`assert 401 == 200` on login with `admin`/`admin`): The test uses `TestClient` against the live app but the DB has no `admin` user seeded. Affects: `test_login_returns_httponly_cookie`, `test_auth_me_returns_user_with_valid_cookie`, `test_logout_invalidates_token`, `test_fido2_register_begin_returns_challenge`, `test_emergency_rotation_requires_fido2_header`, `test_non_admin_gets_403_on_emergency_rotation`, `test_emergency_rotation_endpoint_returns_403_without_admin_role`.

2. **`coroutine` returned instead of user object** (`AttributeError: 'coroutine' object has no attribute 'id'`): `test_expired_token_is_rejected` — test code calls an async auth method without `await`, getting a coroutine not a User.

3. **Missing migration file** (`alembic/versions/001_add_totp_encrypted.py` not found): `test_totp_secret_stored_encrypted` checks for existence of a migration file that was deleted in the clean repo.

4. **`SessionRiskScorer.__init__()` missing `redis_client`**: Tests instantiate `SessionRiskScorer()` with no args but the constructor was updated to require a Redis client. Affects: `test_impossible_travel_triggers_401`, `test_geoip_lookup_returns_lat_lon`, `test_impossible_travel_raises_401_when_speed_gt_900_kmh`.

5. **`RotationResult` missing attributes**: `test_emergency_rotation_flushes_jti_tokens` expects `.sessions_flushed`; `test_emergency_rotation_completes_under_5_min` expects `.elapsed_seconds`. These attributes were renamed in the implementation. Also, `async for key in redis.scan_iter(...)` fails because `scan_iter` mock is not set up as an async iterator.

6. **`asyncio.run()` inside running event loop**: `test_jti_blacklist_key_uses_tenant_id_namespace` and `test_tokens_issued_before_rotation_timestamp_are_rejected` call `asyncio.run()` inside a pytest-asyncio test (which already has a running loop) — should use `await` instead.

7. **`verify_registration_response` not in `app.auth.router`**: `test_fido2_register_complete_stores_credential` patches a symbol that doesn't exist there — possibly moved to a different module.

8. **GeoIP DB not present**: `test_geoip_lookup_returns_lat_lon` fails because the GeoLite2 `.mmdb` file is not present locally.

---

### `test_catboost_kafka.py` — 9 PASSED / 1 FAILED

| Test | Result |
|------|--------|
| TestCatBoostThreatEngine::test_score_returns_0_5_when_model_not_loaded | ✅ PASSED |
| TestCatBoostThreatEngine::test_indian_brand_domain_gets_has_indian_brand_1 | ✅ PASSED |
| TestCatBoostThreatEngine::test_source_confidence_prior | ✅ PASSED |
| TestCatBoostThreatEngine::test_ip_is_indian_asn | ✅ PASSED |
| TestCatBoostThreatEngine::test_extract_domain_features_entropy | ✅ PASSED |
| TestCatBoostThreatEngine::test_extract_domain_features_subdomain_depth | ✅ PASSED |
| TestThreatIndicatorPublisher::test_publish_sends_correct_message_to_kafka_topic | ✅ PASSED |
| TestThreatIndicatorPublisher::test_publisher_start_must_be_called_before_publish | ✅ PASSED |
| TestThreatIndicatorPublisher::test_start_initializes_producer | ❌ FAILED |
| TestThreatIndicatorPublisher::test_stop_stops_producer | ✅ PASSED |

**Root cause:** `test_start_initializes_producer` asserts `call_kwargs["compression_type"] == "lz4"` but the `AIOKafkaProducer` constructor call in `kafka_producer.py` does not include a `compression_type` kwarg (or it's named differently). Fix: add `compression_type="lz4"` to the `AIOKafkaProducer()` constructor call in `kafka_producer.py`.

---

### `test_cert_in_generator.py` — 7 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| test_generate_returns_nonempty_pdf | ✅ PASSED |
| test_pdf_contains_indicator | ✅ PASSED |
| test_dilithium_signature_in_output | ✅ PASSED |
| test_no_signing_key_still_generates | ✅ PASSED |
| test_generation_time_logged | ✅ PASSED |
| test_generation_time_warning_when_slow | ✅ PASSED |
| test_report_id_format | ✅ PASSED |

---

### `test_cert_in_report.py` — 3 PASSED / 2 FAILED

| Test | Result |
|------|--------|
| TestCERTInReportGenerator::test_generate_returns_non_empty_bytes | ✅ PASSED |
| TestCERTInReportGenerator::test_generated_pdf_contains_indicator_value | ✅ PASSED |
| TestCERTInReportGenerator::test_dilithium_signature_embedded_in_output | ✅ PASSED |
| TestCERTInReportGenerator::test_generation_time_is_logged | ❌ FAILED |
| TestCERTInReportGenerator::test_generation_logs_warning_if_slow | ❌ FAILED |

**Root causes:**

- `test_generation_time_is_logged`: Test asserts `"CERT-In report generated in" in log_call_args` but the actual log message is `"CERT-In report KEBOS-20260427173623-9F9BBAB5 generated in 0.02s"` — the assertion string doesn't match because the test serializes `call()` as a string and searches inside it. The log prefix includes the report ID. Fix: update assertion to `"generated in"` or use a regex.

- `test_generation_logs_warning_if_slow`: The slow-path warning is never triggered because mocked time doesn't simulate a slow generation. Fix: mock `time.monotonic` or `datetime.now` to return a value that exceeds the slow threshold.

---

### `test_dependency_health.py` — 11 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| test_all_feeds_down_sets_max_confidence_cap_0_65 | ✅ PASSED |
| test_qmind_down_sets_max_confidence_cap_0_60 | ✅ PASSED |
| test_groq_down_sets_soc_report_mode_jinja2_only | ✅ PASSED |
| test_vault_down_sets_read_only_mode | ✅ PASSED |
| test_kafka_down_sets_qmind_transport_http | ✅ PASSED |
| test_redis_down_sets_rate_limit_backend_db | ✅ PASSED |
| test_certstream_down_sets_ct_monitor_mode_whoisxml_fallback | ✅ PASSED |
| test_abuseipdb_down_logs_warning | ✅ PASSED |
| test_cloudflare_down_logs_warning | ✅ PASSED |
| test_check_all_feeds_status | ✅ PASSED |
| test_all_9_degradation_policies_registered | ✅ PASSED |

---

### `test_egress_and_syslog.py` — 8 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| TestEgressControlledClient::test_blocks_unknown_domain_in_strict_mode | ✅ PASSED |
| TestEgressControlledClient::test_allows_certstream_calidog_io | ✅ PASSED |
| TestEgressControlledClient::test_applies_10s_default_timeout | ✅ PASSED |
| TestEgressControlledClient::test_non_strict_mode_logs_warning | ✅ PASSED |
| TestTLSSyslogHandler::test_initialises_with_tcp_socket_not_udp | ✅ PASSED |
| TestTLSSyslogHandler::test_setup_tls_syslog_no_op_when_host_empty | ✅ PASSED |
| TestTLSSyslogHandler::test_setup_tls_syslog_adds_handler_when_host_configured | ✅ PASSED |
| TestTLSSyslogHandler::test_emit_with_lock_thread_safety | ✅ PASSED |

---

### `test_genai_assistant.py` — 17 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| TestLLMDataSanitiser::test_sanitiser_strips_source_ip_from_payload | ✅ PASSED |
| TestLLMDataSanitiser::test_sanitiser_raises_value_error_for_confidential_classification | ✅ PASSED |
| TestLLMDataSanitiser::test_sanitiser_raises_value_error_for_restricted_classification | ✅ PASSED |
| TestLLMDataSanitiser::test_sanitiser_raises_assertion_error_if_never_external_field_leaks | ✅ PASSED |
| TestLLMDataSanitiser::test_sanitiser_only_includes_safe_fields | ✅ PASSED |
| TestLLMDataSanitiser::test_sanitiser_handles_empty_payload | ✅ PASSED |
| TestLLMRouter::test_router_returns_local_gemma_for_government_tenants | ✅ PASSED |
| TestLLMRouter::test_router_returns_local_gemma_for_confidential_data | ✅ PASSED |
| TestLLMRouter::test_router_returns_local_gemma_for_restricted_data | ✅ PASSED |
| TestLLMRouter::test_router_returns_groq_for_public_data_when_api_key_set | ✅ PASSED |
| TestLLMRouter::test_router_returns_groq_for_internal_data_when_api_key_set | ✅ PASSED |
| TestLLMRouter::test_router_fallback_to_local_gemma_when_no_groq_key | ✅ PASSED |
| TestLLMRouter::test_router_raises_value_error_for_unknown_classification | ✅ PASSED |
| TestGroqClient::test_groq_client_initialization | ✅ PASSED |
| TestGroqClient::test_groq_client_default_model | ✅ PASSED |
| TestLocalGemmaClient::test_local_gemma_client_initialization | ✅ PASSED |
| TestLocalGemmaClient::test_local_gemma_client_default_url | ✅ PASSED |

---

### `test_honeygrid.py` — 7 PASSED / 12 FAILED

| Test | Result |
|------|--------|
| TestHoneyGrid::test_create_aws_honeytoken | ❌ FAILED |
| TestHoneyGrid::test_create_database_honeytoken | ❌ FAILED |
| TestHoneyGrid::test_create_api_token_honeytoken | ❌ FAILED |
| TestHoneyGrid::test_create_honeytoken_with_custom_value | ❌ FAILED |
| TestHoneyGrid::test_honeytoken_types_enum | ✅ PASSED |
| TestSIEMFormatter::test_cef_format | ✅ PASSED |
| TestSIEMFormatter::test_cef_escaping | ✅ PASSED |
| TestSIEMFormatter::test_threat_cef_format | ✅ PASSED |
| TestSIEMFormatter::test_honeytoken_trigger_cef_format | ✅ PASSED |
| TestSIEMFormatter::test_stix_indicator_format | ✅ PASSED |
| TestSIEMFormatter::test_stix_sighting_format | ✅ PASSED |
| TestEgressControl::test_egress_domain_validation | ❌ FAILED |
| TestEgressControl::test_egress_timeout_is_10_seconds | ❌ FAILED |
| TestEgressControl::test_allowed_domains_list | ❌ FAILED |
| TestHoneypotManager::test_connects_to_docker_proxy_not_socket | ❌ FAILED |
| TestHoneypotManager::test_deploy_honeypot_raises_valueerror_for_invalid_ip | ❌ FAILED |
| TestHoneypotManager::test_deploy_honeypot_valid_ip_succeeds | ❌ FAILED |
| TestHoneypotManager::test_parse_cowrie_logs_extracts_source_ips | ❌ FAILED |
| TestHoneypotManager::test_extract_iocs_and_inject_calls_signals_inject | ❌ FAILED |

**Root causes (4 categories):**

1. **`create_honeytoken()` is async, called without `await`** (`AttributeError: 'coroutine' object has no attribute 'token_type'`): All 4 `TestHoneyGrid` creates call the method synchronously. Tests must use `await` and `@pytest.mark.asyncio`.

2. **`EgressControlledClient` API mismatch**:
   - `_validate_domain()` method doesn't exist (no such public method) — test must call the validation differently
   - `.timeout` is an httpx `Timeout` object, not a plain `float` — assert `client.timeout.timeout == 10.0`
   - `EgressControlledClient.ALLOWED_DOMAINS` class attribute doesn't exist — the allowed list is stored elsewhere (in `settings.ALLOWED_EGRESS_DOMAINS`)

3. **Docker socket not accessible from host** (`docker-proxy:2375` DNS resolution fails): `HoneypotManager.__init__()` connects to Docker at `tcp://docker-proxy:2375` which resolves only inside the Docker network. Any test that constructs `HoneypotManager()` directly on the host machine will fail. The other HoneypotManager tests also fail because async test functions lack `@pytest.mark.asyncio`.

4. **`call[0][0]` IndexError on `call_args_list`**: `test_connects_to_docker_proxy_not_socket` iterates `mock_docker_client.call_args_list` and accesses `call[0][0]` — the call tuple structure doesn't have positional args in index 0, causing `IndexError: tuple index out of range`.

---

### `test_phase3_4.py` — 13 PASSED / 10 FAILED / 2 ERROR

| Test | Result |
|------|--------|
| TestEgressControlledClient::test_allowed_domain | ✅ PASSED |
| TestEgressControlledClient::test_blocked_domain_strict_mode | ✅ PASSED |
| TestEgressControlledClient::test_timeout_configured | ✅ PASSED |
| TestEgressControlledClient::test_get_singleton | ✅ PASSED |
| TestCERTInReportGenerator::test_generate_report | ❌ FAILED |
| TestCERTInReportGenerator::test_jinja2_fallback | ✅ PASSED |
| TestCERTInSLAMonitor::test_alert_threshold_hours | ✅ PASSED |
| TestCERTInSLAMonitor::test_five_hour_alert | ❌ FAILED |
| TestCERTInSLAMonitor::test_six_hour_breach | ❌ FAILED |
| TestHoneyGridManager::test_docker_proxy_url | ❌ ERROR |
| TestHoneyGridManager::test_honeypot_images | ❌ ERROR |
| TestHoneytokenManager::test_token_types | ✅ PASSED |
| TestHoneytokenManager::test_token_generation | ✅ PASSED |
| TestDigitalTwinSimulator::test_simulate_action_not_stub | ❌ FAILED |
| TestDigitalTwinSimulator::test_impact_score_range | ❌ FAILED |
| TestDigitalTwinSimulator::test_recommendation_threshold | ❌ FAILED |
| TestDigitalTwinSimulator::test_empty_history_conservative | ❌ FAILED |
| TestCEFSyslogForwarder::test_format_event | ✅ PASSED |
| TestSTIXExporter::test_to_indicator | ❌ FAILED |
| TestSTIXExporter::test_to_bundle | ❌ FAILED |
| TestSplunkHECClient::test_index_configured | ❌ FAILED |
| TestSplunkHECClient::test_hec_url_from_settings | ✅ PASSED |
| TestConfigSettings::test_certstream_in_allowlist | ✅ PASSED |
| TestConfigSettings::test_egress_strict_mode | ✅ PASSED |
| TestConfigSettings::test_splunk_settings | ✅ PASSED |

**Root causes:**

1. **`HoneyGridManager.__init__()` takes 1 positional argument but 2 were given** (ERROR): Test fixture passes `mock_db_pool` to `HoneyGridManager(mock_db_pool)` but the current implementation takes no arguments. Fix: update `HoneyGridManager.__init__` to accept an optional `db_pool` parameter.

2. **`db_pool.acquire()` returns coroutine, not context manager**: `test_generate_report` and all 4 `TestDigitalTwinSimulator` tests fail because their mock's `acquire()` is an `AsyncMock` (returns a coroutine) but the code does `async with self.db_pool.acquire() as conn:`. Fix the mock: `mock_pool.acquire = MagicMock(return_value=AsyncContextManager())` — or apply the `inspect.isawaitable()` pattern in those methods too.

3. **CERT-In SLA Monitor tests** (`test_five_hour_alert`, `test_six_hour_breach`): `mock_conn.execute.assert_called()` fails — `execute` was never called. The SLA monitor logic may use `fetchrow` or `fetch` rather than `execute`, or the mock async context manager isn't configured correctly.

4. **STIX Exporter — invalid STIX ID format**: `test_to_indicator` passes IOC with `id="IOC-001"` but `stix2.Indicator` requires `id` in the format `<object-type>--<UUID>`. Fix: in `stix_export.py`, generate a valid UUID for the STIX indicator ID rather than using the raw IOC ID.

5. **STIX bundle has only 1 object** (`test_to_bundle` asserts `len >= 2`): Because `to_indicator()` fails for the test IOC (same UUID issue), the bundle contains only the Identity object. Fixing the UUID issue in #4 will fix this too.

6. **Splunk index mismatch** (`test_index_configured` expects `"kebos_threats"`, default is `"kebos"`): Irreconcilable conflict between this test and `test_siem_integration.py::test_send_event_with_token` which expects `"kebos"`. One test file must be updated to match the canonical default.

---

### `test_qmind_consumer.py` — 12 PASSED / 8 FAILED

| Test | Result |
|------|--------|
| TestUpdateThreatWithQMindResult::test_confirmed_threat_at_threshold | ❌ FAILED |
| TestUpdateThreatWithQMindResult::test_benign_below_monitoring_threshold | ❌ FAILED |
| TestUpdateThreatWithQMindResult::test_not_a_pass_stub | ✅ PASSED |
| TestUpdateThreatWithQMindResult::test_government_uses_0_70_threshold_not_0_75 | ❌ FAILED |
| TestUpdateThreatWithQMindResult::test_government_0_69_is_elevated_not_confirmed | ❌ FAILED |
| TestUpdateThreatWithQMindResult::test_confirmed_threat_triggers_case_creation | ✅ PASSED |
| TestUpdateThreatWithQMindResult::test_confirmed_threat_triggers_audit_logging | ✅ PASSED |
| TestUpdateThreatWithQMindResult::test_bfsi_uses_0_72_threshold | ❌ FAILED |
| TestUpdateThreatWithQMindResult::test_elevated_status_between_thresholds | ❌ FAILED |
| TestUpdateThreatWithQMindResult::test_monitoring_status_at_threshold | ❌ FAILED |
| TestUpdateThreatWithQMindResult::test_handles_missing_optional_fields | ❌ FAILED |
| TestTenantThresholds::test_government_thresholds | ✅ PASSED |
| TestTenantThresholds::test_bfsi_thresholds | ✅ PASSED |
| TestTenantThresholds::test_enterprise_thresholds | ✅ PASSED |
| TestHandleTaskError::test_handle_task_error_logs_exception | ✅ PASSED |
| TestHandleTaskError::test_handle_task_error_ignores_cancelled_tasks | ✅ PASSED |
| TestHandleTaskError::test_handle_task_error_auto_restarts_qmind_consumer | ✅ PASSED |
| TestHandleTaskError::test_handle_task_error_no_restart_for_non_qmind_tasks | ✅ PASSED |
| TestSetQMindDependencies::test_set_dependencies_sets_globals | ✅ PASSED |

**Root cause:** All 8 failures share the same error: `TypeError: 'AsyncMock' object can't be awaited` at `conn = await _db_pool.acquire()`. This is a Python 3.14 breaking change — `await AsyncMock_instance` was removed; `AsyncMock()` now returns the mock itself which cannot be awaited. The test code at line 74 does `conn = await _db_pool.acquire()` but `acquire()` (which is an `AsyncMock`) should return an async context manager, not be awaited directly. Fix: rewrite the test mock setup to use `AsyncMock` as a context manager (`async with db_pool.acquire() as conn:`), or use the `inspect.isawaitable()` pattern in the production code and mock accordingly.

---

### `test_session25.py` — 5 PASSED / 2 FAILED

| Test | Result |
|------|--------|
| test_cef_format_produces_valid_cef_string | ❌ FAILED |
| test_splunk_hec_skips_when_not_configured | ✅ PASSED |
| test_enrich_endpoint_returns_category_scores | ✅ PASSED |
| test_stix_bundle_returns_valid_json | ✅ PASSED |
| test_silverterrier_in_threat_actors | ✅ PASSED |
| test_revil_in_threat_actors | ✅ PASSED |
| test_timeline_endpoint_returns_buckets | ❌ FAILED |

**Root causes:**

1. **CEF vendor string mismatch**: Test asserts `cef_line.startswith("CEF:0|Pynevera Technologies|KebosAI|1.0")` but `cef_forwarder.py` emits `"CEF:0|Pynevera|KebosAI|1.0"`. Fix: update `cef_forwarder.py` to use `"Pynevera Technologies"` as the vendor field (or update the test to match the current value).

2. **`KeyError: 'timestamp'` in `get_case_timeline()`**: The DB row dict doesn't have a `'timestamp'` key — the column was likely returned under a different name (e.g., `event_time` or `created_at`). Fix: check the actual column name in `cases/router.py:286` and map it correctly.

---

### `test_session26.py` — 3 PASSED / 3 FAILED / 4 SKIPPED

| Test | Result |
|------|--------|
| test_geoip_returns_zero_when_not_configured | ✅ PASSED |
| test_geoip_returns_nonzero_for_public_ip | ✅ PASSED |
| test_private_ip_returns_zero | ✅ PASSED |
| test_login_returns_mfa_required_when_totp_enabled | ⏭ SKIPPED |
| test_verify_totp_correct_code_sets_cookie | ⏭ SKIPPED |
| test_verify_totp_wrong_code_returns_401 | ⏭ SKIPPED |
| test_verify_totp_replay_blocked | ⏭ SKIPPED |
| test_vault_dev_mode_logs_warning | ❌ FAILED |
| test_feedback_stored_on_correction_submission | ❌ FAILED |
| test_retraining_triggered_at_100_corrections | ❌ FAILED |

**Root causes:**

1. **`test_vault_dev_mode_logs_warning`**: `mock_logger.warning.assert_called_once()` — the warning is not triggered because the vault dev-mode check logic either doesn't log via the mocked logger or the condition isn't met with the mock settings.

2. **`test_feedback_stored_on_correction_submission` & `test_retraining_triggered_at_100_corrections`**: `mock_pool.acquire.return_value.__aenter__` raises `AttributeError: __aenter__` — the `Mock()` object returned by `acquire.return_value` is not an async context manager. Fix: use `AsyncMock` with `__aenter__` and `__aexit__` properly configured, e.g.: `mock_pool.acquire.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock(return_value=None))`.

**SKIPPED reason:** TOTP tests are skipped — they require a running Redis instance for replay-attack checking.

---

### `test_session28.py` — 9 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| TestGeoIPExtraction::test_private_ip_returns_zero_zero | ✅ PASSED |
| TestGeoIPExtraction::test_loopback_returns_zero_zero | ✅ PASSED |
| TestGeoIPExtraction::test_invalid_ip_returns_zero_zero | ✅ PASSED |
| TestGeoIPExtraction::test_geoip_reader_none_returns_gracefully | ✅ PASSED |
| TestVaultSecretManager::test_vault_initialise_no_config | ✅ PASSED |
| TestVaultSecretManager::test_vault_get_secret_fallback | ✅ PASSED |
| TestVaultSecretManager::test_vault_is_ready_property | ✅ PASSED |
| TestTimelineEndpoint::test_timeline_models_exist | ✅ PASSED |
| TestTimelineEndpoint::test_timeline_events_chronological_sorting | ✅ PASSED |

---

### `test_siem_integration.py` — 15 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| TestCEFSyslogForwarder::test_format_event_confirmed_threat | ✅ PASSED |
| TestCEFSyslogForwarder::test_format_event_elevated | ✅ PASSED |
| TestCEFSyslogForwarder::test_format_event_monitoring | ✅ PASSED |
| TestCEFSyslogForwarder::test_format_event_benign | ✅ PASSED |
| TestCEFSyslogForwarder::test_format_event_missing_fields | ✅ PASSED |
| TestCEFSyslogForwarder::test_forward_with_syslog_handler | ✅ PASSED |
| TestCEFSyslogForwarder::test_forward_without_syslog_handler | ✅ PASSED |
| TestSplunkHECClient::test_init_with_params | ✅ PASSED |
| TestSplunkHECClient::test_init_defaults | ✅ PASSED |
| TestSplunkHECClient::test_send_event_skips_when_no_token | ✅ PASSED |
| TestSplunkHECClient::test_send_event_with_token | ✅ PASSED |
| TestSplunkHECClient::test_send_event_handles_error | ✅ PASSED |
| TestSIEMRouter::test_enrich_endpoint_requires_auth | ✅ PASSED |
| TestSIEMRouter::test_enrich_endpoint_calls_qmind | ✅ PASSED |
| TestSIEMRouter::test_stix_bundle_endpoint | ✅ PASSED |

---

### `test_simulation.py` — 7 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| TestDigitalTwinSimulator::test_simulate_action_returns_simulation_result_with_valid_impact_score | ✅ PASSED |
| TestDigitalTwinSimulator::test_simulate_action_is_not_a_pass_stub | ✅ PASSED |
| TestDigitalTwinSimulator::test_empty_history_returns_impact_score_1_0_conservative | ✅ PASSED |
| TestDigitalTwinSimulator::test_impact_score_ge_0_05_returns_block_pending_investigation | ✅ PASSED |
| TestDigitalTwinSimulator::test_impact_score_lt_0_05_returns_present_to_analyst | ✅ PASSED |
| TestDigitalTwinSimulator::test_block_ip_action_matches_only_target_ip_in_history | ✅ PASSED |
| TestDigitalTwinSimulator::test_is_confirmed_threat | ✅ PASSED |

---

### `test_soc_generator.py` — 13 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| TestSOCReportGenerator::test_wire_llm_clients_sets_both_clients_non_none | ✅ PASSED |
| TestSOCReportGenerator::test_generate_incident_report_raises_runtime_error_if_llm_client_none | ✅ PASSED |
| TestSOCReportGenerator::test_generate_incident_report_uses_json_mode_not_string_parsing | ✅ PASSED |
| TestSOCReportGenerator::test_prompt_injection_in_llm_output_falls_back_to_jinja2 | ✅ PASSED |
| TestSOCReportGenerator::test_json_parse_failure_falls_back_to_jinja2_template | ✅ PASSED |
| TestSOCReportGenerator::test_government_tenant_always_uses_gemma_client | ✅ PASSED |
| TestSOCReportGenerator::test_confidential_classification_uses_gemma_client | ✅ PASSED |
| TestSOCReportGenerator::test_restricted_classification_uses_gemma_client | ✅ PASSED |
| TestSOCReportGenerator::test_jinja2_fallback_when_client_is_none | ✅ PASSED |
| TestSOCReportGenerator::test_injection_patterns_contains_expected_patterns | ✅ PASSED |
| TestSOCReportGenerator::test_jinja2_fallback_renders_template_correctly | ✅ PASSED |
| TestSOCReport::test_soc_report_dataclass_fields | ✅ PASSED |
| TestSOCReport::test_soc_report_fallback_used_default | ✅ PASSED |

---

### `test_tenant_isolation.py` — 0 PASSED / 2 FAILED

| Test | Result |
|------|--------|
| test_tenant_isolation | ❌ FAILED |
| test_tenant_isolation_all_tables | ❌ FAILED |

**Root cause:** Both tests attempt a direct `asyncpg.connect(settings.DATABASE_URL)` to `postgresql://user:pass@localhost:5432/kebos`. PostgreSQL is running inside Docker on an `internal: true` network — it is not accessible from the Windows host on port 5432. Fix: expose port 5432 from the postgres container in `docker-compose.yml`, or run these tests from inside the Docker network.

---

### `test_tip_mitre_mapping.py` — 8 PASSED / 0 FAILED

| Test | Result |
|------|--------|
| test_all_5_threat_actor_profiles_exist | ✅ PASSED |
| test_silverterrier_profile_structure | ✅ PASSED |
| test_revil_affiliates_profile_structure | ✅ PASSED |
| test_get_threat_actor_profile | ✅ PASSED |
| test_get_all_threat_actors | ✅ PASSED |
| test_mitre_techniques_mapping | ✅ PASSED |
| test_map_category_to_mitre | ✅ PASSED |
| test_all_threat_actors_have_required_fields | ✅ PASSED |

---

### `test_ueba_baseline.py` — 0 PASSED / 6 ERROR

| Test | Result |
|------|--------|
| test_seed_baselines_creates_minimum_50_events_per_user | ❌ ERROR |
| test_compute_anomaly_score_non_zero_for_anomalous_request | ❌ ERROR |
| test_normal_request_returns_low_score | ❌ ERROR |
| test_baseline_without_minimum_samples_returns_zero | ❌ ERROR |
| test_seed_baselines_creates_correct_baseline_features | ❌ ERROR |
| test_mahalanobis_distance_computation | ❌ ERROR |

**Root cause:** All 6 tests require a `db_pool` pytest fixture which is not defined anywhere in the test suite (no `conftest.py` provides it). The tests are integration tests that require a live asyncpg connection pool pointing at the PostgreSQL database. Fix: add a `db_pool` fixture to `conftest.py` that creates an asyncpg pool, or mock the pool as an `AsyncMock` at the fixture level.

---

### Excluded Files (Cross-Service Imports)

| File | Reason |
|------|--------|
| `test_phase5_6.py` | Imports from `qmind_enterprise` package — only available in the QMind container |
| `test_qmind.py` | Imports from `signal_engine` — only available in the QMind container |
| `test_session22.py` | Cross-service imports not resolvable from `kebos-backend` Python path |

---

## Failure Classification Summary

| Category | Tests Affected | Count |
|----------|---------------|------:|
| **Infrastructure not available** (DB, Redis, Docker, GeoIP, liboqs) | test_tenant_isolation (2), test_auth Redis/GeoIP/FIDO2 (5), test_audit_chain liboqs (8), test_ueba_baseline db_pool (6) | 21 |
| **Python 3.14 AsyncMock breaking change** (`await AsyncMock` removed) | test_qmind_consumer (8), test_session26 (2) | 10 |
| **Mock setup incorrect** (not async context manager) | test_phase3_4 db_pool (4+1), test_honeygrid async (4) | 9 |
| **Hardcoded test user not seeded in DB** | test_auth login failures (7+1) | 8 |
| **Implementation/test string mismatch** | test_session25 CEF vendor (1), test_phase3_4 Splunk index (1), test_phase3_4 STIX ID (2), test_catboost lz4 kwarg (1), test_cert_in_report log msg (2), test_session26 vault warning (1) | 8 |
| **Missing symbol / attribute** | test_auth RotationResult attrs (2+1), test_auth SessionRiskScorer args (3), test_honeygrid EgressClient attrs (3), test_auth verify_registration_response (1) | 10 |
| **Missing alembic migration file** | test_auth (1) | 1 |
| **asyncio.run() in async test** | test_auth (2) | 2 |
| **KeyError in production code** | test_session25 timeline timestamp (1) | 1 |

---

## Priority Fix Order

### P0 — Quick wins (code-only, 1-line fixes)
1. **`cef_forwarder.py`**: Change `"Pynevera"` → `"Pynevera Technologies"` to fix `test_session25::test_cef_format_produces_valid_cef_string`
2. **`cases/router.py:286`**: Fix `row["timestamp"]` KeyError — check actual DB column name returned
3. **`kafka_producer.py`**: Add `compression_type="lz4"` to `AIOKafkaProducer()` constructor

### P1 — Mock setup fixes (test-side, no prod change)
4. **`test_phase3_4.py` DigitalTwinSimulator + CERTIn**: Fix `db_pool.acquire()` mock to return async context manager (not `AsyncMock`)
5. **`test_session26.py`**: Fix `mock_pool.acquire` mock to use `AsyncMock` with `__aenter__`/`__aexit__`
6. **`test_honeygrid.py` HoneyGrid create tests**: Add `@pytest.mark.asyncio` and `await` to `create_honeytoken()` calls

### P2 — Production code fixes
7. **`stix_export.py`**: Generate proper UUID-format STIX ID for Indicator (not raw IOC ID string)
8. **`HoneyGridManager.__init__`**: Accept optional `db_pool` parameter (test fixture passes one)
9. **`RotationResult`**: Add `.sessions_flushed` and `.elapsed_seconds` attributes (or rename test assertions to match current field names)
10. **`vault_breach.py:190`**: Fix `async for key in redis.scan_iter(...)` — scan_iter mock not configured as async iterator

### P3 — Infrastructure setup required
11. **`test_tenant_isolation`**: Expose PostgreSQL port 5432 from Docker to host
12. **`test_ueba_baseline`**: Add `db_pool` fixture to `conftest.py`
13. **`test_auth` login tests**: Seed a test `admin` user in the test DB / use mocked auth service
14. **`test_auth` GeoIP/FIDO2**: Mount GeoLite2 DB or mock it; provide FIDO2 test credentials
15. **`test_audit_chain` liboqs**: Install `liboqs` C library locally or mock `generate_keypair`

---

## Warnings (Non-Blocking)

| Warning | Locations |
|---------|-----------|
| `PydanticDeprecatedSince20`: class-based `Config` → use `ConfigDict` | `app/config.py` |
| `datetime.utcnow()` deprecated (Python 3.14 warning) | `kafka_producer.py`, `qmind_consumer.py`, `formatter.py` |
| `asyncio.iscoroutinefunction()` deprecated in 3.14 | `slowapi` library (third-party) |
| Cookie persistence deprecation in Starlette TestClient | `test_auth.py` multiple tests |
