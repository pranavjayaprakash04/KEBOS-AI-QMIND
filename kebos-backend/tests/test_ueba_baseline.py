"""
Tests for UEBA baseline seeding and anomaly detection
"""
import pytest
import json
from datetime import datetime, timezone
from uuid import uuid4
from tests.fixtures.ueba_baseline_seed import seed_baselines, DEMO_TENANT_ID, DEMO_USERS
from app.ueba.baseline_engine import UEBABaselineEngine, get_ueba_engine


@pytest.mark.asyncio
async def test_seed_baselines_creates_minimum_50_events_per_user(db_pool):
    """Test that seed_baselines() creates >= 50 events per user"""
    # Seed baselines
    await seed_baselines(db_pool)
    
    # Verify each user has at least 50 events
    async with db_pool.acquire() as conn:
        await conn.execute("SET LOCAL app.current_tenant TO $1", str(DEMO_TENANT_ID))
        
        for user in DEMO_USERS:
            user_id = user["user_id"]
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM ueba_events WHERE user_id = $1",
                user_id
            )
            assert count >= 50, f"User {user_id} should have at least 50 events, got {count}"
            
            # Verify baseline was created
            baseline = await conn.fetchrow(
                "SELECT sample_count FROM ueba_baselines WHERE user_id = $1",
                user_id
            )
            assert baseline is not None, f"Baseline should exist for user {user_id}"
            assert baseline['sample_count'] >= 50, f"Baseline sample_count should be >= 50, got {baseline['sample_count']}"


@pytest.mark.asyncio
async def test_compute_anomaly_score_non_zero_for_anomalous_request(db_pool):
    """Test that _compute_anomaly_score() returns non-zero for anomalous request after seeding"""
    # Seed baselines first
    await seed_baselines(db_pool)
    
    # Create UEBA engine
    engine = get_ueba_engine(db_pool)
    
    # Get first demo user
    user_id = DEMO_USERS[0]["user_id"]
    
    # Create an anomalous request (3am Sunday - outside normal hours/days)
    anomalous_features = {
        "hour_of_day": 3,  # 3am (outside 9am-8pm)
        "day_of_week": 6,  # Sunday (outside Mon-Fri)
        "source_ip": "203.0.113.50",  # External IP (outside 10.0.x.x)
        "endpoint": "/api/v1/admin/delete",  # Unusual endpoint
        "request_size_bytes": 50000,  # Very large request
        "user_agent": "Unknown/1.0",  # Unknown user agent
    }
    
    # Compute anomaly score
    score = await engine._compute_anomaly_score(
        str(user_id),
        str(DEMO_TENANT_ID),
        anomalous_features
    )
    
    # Should return non-zero score for anomalous request
    assert score > 0.0, f"Anomalous request should return non-zero score, got {score}"
    assert score > 0.5, f"Anomalous request should return score > 0.5, got {score}"


@pytest.mark.asyncio
async def test_normal_request_returns_low_score(db_pool):
    """Test that normal-hours normal-IP request returns score < 0.3 after seeding"""
    # Seed baselines first
    await seed_baselines(db_pool)
    
    # Create UEBA engine
    engine = get_ueba_engine(db_pool)
    
    # Get first demo user
    user_id = DEMO_USERS[0]["user_id"]
    
    # Create a normal request (within normal patterns)
    normal_features = {
        "hour_of_day": 14,  # 2pm (within 9am-8pm)
        "day_of_week": 2,  # Wednesday (within Mon-Fri)
        "source_ip": "10.0.2.25",  # Internal IP (within 10.0.x.x)
        "endpoint": "/api/v1/threats/",  # Normal endpoint
        "request_size_bytes": 500,  # Normal size
        "user_agent": "Mozilla/5.0 KebosAnalyst/1.0",  # Normal user agent
    }
    
    # Compute anomaly score
    score = await engine._compute_anomaly_score(
        str(user_id),
        str(DEMO_TENANT_ID),
        normal_features
    )
    
    # Should return low score for normal request
    assert score < 0.3, f"Normal request should return score < 0.3, got {score}"
    assert score >= 0.0, f"Score should be non-negative, got {score}"


