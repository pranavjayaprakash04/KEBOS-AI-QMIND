# Test Fixtures

This directory contains test fixtures and seeding scripts for demo and test environments.

## UEBA Baseline Seeding

**CRITICAL**: UEBA requires minimum 50 samples before scoring (to avoid false positives during ramp-up). In a fresh deployment or demo environment, the baseline is empty — UEBA shows zero signals.

### Before Running Demos

Seed UEBA baseline data:

```bash
docker-compose exec kebos-backend python -m tests.fixtures.ueba_baseline_seed
```

This seeds 7 days of normal behaviour per user (280 events per user), which exceeds the 50-sample minimum required for UEBA anomaly detection.

Without this, UEBA shows no anomaly signals in live demos.

### Seeded Data

The seeding script creates:
- 3 demo users (ANALYST, ADMIN, AUDITOR roles)
- 280 events per user (7 days × 40 requests/day)
- Normal behaviour patterns:
  - Hours: 9am-8pm IST
  - Days: Monday-Friday
  - IPs: 10.0.x.x range
  - Endpoints: Normal API endpoints

### Using in Tests

Use the `ueba_demo_baseline` fixture in tests that require UEBA scoring:

```python
import pytest

@pytest.mark.usefixtures("ueba_demo_baseline")
async def test_ueba_scoring():
    # UEBA scoring will now work with seeded baseline
    pass
```

The fixture automatically cleans up seeded data after the test session.
