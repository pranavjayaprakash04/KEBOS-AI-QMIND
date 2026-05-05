#!/usr/bin/env python3
import asyncio
import asyncpg
import bcrypt

async def create_user():
    # Generate bcrypt hash
    password = b'admin123'
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password, salt).decode('utf-8')
    
    print(f"Generated hash: {password_hash}")
    
    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='kebos',
        password='kebos_pass',
        database='kebos'
    )
    
    # Insert user
    user_id = '0838c1ce-8874-4885-92b5-38735a990f4a'
    tenant_id = '0838c1ce-8874-4885-92b5-38735a990f4a'
    
    await conn.execute(
        'INSERT INTO users (id, tenant_id, username, email, password_hash, role, is_active, created_at) VALUES ($1, $2, $3, $4, $5, $6, true, NOW())',
        user_id, tenant_id, 'admin', 'admin@kebos.local', password_hash, 'admin'
    )
    
    print(f"User created successfully")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(create_user())
