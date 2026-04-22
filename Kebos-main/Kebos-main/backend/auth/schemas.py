"""
Authentication Schemas

Pydantic models for authentication requests and responses.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    AUDITOR = "auditor"
    ANALYST = "analyst"
    OPERATOR = "operator"
    DEVELOPER = "developer"


class LoginRequest(BaseModel):
    """Login request schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }
    )
    
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")


class LoginResponse(BaseModel):
    """Login response schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "role": "admin",
                    "is_active": True
                }
            }
        }
    )
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class UserInfo(BaseModel):
    """User information schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T10:30:00Z",
                "permissions": ["all"]
            }
        }
    )
    
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(default=True, description="User active status")
    created_at: Optional[datetime] = Field(None, description="Account creation time")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    permissions: List[str] = Field(default_factory=list, description="User permissions")


class UserCreate(BaseModel):
    """User creation schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "new_user",
                "email": "user@example.com",
                "password": "securepassword123",
                "role": "operator",
                "is_active": True
            }
        }
    )
    
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    role: UserRole = Field(default=UserRole.OPERATOR, description="User role")
    is_active: bool = Field(default=True, description="User active status")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain alphanumeric characters, hyphens, and underscores')
        return v.lower()


class UserUpdate(BaseModel):
    """User update schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "updated@example.com",
                "role": "analyst",
                "is_active": True
            }
        }
    )
    
    email: Optional[EmailStr] = Field(None, description="Email address")
    role: Optional[UserRole] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="User active status")


class PasswordChange(BaseModel):
    """Password change schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "currentpassword",
                "new_password": "newsecurepassword123"
            }
        }
    )
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class TokenInfo(BaseModel):
    """Token information schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token_type": "bearer",
                "expires_in": 3600,
                "issued_at": "2024-01-15T10:30:00Z",
                "user_id": 1
            }
        }
    )
    
    token_type: str = Field(..., description="Token type")
    expires_in: int = Field(..., description="Expiration time in seconds")
    issued_at: datetime = Field(..., description="Token issue time")
    user_id: int = Field(..., description="User ID")


class AuthError(BaseModel):
    """Authentication error schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "invalid_credentials",
                "message": "Invalid username or password",
                "detail": "Authentication failed"
            }
        }
    )
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class PermissionCheck(BaseModel):
    """Permission check schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "permission": "view",
                "resource": "threat_detection"
            }
        }
    )
    
    permission: str = Field(..., description="Permission to check")
    resource: Optional[str] = Field(None, description="Resource identifier")


class PermissionResponse(BaseModel):
    """Permission check response schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "has_permission": True,
                "permission": "view",
                "resource": "threat_detection",
                "user_role": "analyst"
            }
        }
    )
    
    has_permission: bool = Field(..., description="Whether user has permission")
    permission: str = Field(..., description="Checked permission")
    resource: Optional[str] = Field(None, description="Resource identifier")
    user_role: str = Field(..., description="User role")
