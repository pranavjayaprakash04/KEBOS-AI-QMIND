"""
Authentication Module

FastAPI authentication and authorization module with JWT tokens,
role-based access control, and comprehensive security features.

Features:
- JWT-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- User management endpoints
- Permission checking
- Async support
- Comprehensive error handling
- Full test coverage

Usage:
    from auth.api import router as auth_router
    from auth.dependencies import get_current_user, require_admin
    from auth.schemas import UserInfo, LoginRequest
    
    app.include_router(auth_router)
"""

from .api import router
from .dependencies import (
    get_current_user,
    get_current_active_user,
    require_permission,
    require_role,
    require_admin,
    require_analyst,
    require_view,
    require_audit
)
from .services import auth_service, AuthenticationError, AuthorizationError
from .schemas import (
    UserRole,
    LoginRequest,
    LoginResponse,
    UserInfo,
    UserCreate,
    UserUpdate,
    PasswordChange,
    TokenInfo,
    PermissionCheck,
    PermissionResponse
)

__all__ = [
    # Router
    "router",
    
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_permission",
    "require_role",
    "require_admin",
    "require_analyst",
    "require_view", 
    "require_audit",
    
    # Services
    "auth_service",
    "AuthenticationError",
    "AuthorizationError",
    
    # Schemas
    "UserRole",
    "LoginRequest",
    "LoginResponse", 
    "UserInfo",
    "UserCreate",
    "UserUpdate",
    "PasswordChange",
    "TokenInfo",
    "PermissionCheck",
    "PermissionResponse"
]
