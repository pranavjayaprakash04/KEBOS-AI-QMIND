"""
Seeds UEBA baseline data for demo and test environments.
Simulates 7 days of normal user behaviour to enable UEBA anomaly detection.
Run before any demo: python -m tests.fixtures.ueba_baseline_seed
"""
import asyncio
import random
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID

DEMO_USERS = [
    {"user_id": uuid4(), "role": "ANALYST"},
    {"user_id": uuid4(), "role": "ADMIN"},
    {"user_id": uuid4(), "role": "AUDITOR"},
]
DEMO_TENANT_ID = uuid4()

NORMAL_ENDPOINTS = [
    "/api/v1/threats/", "/api/v1/cases/", "/api/v1/auth/me",
    "/api/v1/reports/", "/api/v1/signals/inject"
]
NORMAL_HOURS = list(range(9, 20))    # 9am-8pm IST
NORMAL_DAYS = list(range(0, 5))      # Mon-Fri


async def seed_baselines(db_pool=None):
    """
    Seed UEBA baseline data for demo users.
    Generates 7 days × 40 requests/day = 280 samples per user.
    This exceeds the 50-sample minimum required for UEBA scoring.
    """
    if not db_pool:
        from app.config import settings
        import asyncpg
        db_pool = await asyncpg.create_pool(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            database=settings.DATABASE_NAME,
        )
    
    now = datetime.now(timezone.utc)
    
    for user in DEMO_USERS:
        user_id = user["user_id"]
        # Generate 7 days × 40 requests/day = 280 samples per user
        events = []
        for day_offset in range(7):
            for _ in range(40):
                # Random time within normal hours
                hour = random.choice(NORMAL_HOURS)
                minute = random.randint(0, 59)
                ts = now - timedelta(days=day_offset, hours=hour, minutes=minute)
                
                features = {
                    "hour_of_day": ts.hour,
                    "day_of_week": ts.weekday(),
                    "source_ip": f"10.0.{random.randint(1,5)}.{random.randint(10,50)}",
                    "endpoint": random.choice(NORMAL_ENDPOINTS),
                    "request_size_bytes": random.randint(100, 2000),
                    "user_agent": "Mozilla/5.0 KebosAnalyst/1.0",
                }
                
                events.append({
                    "user_id": user_id,
                    "tenant_id": DEMO_TENANT_ID,
                    "features": json.dumps(features),
                    "timestamp": ts,
                })
        
        # Bulk insert into ueba_events
        async with db_pool.acquire() as conn:
            # Disable RLS temporarily for seeding
            await conn.execute("SET LOCAL app.current_tenant TO $1", str(DEMO_TENANT_ID))
            
            for event in events:
                await conn.execute(
                    """
                    INSERT INTO ueba_events (user_id, tenant_id, features, timestamp)
                    VALUES ($1, $2, $3, $4)
                    """,
                    event["user_id"],
                    event["tenant_id"],
                    event["features"],
                    event["timestamp"]
                )
            
            # Build baseline from seeded events using Welford algorithm
            mean_features = {}
            variance_features = {}
            sample_count = 0
            
            for event in events:
                features = json.loads(event["features"])
                sample_count += 1
                
                for key, value in features.items():
                    if key not in mean_features:
                        mean_features[key] = 0.0
                        variance_features[key] = 0.0
                    
                    old_mean = mean_features[key]
                    old_variance = variance_features[key]
                    
                    # Welford online algorithm
                    delta = value - old_mean
                    new_mean = old_mean + delta / sample_count
                    new_variance = old_variance + delta * (value - new_mean) / sample_count
                    
                    mean_features[key] = new_mean
                    variance_features[key] = new_variance
            
            # Insert or update baseline
            await conn.execute(
                """
                INSERT INTO ueba_baselines (user_id, tenant_id, mean_features, variance_features, sample_count, last_updated)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    mean_features = EXCLUDED.mean_features,
                    variance_features = EXCLUDED.variance_features,
                    sample_count = EXCLUDED.sample_count,
                    last_updated = NOW()
                """,
                user_id,
                DEMO_TENANT_ID,
                json.dumps(mean_features),
                json.dumps(variance_features),
                sample_count
            )
        
        print(f"Seeded {len(events)} baseline events for user {user_id} (role: {user['role']})")
    
    print(f"UEBA baseline seeding complete. Total users: {len(DEMO_USERS)}, Events per user: 280")
    print(f"Demo tenant ID: {DEMO_TENANT_ID}")
    print(f"Demo user IDs: {[str(u['user_id']) for u in DEMO_USERS]}")


if __name__ == "__main__":
    asyncio.run(seed_baselines())
