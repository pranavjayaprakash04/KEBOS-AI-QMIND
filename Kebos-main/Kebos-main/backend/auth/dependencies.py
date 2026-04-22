"""
Authentication Dependencies

FastAPI dependency functions for authentication and authorization.
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Dict, Any
import os

from common.models import UserORM
from common.db import get_db
from .services import auth_service, AuthenticationError, AuthorizationError
from .schemas import UserRole

logger = logging.getLogger(__name__)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.warning("SECRET_KEY environment variable not set, using default")
    SECRET_KEY = "your-secret-key-here"

# JWT Algorithm
ALGORITHM = "HS256"

# Update auth service with environment secret key
auth_service.secret_key = SECRET_KEY


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Extract and validate current user from JWT token.
    Returns user information dictionary.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = auth_service.decode_token(token)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
            
        user_id = int(user_id_raw)
        
        # Query user from database
        user = await auth_service.get_user_by_id(db, user_id)
        if user is None:
            raise credentials_exception
            
        # Return user info as dict
        return auth_service.user_to_dict(user)
        
    except (AuthenticationError, ValueError, AttributeError) as e:
        logger.warning(f"Authentication failed: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Ensure current user is active.
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_permission(required_permission: str):
    """
    Dependency factory for role-based access control.
    Returns a dependency function that checks if user has required permission.
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "operator")
        
        # Check permission using auth service
        if not auth_service.check_permission(user_role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
            
        return current_user
    
    return permission_checker


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.
    Returns a dependency function that checks if user has required role.
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role", "operator")
        
        # Check role using auth service
        if not auth_service.check_role(user_role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
            
        return current_user
    
    return role_checker


# Common permission dependencies
require_admin = require_role("admin")
require_analyst = require_permission("analyze")
require_view = require_permission("view")
require_audit = require_permission("audit")
