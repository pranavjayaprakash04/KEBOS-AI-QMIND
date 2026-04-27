#!/usr/bin/env bash
# Kebos/QMind Regression Test Suite
# Usage: bash kebos-backend/tests/regression_test.sh
# Must complete in under 5 minutes.
# Exit 0 = all pass. Exit 1 = one or more failed.

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}PASS${NC}  $1"; PASSED=$((PASSED+1)); }
fail() { echo -e "  ${RED}FAIL${NC}  $1"; FAILED=$((FAILED+1)); FAILED_LIST+=("$1"); }
info() { echo -e "  ${YELLOW}INFO${NC}  $1"; }

PASSED=0
FAILED=0
FAILED_LIST=()

BACKEND_URL="http://localhost:8000"
QMIND_URL="http://localhost:8001"

echo "============================================================"
echo "  Kebos/QMind Regression Test Suite"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# ── CHECK 1: All services running ────────────────────────────────────────────
echo "[CHECK 1] All 8 services running"
SERVICES=(kebos-backend qmind postgres redis kafka zookeeper influxdb vault)
ALL_UP=true
for svc in "${SERVICES[@]}"; do
    STATUS=$(docker-compose ps --format "{{.Service}}:{{.State}}" 2>/dev/null \
        | grep "^${svc}:" | cut -d: -f2 || echo "missing")
    if [[ "$STATUS" == "running" ]]; then
        info "$svc → running"
    else
        info "$svc → ${STATUS:-missing}"
        ALL_UP=false
    fi
done

if $ALL_UP; then
    pass "CHECK 1: All 8 services running"
else
    fail "CHECK 1: One or more services not running (see above)"
fi
echo ""

# ── CHECK 2: Login returns 200 with access_token ─────────────────────────────
echo "[CHECK 2] Login returns 200 + access_token"
LOGIN_RESPONSE=$(docker-compose exec -T kebos-backend python3 -c "
import requests
r = requests.post('http://localhost:8000/api/v1/auth/login',
    json={'username':'admin','password':'admin123'})
if r.status_code == 200 and 'access_token' in r.json():
    print('OK:' + r.json()['access_token'])
else:
    print('FAIL:status=' + str(r.status_code))
" 2>/dev/null || echo "FAIL:exec_error")

if echo "$LOGIN_RESPONSE" | grep -q "^OK:"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | sed 's/^OK://')
    pass "CHECK 2: Login → 200 + access_token (token_length=${#TOKEN})"
else
    TOKEN=""
    fail "CHECK 2: Login failed (actual: $LOGIN_RESPONSE, expected: OK:<token>)"
fi
echo ""

# ── CHECK 3: Signal inject confidence=0.85 returns 200 ──────────────────────
echo "[CHECK 3] Signal inject (confidence=0.85) → 200"
INJECT_IOC="regression-$(date +%s)-${RANDOM}.com"

