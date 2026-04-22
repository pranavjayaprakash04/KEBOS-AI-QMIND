"""
Authentication API

FastAPI routes for authentication and user management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from common.db import get_db
from .schemas import (
    LoginRequest, LoginResponse, UserInfo, UserCreate, UserUpdate, 
    PasswordChange, TokenInfo, PermissionCheck, PermissionResponse
)
from .services import auth_service, AuthenticationError, AuthorizationError
from .dependencies import (
    get_current_user, get_current_active_user, 
    require_admin, require_view, require_audit
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, summary="User login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    - **username**: User's username
    - **password**: User's password
    
    Returns JWT access token and user information.
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = auth_service.create_access_token(user.id)
        
        # Prepare response
        user_info = auth_service.user_to_dict(user)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(auth_service.expiration_delta.total_seconds()),
            user=user_info
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )


@router.get("/me", response_model=UserInfo, summary="Get current user info")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get information about the currently authenticated user.
    
    Returns user profile information and permissions.
    """
    return UserInfo(**current_user)


@router.get("/users", response_model=List[UserInfo], summary="List all users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    List all users in the system.
    
    Requires admin role.
    """
    try:
        # This would be implemented in a real system
        # For now, return current user as example
        return [UserInfo(**current_user)]
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.post("/users", response_model=UserInfo, summary="Create new user")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Create a new user account.
    
    Requires admin role.
    """
    try:
        user = await auth_service.create_user(db, user_data)
        return UserInfo(**auth_service.user_to_dict(user))
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put("/users/{user_id}", response_model=UserInfo, summary="Update user")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Update user information.
    
    Requires admin role.
    """
    try:
        user = await auth_service.update_user(db, user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserInfo(**auth_service.user_to_dict(user))
        
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/change-password", summary="Change password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Change current user's password.
    
    User can only change their own password.
    """
    try:
        success = await auth_service.change_password(
            db, 
            current_user["user_id"], 
            password_data.current_password, 
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/check-permission", response_model=PermissionResponse, summary="Check permission")
async def check_permission(
    permission_check: PermissionCheck,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Check if current user has a specific permission.
    
    Useful for frontend permission-based UI rendering.
    """
    user_role = current_user.get("role", "operator")
    has_permission = auth_service.check_permission(user_role, permission_check.permission)
    
    return PermissionResponse(
        has_permission=has_permission,
        permission=permission_check.permission,
        resource=permission_check.resource,
        user_role=user_role
    )


@router.get("/token/info", response_model=TokenInfo, summary="Get token information")
async def get_token_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get information about the current access token.
    
    Returns token metadata and expiration info.
    """
    return TokenInfo(
        token_type="bearer",
        expires_in=int(auth_service.expiration_delta.total_seconds()),
        issued_at=current_user.get("created_at"),  # This should be token issue time
        user_id=current_user["user_id"]
    )


@router.post("/logout", summary="Logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Logout current user.
    
    In a stateless JWT system, this is mainly for client-side cleanup.
    In a production system, you might implement token blacklisting.
    """
    logger.info(f"User {current_user['user_id']} logged out")
    return {"message": "Successfully logged out"}


@router.get("/health", summary="Authentication service health check")
async def health_check():
    """
    Health check endpoint for authentication service.
    
    Returns service status and basic configuration.
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "1.0.0",
        "jwt_algorithm": auth_service.algorithm,
        "token_expiration_hours": auth_service.expiration_delta.total_seconds() / 3600
    }
