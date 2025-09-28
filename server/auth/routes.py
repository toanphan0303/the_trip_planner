"""
Authentication API routes
FastAPI routes for user authentication and management
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any
from .models import LoginRequest, AuthResponse, UserResponse, Token
from .facebook_auth import facebook_auth
from .middleware import get_current_user
from .database import auth_db
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/facebook/login")
async def facebook_login():
    """
    Initiate Facebook OAuth login
    Redirects user to Facebook login page
    """
    login_url = facebook_auth.get_facebook_login_url()
    return {"login_url": login_url}


@router.get("/facebook/callback")
async def facebook_callback(code: str, state: str = None):
    """
    Handle Facebook OAuth callback
    Exchange authorization code for access token and authenticate user
    """
    try:
        # Exchange code for access token
        token_data = facebook_auth.exchange_code_for_token(code)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from Facebook"
            )
        
        # Authenticate user with Facebook token
        user = facebook_auth.authenticate_user(access_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with Facebook"
            )
        
        # Create JWT token
        jwt_token = facebook_auth.create_jwt_token(user)
        
        # Create response
        token_response = Token(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=facebook_auth.jwt_expire_hours * 3600  # Convert hours to seconds
        )
        
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_picture_url=user.profile_picture_url,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
            preferences=user.preferences
        )
        
        return AuthResponse(
            user=user_response,
            token=token_response,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/login")
async def login(login_request: LoginRequest):
    """
    Login with Facebook access token
    Alternative endpoint for direct token authentication
    """
    try:
        # Authenticate user with Facebook token
        user = facebook_auth.authenticate_user(login_request.facebook_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Facebook token or authentication failed"
            )
        
        # Create JWT token
        jwt_token = facebook_auth.create_jwt_token(user)
        
        # Create response
        token_response = Token(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=facebook_auth.jwt_expire_hours * 3600
        )
        
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_picture_url=user.profile_picture_url,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
            preferences=user.preferences
        )
        
        return AuthResponse(
            user=user_response,
            token=token_response,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return current_user


@router.get("/profile")
async def get_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """
    Get detailed user profile
    """
    return {
        "user": current_user,
        "profile_complete": bool(current_user.preferences),
        "account_age_days": (datetime.utcnow() - current_user.created_at).days
    }


@router.put("/profile/preferences")
async def update_user_preferences(
    preferences: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user preferences
    """
    try:
        success = auth_db.update_user_preferences(current_user.id, preferences)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        return {"message": "Preferences updated successfully", "preferences": preferences}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preferences: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user: UserResponse = Depends(get_current_user)):
    """
    Logout user (client-side token removal)
    """
    return {"message": "Logout successful", "user_id": current_user.id}


@router.delete("/account")
async def deactivate_account(current_user: UserResponse = Depends(get_current_user)):
    """
    Deactivate user account
    """
    try:
        success = auth_db.deactivate_user(current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate account"
            )
        
        return {"message": "Account deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deactivating account: {str(e)}"
        )


@router.get("/status")
async def auth_status(current_user: Optional[UserResponse] = Depends(get_current_user)):
    """
    Check authentication status
    """
    if current_user:
        return {
            "authenticated": True,
            "user": current_user
        }
    else:
        return {
            "authenticated": False,
            "user": None
        }


@router.post("/facebook/share")
async def share_to_facebook(
    share_data: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Share content to Facebook (requires Facebook token)
    """
    try:
        facebook_token = share_data.get("facebook_token")
        message = share_data.get("message", "")
        
        if not facebook_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facebook token is required for sharing"
            )
        
        # Post to Facebook wall
        result = facebook_auth.post_to_wall(facebook_token, message)
        
        if result:
            return {
                "success": True,
                "post_id": result.get("id"),
                "message": "Successfully shared to Facebook"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to share to Facebook"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sharing to Facebook: {str(e)}"
        )


@router.get("/facebook/friends")
async def get_facebook_friends(
    facebook_token: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's Facebook friends (Note: user_friends permission is deprecated by Facebook)
    """
    return {
        "success": False,
        "message": "Facebook has deprecated the user_friends permission. This feature is no longer available.",
        "friends": [],
        "count": 0
    }


@router.get("/facebook/likes")
async def get_facebook_likes(
    facebook_token: str,
    limit: int = 100,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's Facebook likes (requires user_likes permission and App Review)
    """
    try:
        likes = facebook_auth.get_user_likes(facebook_token, limit)
        
        if likes is not None:
            return {
                "success": True,
                "likes": likes.get("data", []),
                "count": len(likes.get("data", [])),
                "paging": likes.get("paging", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get likes or permission denied. Make sure your app has user_likes permission approved by Facebook."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting likes: {str(e)}"
        )


@router.get("/facebook/preferences")
async def get_user_preferences(
    facebook_token: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze user's Facebook likes to extract travel preferences
    """
    try:
        preferences = facebook_auth.analyze_user_preferences(facebook_token)
        
        if preferences is not None:
            return {
                "success": True,
                "preferences": preferences,
                "message": "Travel preferences extracted from Facebook likes"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to analyze preferences or permission denied. Make sure your app has user_likes permission approved by Facebook."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing preferences: {str(e)}"
        )


@router.post("/preferences/update")
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user preferences in the database
    """
    try:
        success = auth_db.update_user_preferences(current_user.id, preferences)
        
        if success:
            return {
                "success": True,
                "message": "Preferences updated successfully",
                "preferences": preferences
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update preferences"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating preferences: {str(e)}"
        )
