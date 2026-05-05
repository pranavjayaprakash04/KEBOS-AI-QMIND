"""
Tenant Isolation Test

Verifies that Row Level Security (RLS) prevents cross-tenant data leakage.
Tests that users from one tenant cannot access data from another tenant.
"""
import pytest
import asyncpg
from app.config import settings


@pytest.mark.asyncio
async def test_tenant_isolation():
    """
    Test that RLS prevents cross-tenant data access.

    1. Create two tenants
    2. Create a threat for tenant A
    3. Verify tenant B cannot access tenant A's threat (via RLS)
    4. Verify tenant A can access their own threat
    """
    conn = await asyncpg.connect(settings.DATABASE_URL)

    try:
        # Create a non-privileged role that will be subject to RLS.
        # The connection user (kebos) is a superuser with BYPASSRLS — it skips
        # RLS entirely. SET ROLE to a plain role makes RLS apply on this session.
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kebos_rls_test') THEN
                    CREATE ROLE kebos_rls_test NOLOGIN NOINHERIT;
                END IF;
            END
            $$
        """)
        await conn.execute("GRANT SELECT ON threat_events TO kebos_rls_test")

        # Create two tenants (as superuser, before role switch)
        tenant_a_id = await conn.fetchval(
            "INSERT INTO tenants (id, name, tenant_type, created_at, is_active) "
            "VALUES (gen_random_uuid(), $1, $2, NOW(), true) RETURNING id",
            "Tenant A", "enterprise"
        )

        tenant_b_id = await conn.fetchval(
            "INSERT INTO tenants (id, name, tenant_type, created_at, is_active) "
            "VALUES (gen_random_uuid(), $1, $2, NOW(), true) RETURNING id",
            "Tenant B", "enterprise"
        )

        # Create a threat for tenant A (as superuser, bypasses RLS for insert)
        threat_a_id = await conn.fetchval(
            "INSERT INTO threat_events (id, tenant_id, event_type, severity, status, "
            "indicator_value, lead_category, qmind_confidence, created_at, updated_at) "
            "VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, NOW(), NOW()) RETURNING id",
            tenant_a_id, "network", "HIGH", "MONITORING", "malicious.com", "Phishing", 0.85
        )

        # Switch to non-privileged role so RLS is enforced for subsequent queries.
        # SET ROLE is session-scoped and persists across auto-commit transactions.
        await conn.execute("SET ROLE kebos_rls_test")

        # Set tenant context to B (session-level, persists across statements)
        await conn.execute(
            "SELECT set_config('app.current_tenant', $1, false)", str(tenant_b_id)
        )

        # Try to access tenant A's threat — RLS should block it
        threats = await conn.fetch(
            "SELECT id FROM threat_events WHERE id = $1",
            threat_a_id
        )
        assert len(threats) == 0, "Tenant B should not be able to access Tenant A's threat"

        # Set tenant context to A
        await conn.execute(
            "SELECT set_config('app.current_tenant', $1, false)", str(tenant_a_id)
        )

        # Verify tenant A can access their own threat
        threats = await conn.fetch(
            "SELECT id FROM threat_events WHERE id = $1",
            threat_a_id
        )
        assert len(threats) == 1, "Tenant A should be able to access their own threat"

        # Reset to superuser for cleanup
        await conn.execute("RESET ROLE")

        # Cleanup
        await conn.execute("DELETE FROM threat_events WHERE id = $1", threat_a_id)
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_a_id)
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_b_id)

    finally:
        try:
            await conn.execute("RESET ROLE")
        except Exception:
            pass
        await conn.close()


@pytest.mark.asyncio
async def test_tenant_isolation_all_tables():
    """
    Test RLS on all tenant-scoped tables.
    """
    conn = await asyncpg.connect(settings.DATABASE_URL)

    try:
        # Create tenant
        tenant_id = await conn.fetchval(
            "INSERT INTO tenants (id, name, tenant_type, created_at, is_active) "
            "VALUES (gen_random_uuid(), $1, $2, NOW(), true) RETURNING id",
            "Test Tenant", "enterprise"
        )

        # Set tenant context
        await conn.execute(
            "SELECT set_config('app.current_tenant', $1, false)", str(tenant_id)
        )

        # Test that RLS is enabled on tables
        tables_with_rls = [
            "threat_events",
            "honeytokens",
            "users",
            "cases",
            "iocs",
            "ueba_events",
            "ueba_baselines",
            "audit_entries"
        ]

        for table in tables_with_rls:
            result = await conn.fetchval(
                """
                SELECT relrowsecurity
                FROM pg_class
                WHERE relname = $1
                """,
                table
            )
            assert result == True, f"RLS should be enabled on table {table}"

        # Cleanup
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_id)

    finally:
        await conn.close()
