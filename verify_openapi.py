import json
import sys

spec = json.load(sys.stdin)
paths = spec.get('paths', {})

required = [
    ('get',   '/api/v1/threats/'),
    ('post',  '/api/v1/threats/ingest'),
    ('patch', '/api/v1/threats/{threat_id}'),
    ('get',   '/api/v1/cases/'),
    ('post',  '/api/v1/cases/'),
    ('get',   '/api/v1/cases/{case_id}/timeline'),
    ('get',   '/api/v1/reports/'),
    ('post',  '/api/v1/reports/cert-in'),
    ('get',   '/api/v1/admin/tenants/{tenant_id}'),
    ('put',   '/api/v1/admin/tenants/{tenant_id}'),
    ('post',  '/api/v1/auth/login'),
    ('post',  '/api/v1/auth/refresh'),
    ('get',   '/api/v1/ueba/baseline'),
]

all_ok = True
for method, path in required:
    ok = path in paths and method in paths[path]
    print(f"{'PASS' if ok else 'FAIL'}  {method.upper():6} {path}")
    if not ok: all_ok = False

print()
print('CONTRACT:', 'OK — proceed to tasks' if all_ok else 'STOP — missing routes')
