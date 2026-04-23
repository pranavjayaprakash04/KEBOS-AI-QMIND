"""
Pytest configuration and shared fixtures for Kebos backend tests
"""
import pytest
import asyncio
from tests.fixtures.ueba_baseline_seed import seed_baselines, DEMO_TENANT_ID


@pytest.fixture(scope="session", autouse=False)
async def ueba_demo_baseline(db_pool):
    """
    Seed UEBA baseline data for demo and test environments.
    Use in tests that exercise UEBA scoring.
    
    This fixture seeds 7 days of normal behaviour per user (280 events per user),
    which exceeds the 50-sample minimum required for UEBA anomaly detection.
    
    Usage:
        @pytest.mark.usefixtures("ueba_demo_baseline")
        async def test_ueba_scoring():
            # UEBA scoring will now work with seeded baseline
            pass
    """
    await seed_baselines(db_pool)
    yield
    
    # Cleanup: remove seeded events
    async with db_pool.acquire() as conn:
        await conn.execute("SET LOCAL app.current_tenant TO $1", str(DEMO_TENANT_ID))
        await conn.execute("DELETE FROM ueba_events WHERE source_ip LIKE '10.0.%'")
        await conn.execute("DELETE FROM ueba_baselines WHERE user_id IN (SELECT user_id FROM ueba_events)")