@pytest.mark.asyncio
async def test_baseline_without_minimum_samples_returns_zero(db_pool):
    """Test that _compute_anomaly_score() returns 0.0 when baseline has < 50 samples"""
    # Create a new user with insufficient baseline
    new_user_id = uuid4()
    
    # Insert only 10 events (below 50-sample threshold)
    async with db_pool.acquire() as conn:
        await conn.execute("SET LOCAL app.current_tenant TO $1", str(DEMO_TENANT_ID))
        
        for i in range(10):
            features = {
                "hour_of_day": 14,
                "day_of_week": 2,
                "source_ip": "10.0.2.25",
                "endpoint": "/api/v1/threats/",
                "request_size_bytes": 500,
                "user_agent": "Mozilla/5.0",
            }
            await conn.execute(
                """
                INSERT INTO ueba_events (user_id, tenant_id, features)
                VALUES ($1, $2, $3)
                """,
                new_user_id,
                DEMO_TENANT_ID,
                json.dumps(features)
            )
        
        # Create baseline with only 10 samples
        await conn.execute(
            """
            INSERT INTO ueba_baselines (user_id, tenant_id, mean_features, variance_features, sample_count)
            VALUES ($1, $2, $3, $4, $5)
            """,
            new_user_id,
            DEMO_TENANT_ID,
            json.dumps({"hour_of_day": 14.0}),
            json.dumps({"hour_of_day": 1.0}),
            10
        )
    
    # Create UEBA engine
    engine = get_ueba_engine(db_pool)
    
    # Try to compute anomaly score
    features = {
        "hour_of_day": 3,
        "day_of_week": 6,
        "source_ip": "203.0.113.50",
        "endpoint": "/api/v1/admin/delete",
        "request_size_bytes": 50000,
        "user_agent": "Unknown/1.0",
    }
    
    score = await engine._compute_anomaly_score(
        str(new_user_id),
        str(DEMO_TENANT_ID),
        features
    )
    
    # Should return 0.0 due to insufficient samples
    assert score == 0.0, f"Should return 0.0 with < 50 samples, got {score}"


@pytest.mark.asyncio
async def test_seed_baselines_creates_correct_baseline_features(db_pool):
    """Test that seed_baselines() creates correct baseline features"""
    # Seed baselines
    await seed_baselines(db_pool)
    
    async with db_pool.acquire() as conn:
        await conn.execute("SET LOCAL app.current_tenant TO $1", str(DEMO_TENANT_ID))
        
        # Check baseline for first user
        user_id = DEMO_USERS[0]["user_id"]
        baseline = await conn.fetchrow(
            """
            SELECT mean_features, variance_features, sample_count
            FROM ueba_baselines
            WHERE user_id = $1
            """,
            user_id
        )
        
        assert baseline is not None, "Baseline should exist"
        
        mean_features = json.loads(baseline['mean_features'])
        variance_features = json.loads(baseline['variance_features'])
        
        # Verify expected features exist
        expected_features = ["hour_of_day", "day_of_week", "source_ip", "endpoint", "request_size_bytes", "user_agent"]
        for feature in expected_features:
            assert feature in mean_features, f"Feature '{feature}' should exist in mean_features"
            assert feature in variance_features, f"Feature '{feature}' should exist in variance_features"
        
        # Verify hour_of_day is within normal range (9-19)
        assert 9 <= mean_features["hour_of_day"] <= 19, f"hour_of_day mean should be within normal range, got {mean_features['hour_of_day']}"
        
        # Verify day_of_week is within normal range (0-4)
        assert 0 <= mean_features["day_of_week"] <= 4, f"day_of_week mean should be within normal range, got {mean_features['day_of_week']}"


@pytest.mark.asyncio
async def test_mahalanobis_distance_computation(db_pool):
    """Test that Mahalanobis distance computation works correctly"""
    # Seed baselines
    await seed_baselines(db_pool)
    
    engine = get_ueba_engine(db_pool)
    user_id = DEMO_USERS[0]["user_id"]
    
    # Get baseline
    async with db_pool.acquire() as conn:
        await conn.execute("SET LOCAL app.current_tenant TO $1", str(DEMO_TENANT_ID))
        baseline = await conn.fetchrow(
            """
            SELECT mean_features, variance_features, sample_count
            FROM ueba_baselines
            WHERE user_id = $1
            """,
            user_id
        )
    
    baseline_dict = {
        'mean_features': json.loads(baseline['mean_features']),
        'variance_features': json.loads(baseline['variance_features']),
        'sample_count': baseline['sample_count']
    }
    
    # Test with features exactly matching baseline (should give low score)
    normal_features = baseline_dict['mean_features'].copy()
    score = engine._mahalanobis_distance(normal_features, baseline_dict)
    assert score < 0.5, f"Features matching baseline should give low score, got {score}"
    
    # Test with features far from baseline (should give high score)
    anomalous_features = baseline_dict['mean_features'].copy()
    if "hour_of_day" in anomalous_features:
        anomalous_features["hour_of_day"] = 0.0  # Midnight (far from normal hours)
    score = engine._mahalanobis_distance(anomalous_features, baseline_dict)
    assert score > 0.0, f"Features far from baseline should give non-zero score, got {score}"
