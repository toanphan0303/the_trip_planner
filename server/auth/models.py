"""
Authentication models for Trip Planner
Defines user data structures and authentication-related models
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from bson import ObjectId


class User(BaseModel):
    """User model for authentication"""
    id: Optional[str] = None  # MongoDB ObjectId as string
    email: str
    name: str
    facebook_id: Optional[str] = None
    profile_picture_url: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    is_active: bool = True
    preferences: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: str
    name: str
    facebook_id: Optional[str] = None
    profile_picture_url: Optional[str] = None


class UserResponse(BaseModel):
    """Model for user response (excluding sensitive data)"""
    id: str
    email: str
    name: str
    profile_picture_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    preferences: Optional[Dict[str, Any]] = None


class Token(BaseModel):
    """JWT Token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class FacebookUserData(BaseModel):
    """Facebook user data from OAuth"""
    id: str
    name: str
    email: str
    picture: Optional[Any] = None  # Allow any type for picture data
    
    def get_profile_picture_url(self) -> Optional[str]:
        """Extract profile picture URL from Facebook data"""
        if self.picture and isinstance(self.picture, dict):
            data = self.picture.get('data', {})
            if isinstance(data, dict):
                return data.get('url')
        return None


class LoginRequest(BaseModel):
    """Login request model"""
    facebook_token: str


class AuthResponse(BaseModel):
    """Authentication response model"""
    user: UserResponse
    token: Token
    message: str = "Login successful"
