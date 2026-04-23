#!/usr/bin/env python3
import asyncio
import asyncpg
from uuid import uuid4
from passlib.context import CryptContext

async def create_demo_user():
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    password_hash = pwd_context.hash('admin123')
    
    conn = await asyncpg.connect('postgresql://kebos:kebos_pass@postgres:5432/kebos')
    
    # Get or create tenant
    tenant_id = await conn.fetchval("SELECT id FROM tenants WHERE name = 'Demo Tenant'")
    if not tenant_id:
        tenant_id = uuid4()
        await conn.execute('INSERT INTO tenants (id, name, tenant_type, created_at, is_active) VALUES ($1, $2, $3, NOW(), true)', tenant_id, 'Demo Tenant', 'enterprise')
    
    # Create user
    user_id = uuid4()
    await conn.execute('INSERT INTO users (id, tenant_id, username, email, password_hash, role, is_active, created_at) VALUES ($1, $2, $3, $4, $5, $6, true, NOW())', user_id, tenant_id, 'admin', 'admin@kebos.local', password_hash, 'admin')
    
    print(f'Created user: {user_id}')
    print(f'Tenant ID: {tenant_id}')
    await conn.close()

if __name__ == '__main__':
    asyncio.run(create_demo_user())
