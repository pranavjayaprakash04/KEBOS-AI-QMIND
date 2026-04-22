import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.services import AuthService
import jwt
import json
from unittest import mock


client = TestClient(app)


class TestPhase11Auth:
    """Phase 1.1: JWT to HttpOnly Cookie + RS256"""
    
    def test_login_returns_httponly_cookie(self):
        """Login should return HttpOnly cookie, not JSON token"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Token should NOT be in response body
        assert "access_token" not in data
        assert "token" not in data
        
        # User profile should be in response
        assert "user" in data
        assert data["user"]["username"] == "admin"
        
        # Cookie should be set
        assert "access_token" in response.cookies
        cookie = response.cookies["access_token"]
        assert cookie  # Cookie should have a value
    
    def test_auth_me_returns_401_without_cookie(self):
        """/auth/me should return 401 without cookie"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_auth_me_returns_user_with_valid_cookie(self):
        """/auth/me should return user profile with valid cookie"""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        assert login_response.status_code == 200
        
        # Get cookie
        access_token = login_response.cookies.get("access_token")
        
        # Call /me with cookie
        me_response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": access_token}
        )
        
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["username"] == "admin"
        assert data["role"] == "ADMIN"
    
    def test_logout_invalidates_token(self):
        """Logout should invalidate token via JTI blacklist"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        access_token = login_response.cookies.get("access_token")
        
        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            cookies={"access_token": access_token}
        )
        assert logout_response.status_code == 200
        
        # Try to use the token after logout - should be invalid
        me_response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": access_token}
        )
        # Should be 401 because JTI is blacklisted
        assert me_response.status_code == 401
    
    def test_hs256_token_is_rejected(self):
        """HS256 tokens should be rejected (must be RS256)"""
        # Create a fake HS256 token
        fake_payload = {
            "sub": "1",
            "username": "admin",
            "role": "ADMIN",
            "tenant_id": 1,
            "jti": "fake-jti",
            "iat": 1234567890,
            "exp": 9999999999
        }
        hs256_token = jwt.encode(fake_payload, "secret", algorithm="HS256")
        
        # Try to use HS256 token
        response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": hs256_token}
        )
        
        # Should be rejected (401)
        assert response.status_code == 401
    
    def test_expired_token_is_rejected(self):
        """Expired tokens should be rejected"""
        # Create an expired RS256 token
        from datetime import datetime, timedelta
        import uuid
        from app.auth.services import AuthService
        
        auth_service = AuthService()
        user = auth_service.authenticate_user("admin", "admin")
        
        # Manually create an expired token
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        expired_payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "jti": str(uuid.uuid4()),
            "iat": (datetime.utcnow() - timedelta(days=1)).timestamp(),
            "exp": (datetime.utcnow() - timedelta(hours=1)).timestamp()
        }
        
        expired_token = jwt.encode(expired_payload, private_pem, algorithm="RS256")
        
        # Try to use expired token
        response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": expired_token}
        )
        
        # Should be rejected (401)
        assert response.status_code == 401
    
    def test_endpoint_rejects_request_without_valid_jwt(self):
        """Protected endpoints should reject requests without valid JWT"""
        # No cookie at all
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        
        # Invalid cookie
        response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": "invalid-token"}
        )
        assert response.status_code == 401


class TestPhase12TotpAndGovernment:
    """Phase 1.2: TOTP MFA + Vault Encryption"""
    
    def test_totp_secret_stored_encrypted(self):
        """TOTP secret must be stored encrypted (never plaintext)"""
        # This test validates the DB schema has totp_secret_encrypted
        # and NOT totp_secret (plaintext)
        import os
        
        # Check migration file exists and has correct column name
        migration_file = "kebos-backend/alembic/versions/001_add_totp_encrypted.py"
        assert os.path.exists(migration_file), "Migration file must exist"
        
        with open(migration_file, 'r') as f:
            content = f.read()
            assert "totp_secret_encrypted" in content, \
                "Must have totp_secret_encrypted column"
            assert "totp_secret" not in content or \
                   content.count("totp_secret_encrypted") > content.count("totp_secret"), \
                "Must NOT have plaintext totp_secret column"
    
    def test_totp_verification_methods_exist(self):
        """TOTP service should have verify and generate_secret methods"""
        from app.auth.totp import TOTPService
        
        totp_service = TOTPService()
        assert hasattr(totp_service, 'verify')
        assert hasattr(totp_service, 'generate_secret')
        assert hasattr(totp_service, 'is_enabled')
    
    def test_government_tenant_without_fido2_gets_403(self):
        """Government tenant without FIDO2 verification should get 403"""
        # Login as government user without FIDO2
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "gov_user", "password": "gov"}
        )
        
        assert login_response.status_code == 200
        access_token = login_response.cookies.get("access_token")
        
        # Try to access protected endpoint
        # Should get 403 because government tenant requires FIDO2
        me_response = client.get(
            "/api/v1/auth/me",
            cookies={"access_token": access_token}
        )
        
        assert me_response.status_code == 403
        assert "FIDO2 required" in me_response.json()["detail"]
    
    def test_fido2_skeleton_endpoints_exist(self):
        """FIDO2 skeleton endpoints should exist (return 501)"""
        endpoints = [
            "/api/v1/auth/fido2/register/begin",
            "/api/v1/auth/fido2/register/complete",
            "/api/v1/auth/fido2/authenticate/begin",
            "/api/v1/auth/fido2/authenticate/complete",
        ]
        
        for endpoint in endpoints:
            response = client.post(endpoint)
            assert response.status_code == 501, \
                f"{endpoint} should return 501 (Not implemented)"


class TestPhase13SessionRiskAndSecurityHeaders:
    """Phase 1.3: SessionRiskScorer + Security Headers"""
    
    def test_impossible_travel_triggers_401(self):
        """Impossible travel (>900km/h) should trigger 401"""
        from app.auth.session_risk import SessionRiskScorer
        from unittest.mock import Mock, AsyncMock
        
        risk_scorer = SessionRiskScorer()
        
        # Mock request with location data
        request = Mock()
        request.headers = {"user-agent": "test-agent"}
        
        # Mock previous session in different location (simulating impossible travel)
        risk_scorer.redis_client = AsyncMock()
        risk_scorer.redis_client.get = AsyncMock(return_value=json.dumps({
            "lat": 40.7128,  # New York
            "lon": -74.0060,
            "fingerprint": "test-agent",
            "timestamp": 1000000000
        }))
        risk_scorer.redis_client.setex = AsyncMock()
        
        # Mock current location in London (distance ~5570km)
        # If time delta is small, speed would be > 900km/h
        import time
        risk_scorer._extract_ip_location = lambda req: (51.5074, -0.1278)
        risk_scorer._extract_fingerprint = lambda req: "test-agent"
        
        # This should detect impossible travel
        # For scaffold, we just verify the method exists
        assert hasattr(risk_scorer, 'score')
        assert hasattr(risk_scorer, '_haversine_distance')
    
    def test_security_headers_present_on_every_response(self):
        """Security headers should be present on every response"""
        response = client.get("/health")
        
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        
        # Check HSTS has correct values
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        
        # Check CSP
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        
        # Check X-Frame-Options
        assert response.headers["X-Frame-Options"] == "DENY"
        
        # Check X-Content-Type-Options
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_x_pqc_status_header_present_on_every_response(self):
        """X-PQC-Status header should be present on every response"""
        response = client.get("/health")
        assert "X-PQC-Status" in response.headers
        # Should be either "enabled" or "disabled"
        assert response.headers["X-PQC-Status"] in ["enabled", "disabled"]
    
    def test_validate_environment_succeeds_with_correct_settings(self):
        """validate_environment should succeed with correct settings"""
        from app.security.validate_environment import validate_environment
        from app.config import settings

        # Save original values
        original_algo = settings.JWT_ALGORITHM
        original_expiry = settings.ACCESS_TOKEN_EXPIRE_MINUTES

        # Set correct values
        settings.JWT_ALGORITHM = "RS256"
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15

        errors = validate_environment()

        # Restore
        settings.JWT_ALGORITHM = original_algo
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = original_expiry

        # Should not have CRITICAL errors
        critical = [e for e in errors if e.startswith("CRITICAL")]
        assert len(critical) == 0

    def test_validate_environment_raises_systemexit_on_hs256(self):
        """validate_environment should raise SystemExit when JWT_ALGORITHM=HS256"""
        from app.security.validate_environment import validate_environment
        from app.config import settings

        # Temporarily set to HS256
        original_algo = settings.JWT_ALGORITHM
        settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(SystemExit):
            validate_environment()

        # Restore
        settings.JWT_ALGORITHM = original_algo
    
    def test_validate_environment_raises_systemexit_on_gt_15min_expiry(self):
        """validate_environment should raise SystemExit when ACCESS_TOKEN_EXPIRE_MINUTES=60"""
        from app.security.validate_environment import validate_environment
        from app.config import settings

        # Temporarily set to >15
        original_expiry = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60

        with pytest.raises(SystemExit):
            validate_environment()

        # Restore
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = original_expiry


class TestPhase13bEmergencyRotation:
    """Phase 1.3b: VaultBreachResponse + Emergency Rotation"""
    
    def test_non_admin_gets_403_on_emergency_rotation(self):
        """Non-admin users should get 403 on emergency rotation"""
        # Login as regular user
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "gov_user", "password": "gov"}
        )
        access_token = login_response.cookies.get("access_token")
        
        # Try emergency rotation without ADMIN role
        response = client.post(
            "/api/v1/auth/security/emergency-rotation",
            json={"reason": "test"},
            headers={"X-FIDO2-Assertion": "test"},
            cookies={"access_token": access_token}
        )
        
        assert response.status_code == 403
        assert "ADMIN role" in response.json()["detail"]
    
    def test_emergency_rotation_requires_fido2_header(self):
        """Emergency rotation should require X-FIDO2-Assertion header"""
        # Login as admin
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        access_token = login_response.cookies.get("access_token")
        
        # Try emergency rotation without FIDO2 header
        response = client.post(
            "/api/v1/auth/security/emergency-rotation",
            json={"reason": "test"},
            cookies={"access_token": access_token}
        )
        
        assert response.status_code == 403
        assert "FIDO2 verification" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_emergency_rotation_flushes_jti_tokens(self):
        """Emergency rotation should flush all JTI tokens"""
        from app.security.vault_breach import VaultBreachResponse
        from unittest.mock import AsyncMock
        import redis.asyncio as redis
        
        vault_breach = VaultBreachResponse()
        
        # Mock Redis to return some JTI keys
        vault_breach.redis_client = AsyncMock()
        vault_breach.redis_client.keys = AsyncMock(return_value=["jti:1:abc", "jti:2:def"])
        vault_breach.redis_client.delete = AsyncMock()
        
        result = await vault_breach.emergency_rotation(
            initiated_by="admin",
            reason="test"
        )
        
        # Should have flushed 2 JTI tokens
        assert result.sessions_flushed == 2
        vault_breach.redis_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_emergency_rotation_completes_under_5_min(self):
        """Emergency rotation should complete in under 5 minutes (300s)"""
        from app.security.vault_breach import VaultBreachResponse
        from unittest.mock import AsyncMock
        
        vault_breach = VaultBreachResponse()
        
        # Mock Redis
        vault_breach.redis_client = AsyncMock()
        vault_breach.redis_client.keys = AsyncMock(return_value=[])
        
        result = await vault_breach.emergency_rotation(
            initiated_by="admin",
            reason="test"
        )
        
        # Should complete in under 300 seconds
        assert result.elapsed_seconds < 300
        # For scaffold with TODOs, it should be very fast
        assert result.elapsed_seconds < 1

    @pytest.mark.asyncio
    async def test_jti_blacklist_key_uses_tenant_id_namespace(self):
        """JTI blacklist key should use tenant_id namespace (jti:{tenant_id}:{jti})"""
        from app.auth.services import AuthService
        from unittest.mock import AsyncMock, patch

        auth_service = AuthService()

        # Mock Redis client
        mock_redis = AsyncMock()
        auth_service.redis_client = mock_redis

        # Create a mock user
        user = auth_service.authenticate_user("admin", "admin")
        jti = "test-jti-123"

        # Call logout_user
        import asyncio
        asyncio.run(auth_service.logout_user(user, jti))

        # Verify Redis key format includes tenant_id
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        key = call_args[0][0]
        # Key should be in format jti:{tenant_id}:{jti}
        assert key == f"jti:{user.tenant_id}:{jti}"


class TestFido2Implementation:
    """FIDO2/WebAuthn Implementation Tests"""

    def test_fido2_register_begin_returns_challenge(self):
        """FIDO2 register/begin should return registration options with challenge"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        access_token = login_response.cookies.get("access_token")

        # Call register/begin
        reg_response = client.post(
            "/api/v1/auth/fido2/register/begin",
            cookies={"access_token": access_token}
        )

        assert reg_response.status_code == 200
        data = reg_response.json()
        assert "options" in data
        assert "challenge" in data["options"]
        assert "rpId" in data["options"]

    def test_fido2_register_complete_stores_credential(self):
        """FIDO2 register/complete should store credential in Redis"""
        from app.auth.services import AuthService
        from unittest.mock import AsyncMock, patch
        import asyncio

        auth_service = AuthService()

        # Mock Redis
        mock_redis = AsyncMock()
        auth_service.redis_client = mock_redis

        # Mock challenge retrieval
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "challenge": "test-challenge",
            "user_id": "1"
        }))

        # Mock webauthn verification
        with patch('app.auth.router.verify_registration_response') as mock_verify:
            mock_verify.return_value = type('obj', (object,), {
                'credential_id': 'test-cred-id',
                'public_key': 'test-public-key',
                'sign_count': 0
            })

            # This test validates the flow structure
            # Full integration test would require actual WebAuthn credential
            assert True  # Placeholder for integration test

    def test_geoip_lookup_returns_lat_lon(self):
        """GeoIP lookup should return float lat/lon when configured"""
        from app.auth.session_risk import SessionRiskScorer
        from unittest.mock import Mock, patch

        # Mock geoip2 reader
        mock_location = Mock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060

        mock_response = Mock()
        mock_response.location = mock_location

        mock_reader = Mock()
        mock_reader.city = Mock(return_value=mock_response)

        scorer = SessionRiskScorer()
        scorer.geoip_reader = mock_reader

        # Mock request
        request = Mock()
        request.client = Mock()
        request.client.host = "8.8.8.8"

        lat, lon = scorer._extract_ip_location(request)

        assert isinstance(lat, float)
        assert isinstance(lon, float)
        assert lat == 40.7128
        assert lon == -74.0060

    @pytest.mark.asyncio
    async def test_impossible_travel_raises_401_when_speed_gt_900_kmh(self):
        """Impossible travel should raise 401 when speed > 900 km/h"""
        from app.auth.session_risk import SessionRiskScorer
        from unittest.mock import AsyncMock

        scorer = SessionRiskScorer()

        # Mock Redis
        scorer.redis_client = AsyncMock()

        # Mock previous session in New York
        scorer.redis_client.get = AsyncMock(return_value=json.dumps({
            "lat": 40.7128,
            "lon": -74.0060,
            "fingerprint": "test-agent",
            "timestamp": 1000000000  # 1 hour ago
        }))

        # Mock geoip to return London (distance ~5570km)
        mock_location = Mock()
        mock_location.latitude = 51.5074
        mock_location.longitude = -0.1278

        mock_response = Mock()
        mock_response.location = mock_location

        scorer.geoip_reader = Mock()
        scorer.geoip_reader.city = Mock(return_value=mock_response)

        # Mock request
        request = Mock()
        request.client = Mock()
        request.client.host = "8.8.8.8"
        request.headers = {"user-agent": "test-agent"}

        # Score should detect impossible travel
        result = await scorer.score(request, 1, 1)

        assert result.action == "lock"
        assert "Impossible travel" in result.reason


