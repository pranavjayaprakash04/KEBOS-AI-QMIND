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
    2. Create a user for each tenant
    3. Create a threat for tenant A
    4. Verify tenant B cannot access tenant A's threat
    """
    # Connect to database
    conn = await asyncpg.connect(settings.DATABASE_URL)
    
    try:
        # Create two tenants
        tenant_a_id = await conn.fetchval(
            "INSERT INTO tenants (name, organisation_name, tenant_type, auth_policy, confidence_threshold, sla_hours) "
            "VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            "Tenant A", "Org A", "enterprise", "mfa_required", 0.5, 6
        )
        
        tenant_b_id = await conn.fetchval(
            "INSERT INTO tenants (name, organisation_name, tenant_type, auth_policy, confidence_threshold, sla_hours) "
            "VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            "Tenant B", "Org B", "enterprise", "mfa_required", 0.5, 6
        )
        
        # Create a threat for tenant A
        threat_a_id = await conn.fetchval(
            "INSERT INTO threats (tenant_id, ioc_value, ioc_type, lead_category, confidence, source) "
            "VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            tenant_a_id, "malicious.com", "domain", "Phishing", 0.85, "test"
        )
        
        # Set tenant context to B
        await conn.execute("SET LOCAL app.current_tenant = $1", tenant_b_id)
        
        # Try to access tenant A's threat - should return empty
        threats = await conn.fetch(
            "SELECT id FROM threats WHERE id = $1",
            threat_a_id
        )
        
        # Verify no data leakage
        assert len(threats) == 0, "Tenant B should not be able to access Tenant A's threat"
        
        # Set tenant context to A
        await conn.execute("SET LOCAL app.current_tenant = $1", tenant_a_id)
        
        # Verify tenant A can access their own threat
        threats = await conn.fetch(
            "SELECT id FROM threats WHERE id = $1",
            threat_a_id
        )
        
        assert len(threats) == 1, "Tenant A should be able to access their own threat"
        
        # Cleanup
        await conn.execute("DELETE FROM threats WHERE id = $1", threat_a_id)
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_a_id)
        await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_b_id)
        
    finally:
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
            "INSERT INTO tenants (name, organisation_name, tenant_type, auth_policy, confidence_threshold, sla_hours) "
            "VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            "Test Tenant", "Test Org", "enterprise", "mfa_required", 0.5, 6
        )
        
        # Set tenant context
        await conn.execute("SET LOCAL app.current_tenant = $1", tenant_id)
        
        # Test that RLS is enabled on tables
        tables_with_rls = [
            "threats",
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
