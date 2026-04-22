"""
Authentication Services

Core authentication and authorization business logic.
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from common.models import UserORM
from .schemas import UserCreate, UserUpdate, UserInfo, UserRole

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
import os
JWT_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(hours=24)

# RBAC Configuration
ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["all"],
    UserRole.AUDITOR: ["view", "audit"],
    UserRole.ANALYST: ["view", "analyze", "threat_detection"],
    UserRole.OPERATOR: ["view", "monitor"],
    UserRole.DEVELOPER: ["upload", "test", "view"]
}


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class AuthorizationError(Exception):
    """Authorization related errors."""
    pass


class AuthService:
    """Authentication service class."""

    def __init__(self, secret_key: str = JWT_SECRET_KEY, algorithm: str = JWT_ALGORITHM):
        """Initialize authentication service."""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_delta = JWT_EXPIRATION_DELTA

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise AuthenticationError("Failed to hash password")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def create_access_token(self, user_id: int, additional_claims: Optional[Dict] = None) -> str:
        """Create a JWT access token."""
        try:
            now = datetime.utcnow()
            expire = now + self.expiration_delta
            
            payload = {
                "sub": str(user_id),
                "iat": now,
                "exp": expire,
                "type": "access_token"
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Access token created for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise AuthenticationError("Failed to create access token")

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Validate token type
            if payload.get("type") != "access_token":
                raise AuthenticationError("Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise AuthenticationError("Token has expired")
        except jwt.JWTClaimsError:
            logger.warning("Invalid token claims")
            raise AuthenticationError("Invalid token claims")
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid token")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify token and return payload with user information."""
        try:
            payload = self.decode_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("Token missing user information")
            
            return {
                "user_id": int(user_id),
                "username": payload.get("username"),
                "role": payload.get("role"),
                "exp": payload.get("exp")
            }
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            raise AuthenticationError("Token verification failed")

    async def authenticate_user(self, db: Session, username: str, password: str) -> Optional[UserORM]:
        """Authenticate a user with username and password."""
        try:
            user = db.query(UserORM).filter(UserORM.username == username).first()
            
            if not user:
                logger.warning(f"Authentication failed: user '{username}' not found")
                return None
            
            if not user.is_active:
                logger.warning(f"Authentication failed: user '{username}' is inactive")
                return None
            
            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password for user '{username}'")
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            logger.info(f"User '{username}' authenticated successfully")
            return user
            
        except SQLAlchemyError as e:
            logger.error(f"Database error during authentication: {e}")
            db.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return None

    async def get_user_by_id(self, db: Session, user_id: int) -> Optional[UserORM]:
        """Get user by ID."""
        try:
            user = db.query(UserORM).filter(UserORM.id == user_id).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by ID: {e}")
            return None

    async def create_user(self, db: Session, user_data: UserCreate) -> UserORM:
        """Create a new user."""
        try:
            # Check if username already exists
            existing_user = db.query(UserORM).filter(UserORM.username == user_data.username).first()
            if existing_user:
                raise AuthenticationError(f"Username '{user_data.username}' already exists")
            
            # Check if email already exists
            existing_email = db.query(UserORM).filter(UserORM.email == user_data.email).first()
            if existing_email:
                raise AuthenticationError(f"Email '{user_data.email}' already exists")
            
            # Create new user
            hashed_password = self.hash_password(user_data.password)
            user = UserORM(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                role=user_data.role.value,
                is_active=user_data.is_active,
                created_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"User '{user_data.username}' created successfully")
            return user
            
        except SQLAlchemyError as e:
            logger.error(f"Database error creating user: {e}")
            db.rollback()
            raise AuthenticationError("Failed to create user")

    async def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> Optional[UserORM]:
        """Update user information."""
        try:
            user = db.query(UserORM).filter(UserORM.id == user_id).first()
            if not user:
                return None
            
            # Update fields if provided
            if user_data.email is not None:
                user.email = user_data.email
            if user_data.role is not None:
                user.role = user_data.role.value
            if user_data.is_active is not None:
                user.is_active = user_data.is_active
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"User {user_id} updated successfully")
            return user
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating user: {e}")
            db.rollback()
            return None

    async def change_password(self, db: Session, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            user = db.query(UserORM).filter(UserORM.id == user_id).first()
            if not user:
                return False
            
            # Verify current password
            if not self.verify_password(current_password, user.hashed_password):
                logger.warning(f"Password change failed: invalid current password for user {user_id}")
                return False
            
            # Update password
            user.hashed_password = self.hash_password(new_password)
            db.commit()
            
            logger.info(f"Password changed successfully for user {user_id}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error changing password: {e}")
            db.rollback()
            return False

    def user_to_dict(self, user: UserORM) -> Dict[str, Any]:
        """Convert UserORM to dictionary."""
        return {
            "user_id": user.id,
            "username": user.username,
            "email": getattr(user, 'email', None),
            "role": getattr(user, 'role', 'operator'),
            "is_active": getattr(user, 'is_active', True),
            "created_at": getattr(user, 'created_at', None),
            "last_login": getattr(user, 'last_login', None),
            "permissions": self.get_user_permissions(getattr(user, 'role', 'operator'))
        }

    def get_user_permissions(self, role: str) -> List[str]:
        """Get permissions for a role."""
        try:
            user_role = UserRole(role)
            return ROLE_PERMISSIONS.get(user_role, [])
        except ValueError:
            logger.warning(f"Unknown role: {role}")
            return []

    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission."""
        permissions = self.get_user_permissions(user_role)
        return "all" in permissions or required_permission in permissions

    def check_role(self, user_role: str, required_role: str) -> bool:
        """Check if user has required role."""
        return user_role == required_role or user_role == "admin"


# Global auth service instance
auth_service = AuthService()