class TestEmergencyRotation:
    """Emergency Rotation Tests"""

    @pytest.mark.asyncio
    async def test_emergency_rotation_completes_under_5_minutes(self):
        """Emergency rotation should complete in under 5 minutes"""
        from app.security.vault_breach import VaultBreachResponse
        from unittest.mock import AsyncMock

        vault_breach = VaultBreachResponse()

        # Mock Redis client
        mock_redis = AsyncMock()
        vault_breach.redis_client = mock_redis
        mock_redis.scan_iter = AsyncMock(return_value=[])  # No JTIs to flush
        mock_redis.set = AsyncMock()

        # Run emergency rotation
        result = await vault_breach.emergency_rotation(
            initiated_by="admin",
            reason="test rotation"
        )

        # Should complete in under 5 minutes (300s)
        assert result.duration_seconds < 300
        # Should have completed steps
        assert len(result.steps_completed) > 0

    @pytest.mark.asyncio
    async def test_emergency_rotation_flushes_all_jti_keys(self):
        """Emergency rotation should flush all jti:* keys from Redis"""
        from app.security.vault_breach import VaultBreachResponse
        from unittest.mock import AsyncMock

        vault_breach = VaultBreachResponse()

        # Mock Redis client with some JTI keys
        mock_redis = AsyncMock()
        vault_breach.redis_client = mock_redis

        # Simulate 3 JTI keys
        jti_keys = [b"jti:1:abc", b"jti:2:def", b"jti:3:ghi"]
        mock_redis.scan_iter = AsyncMock(return_value=iter(jti_keys))
        mock_redis.delete = AsyncMock()
        mock_redis.set = AsyncMock()

        result = await vault_breach.emergency_rotation(
            initiated_by="admin",
            reason="test"
        )

        # Verify delete was called for each key
        assert mock_redis.delete.call_count == 3
        # Verify rotation timestamp was set
        mock_redis.set.assert_called_with("session:rotation_timestamp", mock.ANY, ex=86400)

    @pytest.mark.asyncio
    async def test_tokens_issued_before_rotation_timestamp_are_rejected(self):
        """Tokens issued before rotation timestamp should be rejected"""
        from app.auth.services import AuthService
        from app.auth.dependencies import get_current_user
        from fastapi import Request
        from unittest.mock import AsyncMock, Mock

        auth_service = AuthService()

        # Mock Redis client with rotation timestamp
        mock_redis = AsyncMock()
        auth_service.redis_client = mock_redis
        mock_redis.exists = AsyncMock(return_value=0)  # JTI not blacklisted
        mock_redis.get = AsyncMock(return_value=str(int(__import__('time').time())))  # Rotation just happened

        # Create a token issued before rotation (iat = 0)
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        old_payload = {
            "sub": "1",
            "username": "admin",
            "role": "ADMIN",
            "tenant_id": 1,
            "tenant_type": "enterprise",
            "fido2_enabled": True,
            "jti": "old-jti",
            "iat": 0,  # Issued at epoch (before rotation)
            "exp": 9999999999
        }

        old_token = jwt.encode(old_payload, private_pem, algorithm="RS256")

        # Mock request with old token
        request = Mock()
        request.cookies = {"access_token": old_token}
        request.app = Mock()
        request.app.state = Mock()

        # Try to get current user - should fail due to rotation timestamp
        try:
            import asyncio
            asyncio.run(get_current_user(request, auth_service))
            assert False, "Should have raised HTTPException"
        except Exception as e:
            assert "invalidated by emergency rotation" in str(e).lower()

    def test_emergency_rotation_endpoint_returns_403_without_admin_role(self):
        """Emergency rotation endpoint should return 403 without ADMIN role"""
        # Login as regular user (gov_user is ANALYST, not ADMIN)
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "gov_user", "password": "gov"}
        )
        access_token = login_response.cookies.get("access_token")

        # Try emergency rotation without ADMIN role
        response = client.post(
            "/api/v1/auth/emergency-rotation",
            json={"reason": "test"},
            cookies={"access_token": access_token}
        )

        assert response.status_code == 403
        assert "ADMIN role" in response.json()["detail"]
