"""
Authentication Module Tests

Comprehensive tests for authentication API endpoints.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from auth.api import router as auth_router
from auth.services import auth_service, AuthenticationError
from auth.schemas import UserCreate, UserRole, LoginResponse, UserInfo
from common.models import UserORM


# Test app setup
app = FastAPI()
app.include_router(auth_router)
client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_user():
    """Mock user object."""
    user = Mock(spec=UserORM)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "hashed_password"
    user.role = "operator"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.last_login = None
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user object."""
    user = Mock(spec=UserORM)
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.hashed_password = "hashed_password"
    user.role = "admin"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.last_login = None
    return user


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for testing."""
    payload = {
        "sub": "1",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "type": "access_token"
    }
    return jwt.encode(payload, auth_service.secret_key, algorithm=auth_service.algorithm)


@pytest.fixture
def admin_token():
    """Generate a valid JWT token for admin user."""
    payload = {
        "sub": "2",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "type": "access_token"
    }
    return jwt.encode(payload, auth_service.secret_key, algorithm=auth_service.algorithm)


class TestAuthAPI:
    """Test authentication API endpoints."""

    @patch('auth.api.get_db')
    @patch('auth.services.auth_service.authenticate_user')
    @patch('auth.services.auth_service.create_access_token')
    def test_login_success(self, mock_create_token, mock_authenticate, mock_get_db, mock_user):
        """Test successful login."""
        # Setup mocks
        mock_get_db.return_value = Mock()
        mock_authenticate.return_value = mock_user
        mock_create_token.return_value = "test_token"
        
        # Test login
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "password"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token"
        assert data["token_type"] == "bearer"
        assert "user" in data

    @patch('auth.api.get_db')
    @patch('auth.services.auth_service.authenticate_user')
    def test_login_invalid_credentials(self, mock_authenticate, mock_get_db):
        """Test login with invalid credentials."""
        # Setup mocks
        mock_get_db.return_value = Mock()
        mock_authenticate.return_value = None
        
        # Test login
        response = client.post(
            "/auth/login",
            data={"username": "invalid", "password": "wrong"}
        )
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @patch('auth.dependencies.get_current_user')
    def test_get_current_user_info(self, mock_get_current_user):
        """Test getting current user info."""
        # Setup mock
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "operator",
            "is_active": True,
            "permissions": ["view"]
        }
        mock_get_current_user.return_value = user_data
        
        # Test endpoint
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "operator"

    @patch('auth.dependencies.require_admin')
    @patch('auth.api.get_db')
    def test_list_users_admin(self, mock_get_db, mock_require_admin):
        """Test listing users as admin."""
        # Setup mocks
        mock_get_db.return_value = Mock()
        admin_data = {
            "user_id": 2,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True,
            "permissions": ["all"]
        }
        mock_require_admin.return_value = admin_data
        
        # Test endpoint
        response = client.get(
            "/auth/users",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch('auth.dependencies.require_admin')
    @patch('auth.api.get_db')
    @patch('auth.services.auth_service.create_user')
    def test_create_user_admin(self, mock_create_user, mock_get_db, mock_require_admin, mock_user):
        """Test creating user as admin."""
        # Setup mocks
        mock_get_db.return_value = Mock()
        admin_data = {
            "user_id": 2,
            "username": "admin",
            "role": "admin",
            "is_active": True,
            "permissions": ["all"]
        }
        mock_require_admin.return_value = admin_data
        mock_create_user.return_value = mock_user
        
        # Test endpoint
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "role": "operator"
        }
        
        response = client.post(
            "/auth/users",
            json=user_data,
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    @patch('auth.dependencies.get_current_active_user')
    @patch('auth.api.get_db')
    @patch('auth.services.auth_service.change_password')
    def test_change_password_success(self, mock_change_password, mock_get_db, mock_get_current_user):
        """Test successful password change."""
        # Setup mocks
        mock_get_db.return_value = Mock()
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "operator",
            "is_active": True
        }
        mock_get_current_user.return_value = user_data
        mock_change_password.return_value = True
        
        # Test endpoint
        password_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123"
        }
        
        response = client.post(
            "/auth/change-password",
            json=password_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]

    @patch('auth.dependencies.get_current_active_user')
    def test_check_permission(self, mock_get_current_user):
        """Test permission checking."""
        # Setup mock
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "operator",
            "is_active": True
        }
        mock_get_current_user.return_value = user_data
        
        # Test endpoint
        permission_data = {
            "permission": "view",
            "resource": "dashboard"
        }
        
        response = client.post(
            "/auth/check-permission",
            json=permission_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "has_permission" in data
        assert data["permission"] == "view"

    def test_health_check(self):
        """Test authentication service health check."""
        response = client.get("/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"

    @patch('auth.dependencies.get_current_user')
    def test_logout(self, mock_get_current_user):
        """Test user logout."""
        # Setup mock
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "operator"
        }
        mock_get_current_user.return_value = user_data
        
        # Test endpoint
        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    @patch('auth.dependencies.get_current_user')
    def test_get_token_info(self, mock_get_current_user):
        """Test getting token information."""
        # Setup mock
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "created_at": datetime.utcnow().isoformat()
        }
        mock_get_current_user.return_value = user_data
        
        # Test endpoint
        response = client.get(
            "/auth/token/info",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401

    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestAuthAPIIntegration:
    """Integration tests for authentication API."""

    @patch('auth.api.get_db')
    def test_login_flow_integration(self, mock_get_db, mock_user):
        """Test complete login flow."""
        # Setup database mock
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock password verification
        with patch('auth.services.auth_service.verify_password', return_value=True):
            # Test login
            response = client.post(
                "/auth/login",
                data={"username": "testuser", "password": "password"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_permission_enforcement(self):
        """Test that permission enforcement works correctly."""
        # This would test actual permission checking
        # in a real implementation with database
        pass

    def test_role_based_access(self):
        """Test role-based access control."""
        # This would test RBAC functionality
        # in a real implementation
        pass


if __name__ == "__main__":
    pytest.main([__file__])
