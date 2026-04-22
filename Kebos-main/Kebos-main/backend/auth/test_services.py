"""
Authentication Services Tests

Comprehensive tests for authentication services and business logic.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from auth.services import AuthService, AuthenticationError, AuthorizationError
from auth.schemas import UserCreate, UserUpdate, UserRole
from common.models import UserORM


@pytest.fixture
def auth_service():
    """Create auth service instance for testing."""
    return AuthService(secret_key="test_secret_key")


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
    user.hashed_password = "$2b$12$test_hashed_password"
    user.role = "operator"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.last_login = None
    return user


class TestAuthService:
    """Test authentication service methods."""

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith("$2b$")

    def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        
        # Test correct password
        assert auth_service.verify_password(password, hashed) is True
        
        # Test incorrect password
        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_create_access_token(self, auth_service):
        """Test JWT token creation."""
        user_id = 1
        token = auth_service.create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Verify token can be decoded
        payload = auth_service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access_token"

    def test_create_access_token_with_claims(self, auth_service):
        """Test JWT token creation with additional claims."""
        user_id = 1
        additional_claims = {"role": "admin", "scope": "full"}
        token = auth_service.create_access_token(user_id, additional_claims)
        
        payload = auth_service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "admin"
        assert payload["scope"] == "full"

    def test_decode_token_valid(self, auth_service):
        """Test decoding valid token."""
        user_id = 1
        token = auth_service.create_access_token(user_id)
        
        payload = auth_service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access_token"
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_token_invalid(self, auth_service):
        """Test decoding invalid token."""
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(AuthenticationError, match="Invalid token"):
            auth_service.decode_token(invalid_token)

    def test_decode_token_expired(self, auth_service):
        """Test decoding expired token."""
        # Create service with same secret key but very short expiration
        short_service = AuthService(secret_key="test_secret_key")  # Use same key
        short_service.expiration_delta = timedelta(seconds=-1)  # Already expired
        
        token = short_service.create_access_token(1)
        
        with pytest.raises(AuthenticationError, match="Token has expired|Invalid token"):
            auth_service.decode_token(token)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_db, mock_user):
        """Test successful user authentication."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock password verification
        with patch.object(auth_service, 'verify_password', return_value=True):
            user = await auth_service.authenticate_user(mock_db, "testuser", "password")
            
            assert user == mock_user
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_db):
        """Test authentication with non-existent user."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user = await auth_service.authenticate_user(mock_db, "nonexistent", "password")
        
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, mock_db, mock_user):
        """Test authentication with inactive user."""
        # Setup mocks
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        user = await auth_service.authenticate_user(mock_db, "testuser", "password")
        
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, mock_db, mock_user):
        """Test authentication with wrong password."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock password verification
        with patch.object(auth_service, 'verify_password', return_value=False):
            user = await auth_service.authenticate_user(mock_db, "testuser", "wrong_password")
            
            assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, auth_service, mock_db, mock_user):
        """Test getting user by ID."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        user = await auth_service.get_user_by_id(mock_db, 1)
        
        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service, mock_db):
        """Test getting non-existent user by ID."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user = await auth_service.get_user_by_id(mock_db, 999)
        
        assert user is None

    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service, mock_db):
        """Test successful user creation."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing user
        new_user = Mock(spec=UserORM)
        new_user.id = 2
        new_user.username = "newuser"
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123",
            role=UserRole.OPERATOR
        )
        
        with patch('auth.services.UserORM', return_value=new_user):
            user = await auth_service.create_user(mock_db, user_data)
            
            assert user == new_user
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, auth_service, mock_db, mock_user):
        """Test creating user with duplicate username."""
        # Setup mocks - existing user found
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        user_data = UserCreate(
            username="testuser",  # Same as existing user
            email="new@example.com",
            password="password123",
            role=UserRole.OPERATOR
        )
        
        with pytest.raises(AuthenticationError, match="Username .* already exists"):
            await auth_service.create_user(mock_db, user_data)

    @pytest.mark.asyncio
    async def test_update_user_success(self, auth_service, mock_db, mock_user):
        """Test successful user update."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        user_data = UserUpdate(
            email="updated@example.com",
            role=UserRole.ANALYST
        )
        
        user = await auth_service.update_user(mock_db, 1, user_data)
        
        assert user == mock_user
        assert mock_user.email == "updated@example.com"
        assert mock_user.role == "analyst"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, auth_service, mock_db):
        """Test updating non-existent user."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user_data = UserUpdate(email="updated@example.com")
        
        user = await auth_service.update_user(mock_db, 999, user_data)
        
        assert user is None

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_db, mock_user):
        """Test successful password change."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch.object(auth_service, 'verify_password', return_value=True), \
             patch.object(auth_service, 'hash_password', return_value="new_hashed"):
            
            result = await auth_service.change_password(mock_db, 1, "old_password", "new_password")
            
            assert result is True
            assert mock_user.hashed_password == "new_hashed"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service, mock_db, mock_user):
        """Test password change with wrong current password."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch.object(auth_service, 'verify_password', return_value=False):
            result = await auth_service.change_password(mock_db, 1, "wrong_password", "new_password")
            
            assert result is False

    def test_user_to_dict(self, auth_service, mock_user):
        """Test converting user to dictionary."""
        user_dict = auth_service.user_to_dict(mock_user)
        
        assert user_dict["user_id"] == mock_user.id
        assert user_dict["username"] == mock_user.username
        assert user_dict["email"] == mock_user.email
        assert user_dict["role"] == mock_user.role
        assert user_dict["is_active"] == mock_user.is_active
        assert "permissions" in user_dict

    def test_get_user_permissions(self, auth_service):
        """Test getting user permissions by role."""
        # Test admin permissions
        admin_perms = auth_service.get_user_permissions("admin")
        assert "all" in admin_perms
        
        # Test analyst permissions
        analyst_perms = auth_service.get_user_permissions("analyst")
        assert "view" in analyst_perms
        assert "analyze" in analyst_perms
        
        # Test unknown role
        unknown_perms = auth_service.get_user_permissions("unknown")
        assert unknown_perms == []

    def test_check_permission(self, auth_service):
        """Test permission checking."""
        # Test admin (has all permissions)
        assert auth_service.check_permission("admin", "any_permission") is True
        
        # Test analyst with valid permission
        assert auth_service.check_permission("analyst", "view") is True
        assert auth_service.check_permission("analyst", "analyze") is True
        
        # Test analyst with invalid permission
        assert auth_service.check_permission("analyst", "admin_only") is False
        
        # Test operator
        assert auth_service.check_permission("operator", "view") is True
        assert auth_service.check_permission("operator", "analyze") is False

    def test_check_role(self, auth_service):
        """Test role checking."""
        # Test exact role match
        assert auth_service.check_role("admin", "admin") is True
        assert auth_service.check_role("analyst", "analyst") is True
        
        # Test admin can access any role
        assert auth_service.check_role("admin", "analyst") is True
        assert auth_service.check_role("admin", "operator") is True
        
        # Test non-admin cannot access other roles
        assert auth_service.check_role("analyst", "admin") is False
        assert auth_service.check_role("operator", "analyst") is False


class TestAuthServiceErrorHandling:
    """Test error handling in authentication service."""

    @pytest.mark.asyncio
    async def test_authenticate_user_db_error(self, auth_service, mock_db):
        """Test handling database error during authentication."""
        # Setup mock to raise SQLAlchemy error
        mock_db.query.side_effect = SQLAlchemyError("Database connection failed")
        
        user = await auth_service.authenticate_user(mock_db, "testuser", "password")
        
        assert user is None
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_db_error(self, auth_service, mock_db):
        """Test handling database error during user creation."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123",
            role=UserRole.OPERATOR
        )
        
        with pytest.raises(AuthenticationError, match="Failed to create user"):
            await auth_service.create_user(mock_db, user_data)
        
        mock_db.rollback.assert_called_once()

    def test_hash_password_error(self, auth_service):
        """Test handling error during password hashing."""
        with patch('auth.services.pwd_context.hash', side_effect=Exception("Hash error")):
            with pytest.raises(AuthenticationError, match="Failed to hash password"):
                auth_service.hash_password("password")

    def test_verify_password_error(self, auth_service):
        """Test handling error during password verification."""
        with patch('auth.services.pwd_context.verify', side_effect=Exception("Verify error")):
            result = auth_service.verify_password("password", "hash")
            assert result is False

    def test_create_token_error(self, auth_service):
        """Test handling error during token creation."""
        with patch('auth.services.jwt.encode', side_effect=Exception("JWT error")):
            with pytest.raises(AuthenticationError, match="Failed to create access token"):
                auth_service.create_access_token(1)


if __name__ == "__main__":
    pytest.main([__file__])