if [[ -n "$TOKEN" ]]; then
    INJECT_RESPONSE=$(docker-compose exec -T kebos-backend python3 -c "
import requests
r = requests.post('http://localhost:8000/api/v1/signals/inject',
    headers={'Authorization': 'Bearer $TOKEN'},
    json={
        'threat_id': 'regression-$(date +%s)',
        'ioc_value': '$INJECT_IOC',
        'ioc_type': 'domain',
        'source_type': 'ct_log',
        'category': 'Phishing',
        'confidence': 0.85
    })
print(str(r.status_code))
" 2>/dev/null || echo "exec_error")

    if [[ "$INJECT_RESPONSE" == "200" ]]; then
        pass "CHECK 3: Signal inject → 200 (ioc=$INJECT_IOC)"
    else
        fail "CHECK 3: Signal inject failed (actual: $INJECT_RESPONSE, expected: 200)"
    fi
else
    fail "CHECK 3: Skipped — no auth token from CHECK 2"
fi
echo ""

# ── Wait for QMind pipeline to process ───────────────────────────────────────
echo "  Waiting 30s for QMind pipeline to score the signal..."
sleep 30
echo ""

# ── CHECK 4: threat_events has CONFIRMED_THREAT row ─────────────────────────
echo "[CHECK 4] threat_events → CONFIRMED_THREAT for injected IOC"
THREAT_STATUS=$(docker-compose exec -T postgres psql -U kebos -d kebos -t -c \
    "SELECT COALESCE(status, 'NOT_FOUND') FROM threat_events
     WHERE indicator_value = '$INJECT_IOC' LIMIT 1;" \
    2>/dev/null | tr -d ' \n' || echo "QUERY_ERROR")

if [[ "$THREAT_STATUS" == "CONFIRMED_THREAT" ]]; then
    pass "CHECK 4: threat_events → CONFIRMED_THREAT (actual: $THREAT_STATUS)"
elif [[ "$THREAT_STATUS" == "ELEVATED" || "$THREAT_STATUS" == "MONITORING" ]]; then
    fail "CHECK 4: Status below CONFIRMED_THREAT (actual: $THREAT_STATUS, expected: CONFIRMED_THREAT)"
elif [[ "$THREAT_STATUS" == "pending" ]]; then
    fail "CHECK 4: Pipeline stalled — still 'pending' after 30s"
else
    fail "CHECK 4: No row found or query error (actual: '$THREAT_STATUS', expected: CONFIRMED_THREAT)"
fi
echo ""

# ── CHECK 5: cases table has a new case ──────────────────────────────────────
echo "[CHECK 5] cases table → auto-created case"
CASE_COUNT=$(docker-compose exec -T postgres psql -U kebos -d kebos -t -c \
    "SELECT COUNT(*) FROM cases
     WHERE created_at > NOW() - INTERVAL '5 minutes';" \
    2>/dev/null | tr -d ' \n' || echo "0")

if [[ "$CASE_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    pass "CHECK 5: Case auto-created (count=$CASE_COUNT new cases in last 5 minutes)"
else
    fail "CHECK 5: No new case found (actual: count=${CASE_COUNT}, expected: >=1)"
fi
echo ""

# ── CHECK 6: CERT-In PDF download > 1000 bytes ───────────────────────────────
echo "[CHECK 6] CERT-In PDF download > 1000 bytes"
if [[ -n "$TOKEN" ]]; then
    CASE_ID=$(docker-compose exec -T postgres psql -U kebos -d kebos -t -c \
        "SELECT id FROM cases ORDER BY created_at DESC LIMIT 1;" \
        2>/dev/null | tr -d ' \n' || echo "")

    if [[ -n "$CASE_ID" && "$CASE_ID" != "QUERY_ERROR" ]]; then
        PDF_SIZE=$(docker-compose exec -T kebos-backend python3 -c "
import requests
r = requests.get('http://localhost:8000/api/v1/cases/$CASE_ID/cert-in-report',
    headers={'Authorization': 'Bearer $TOKEN'})
print(len(r.content) if r.status_code == 200 else 'STATUS:' + str(r.status_code))
" 2>/dev/null || echo "0")

        if [[ "$PDF_SIZE" =~ ^[0-9]+$ ]] && (( PDF_SIZE > 1000 )); then
            pass "CHECK 6: CERT-In PDF generated (size=${PDF_SIZE} bytes, expected: >1000)"
        elif echo "$PDF_SIZE" | grep -q "STATUS:"; then
            fail "CHECK 6: Report endpoint returned error (actual: $PDF_SIZE, expected: 200+PDF)"
        else
            fail "CHECK 6: PDF too small or empty (actual: ${PDF_SIZE} bytes, expected: >1000)"
        fi
    else
        fail "CHECK 6: No case ID found to test against"
    fi
else
    fail "CHECK 6: Skipped — no auth token from CHECK 2"
fi
echo ""

# ── CHECK 7: ueba_events COUNT >= 200 ────────────────────────────────────────
echo "[CHECK 7] ueba_events COUNT >= 200"
UEBA_COUNT=$(docker-compose exec -T postgres psql -U kebos -d kebos -t -c \
    "SELECT COUNT(*) FROM ueba_events;" \
    2>/dev/null | tr -d ' \n' || echo "0")

if [[ "$UEBA_COUNT" =~ ^[0-9]+$ ]] && (( UEBA_COUNT >= 200 )); then
    pass "CHECK 7: ueba_events count OK (actual: $UEBA_COUNT, expected: >=200)"
else
    fail "CHECK 7: ueba_events count too low (actual: ${UEBA_COUNT}, expected: >=200)"
fi
echo ""

# ── CHECK 8: Tenant isolation ─────────────────────────────────────────────────
echo "[CHECK 8] Tenant isolation — no orphaned records"
ORPHAN_COUNT=$(docker-compose exec -T postgres psql -U kebos -d kebos -t -c "
SELECT COUNT(*) FROM threat_events te
WHERE NOT EXISTS (SELECT 1 FROM tenants t WHERE t.id = te.tenant_id);" \
    2>/dev/null | tr -d ' \n' || echo "QUERY_ERROR")

if [[ "$ORPHAN_COUNT" == "0" ]]; then
    pass "CHECK 8: Tenant isolation — 0 orphaned threat_events (expected: 0)"
elif [[ "$ORPHAN_COUNT" == "QUERY_ERROR" ]]; then
    fail "CHECK 8: Tenant isolation query failed — tenants table may be missing"
else
    fail "CHECK 8: Orphaned records found (actual: $ORPHAN_COUNT rows without valid tenant)"
fi

RLS_COUNT=$(docker-compose exec -T postgres psql -U kebos -d kebos -t -c "
SELECT COUNT(*) FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relrowsecurity = true;" \
    2>/dev/null | tr -d ' \n' || echo "0")
info "RLS enabled on $RLS_COUNT public tables"
echo ""

# ── CHECK 9: liboqs Kyber768 KEM round-trip ──────────────────────────────────
echo "[CHECK 9] liboqs Kyber768 KEM round-trip"
KYBER_RESULT=$(docker-compose exec -T qmind python3 -c "
try:
    import oqs
    kem_a = oqs.KeyEncapsulation('Kyber768')
    pub = kem_a.generate_keypair()
    kem_b = oqs.KeyEncapsulation('Kyber768')
    ct, ss_enc = kem_b.encap_secret(pub)
    ss_dec = kem_a.decap_secret(ct)
    if ss_enc == ss_dec:
        print('OK:length=' + str(len(ss_dec)))
    else:
        print('FAIL:secret_mismatch')
except Exception as e:
    print('FAIL:' + str(e))
" 2>/dev/null || echo "FAIL:exec_error")

if echo "$KYBER_RESULT" | grep -q "^OK:"; then
    pass "CHECK 9: Kyber768 KEM round-trip OK ($KYBER_RESULT)"
else
    fail "CHECK 9: Kyber768 failed (actual: $KYBER_RESULT, expected: OK:length=32)"
fi
echo ""

# ── CHECK 10: No plaintext passwords in recent logs ──────────────────────────
echo "[CHECK 10] No plaintext passwords in recent backend logs"
PASSWORD_IN_LOGS=$(docker-compose logs --since=120s kebos-backend 2>/dev/null \
    | grep -c "admin123" || echo "0")

if [[ "$PASSWORD_IN_LOGS" == "0" ]]; then
    pass "CHECK 10: No plaintext 'admin123' in last 120s of logs"
else
    fail "CHECK 10: Plaintext password found in logs (actual: $PASSWORD_IN_LOGS occurrences, expected: 0)"
    info "  SEC-001/SEC-002: remove print/log lines at auth/router.py:79 and auth/services.py:78-79"
fi
echo ""

# ── Summary ──────────────────────────────────────────────────────────────────
echo "============================================================"
echo "  SUMMARY"
echo "============================================================"
echo -e "  ${GREEN}CHECKS PASSED: ${PASSED}/10${NC}"
echo -e "  ${RED}CHECKS FAILED: ${FAILED}/10${NC}"

if (( FAILED > 0 )); then
    echo ""
    echo "  Failed checks:"
    for item in "${FAILED_LIST[@]}"; do
        echo -e "    ${RED}✗${NC} $item"
    done
    echo ""
    echo -e "  ${RED}REGRESSION SUITE FAILED — do not demo or deploy${NC}"
    exit 1
else
    echo ""
    echo -e "  ${GREEN}ALL SYSTEMS GO${NC}"
    exit 0
fi
