"""
Facebook authentication using official Facebook SDK
Clean implementation with SDK as primary method
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
import facebook

from .models import FacebookUserData, User, UserCreate
from .database import auth_db


class FacebookAuth:
    """Facebook authentication using official Facebook SDK"""
    
    def __init__(self):
        """Initialize Facebook authentication with SDK"""
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/auth/facebook/callback")
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expire_hours = 24 * 7  # 7 days
        
        if not self.app_id or not self.app_secret:
            raise ValueError("Facebook App ID and App Secret must be set in environment variables")
        
        # Initialize Facebook Graph API client
        self.graph = facebook.GraphAPI()
    
    def get_facebook_login_url(self) -> str:
        """Generate Facebook login URL with basic scopes"""
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": "public_profile",
            "response_type": "code",
            "state": "random_state_string",  # In production, use a proper state parameter
            "auth_type": "rerequest"  # Force re-authentication if user previously denied permissions
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://www.facebook.com/v18.0/dialog/oauth?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token using SDK"""
        try:
            token_info = self.graph.get_access_token_from_code(
                code, 
                redirect_uri=self.redirect_uri,
                app_id=self.app_id,
                app_secret=self.app_secret
            )
            return token_info
        except facebook.GraphAPIError as e:
            print(f"Facebook SDK error during token exchange: {e}")
            return None
    
    def validate_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validate Facebook access token using SDK"""
        try:
            # Set the access token
            self.graph.access_token = access_token
            
            # Debug token to validate
            debug_info = self.graph.get_object(
                "/debug_token",
                input_token=access_token,
                access_token=f"{self.app_id}|{self.app_secret}"
            )
            
            if debug_info.get("data", {}).get("is_valid", False):
                return debug_info["data"]
            return None
            
        except facebook.GraphAPIError as e:
            print(f"Facebook SDK error during token validation: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[FacebookUserData]:
        """Get user information from Facebook using SDK"""
        try:
            # Set the access token
            self.graph.access_token = access_token
            
            # Get user info with basic fields (email may not be available)
            user_data = self.graph.get_object(
                "me",
                fields="id,name,picture.width(200).height(200)"
            )
            
            # Try to get email separately if available
            email = ""
            try:
                email_data = self.graph.get_object("me", fields="email")
                email = email_data.get("email", "")
            except facebook.GraphAPIError:
                # Email permission not available or denied
                email = ""
            
            # Handle picture data
            picture_data = user_data.get("picture")
            
            return FacebookUserData(
                id=user_data["id"],
                name=user_data["name"],
                email=email,
                picture=picture_data
            )
            
        except facebook.GraphAPIError as e:
            print(f"Facebook SDK error getting user info: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting user info: {e}")
            return None
    
    def get_user_friends(self, access_token: str) -> Optional[list]:
        """Get user's friends list (Note: user_friends permission is deprecated)"""
        # Note: Facebook has deprecated the user_friends permission
        # This method is kept for backward compatibility but will return None
        print("Warning: user_friends permission is deprecated by Facebook")
        return None
    
    def get_user_likes(self, access_token: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get user's liked pages (requires user_likes permission and App Review)"""
        try:
            self.graph.access_token = access_token
            
            # Get user's liked pages
            likes_data = self.graph.get_object(
                "me/likes",
                fields="name,category,id,created_time",
                limit=limit
            )
            
            return likes_data
            
        except facebook.GraphAPIError as e:
            print(f"Error getting user likes: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting user likes: {e}")
            return None
    
    def analyze_user_preferences(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Analyze user's likes to extract travel preferences"""
        try:
            likes_data = self.get_user_likes(access_token)
            if not likes_data:
                return None
            
            # Categorize likes by interest areas
            preferences = {
                "travel_interests": [],
                "food_preferences": [],
                "entertainment": [],
                "sports": [],
                "culture": [],
                "shopping": [],
                "outdoor_activities": [],
                "nightlife": [],
                "family_friendly": [],
                "budget_level": "medium",  # Default
                "travel_style": "balanced"  # Default
            }
            
            # Map categories to preferences
            category_mapping = {
                "Travel/Leisure": "travel_interests",
                "Food/Beverages": "food_preferences", 
                "Restaurant/Cafe": "food_preferences",
                "Entertainment": "entertainment",
                "Sports": "sports",
                "Museum/Art Gallery": "culture",
                "Shopping/Retail": "shopping",
                "Outdoor/Recreation": "outdoor_activities",
                "Bar/Club": "nightlife",
                "Family/Kids": "family_friendly",
                "Hotel/Lodging": "travel_interests"
            }
            
            for like in likes_data.get("data", []):
                category = like.get("category", "")
                name = like.get("name", "")
                
                # Map category to preference type
                for cat_key, pref_key in category_mapping.items():
                    if cat_key.lower() in category.lower():
                        if name not in preferences[pref_key]:
                            preferences[pref_key].append(name)
                        break
                
                # Special analysis for specific pages
                name_lower = name.lower()
                if any(word in name_lower for word in ["luxury", "premium", "5-star", "upscale"]):
                    preferences["budget_level"] = "high"
                elif any(word in name_lower for word in ["budget", "cheap", "affordable", "backpack"]):
                    preferences["budget_level"] = "low"
                
                if any(word in name_lower for word in ["adventure", "extreme", "hiking", "climbing"]):
                    preferences["travel_style"] = "adventure"
                elif any(word in name_lower for word in ["relax", "spa", "wellness", "peaceful"]):
                    preferences["travel_style"] = "relaxation"
            
            return preferences
            
        except Exception as e:
            print(f"Error analyzing user preferences: {e}")
            return None
    
    def post_to_wall(self, access_token: str, message: str) -> Optional[Dict[str, Any]]:
        """Post a message to user's Facebook wall"""
        try:
            self.graph.access_token = access_token
            
            result = self.graph.put_object(
                "me",
                "feed",
                message=message
            )
            
            return result
            
        except facebook.GraphAPIError as e:
            print(f"Error posting to wall: {e}")
            return None
    
    def authenticate_user(self, facebook_token: str) -> Optional[User]:
        """Complete authentication flow with Facebook token"""
        # Validate the token
        token_data = self.validate_access_token(facebook_token)
        if not token_data:
            return None
        
        # Get user info from Facebook
        facebook_user = self.get_user_info(facebook_token)
        if not facebook_user:
            return None
        
        # Check if user exists by Facebook ID first
        existing_user = auth_db.get_user_by_facebook_id(facebook_user.id)
        
        if existing_user:
            # Update existing user with latest Facebook info and last login
            updated_user = self.update_existing_user(existing_user, facebook_user)
            auth_db.update_user_login(updated_user.id)
            return updated_user
        else:
            # Check if user exists by email (only if email is available)
            existing_user = None
            if facebook_user.email:
                existing_user = auth_db.get_user_by_email(facebook_user.email)
                if existing_user:
                    # Link Facebook account to existing user and update with Facebook info
                    updated_user = self.link_facebook_to_existing_user(existing_user, facebook_user)
                    auth_db.update_user_login(updated_user.id)
                    return updated_user
            
            # Create new user
            # Use Facebook ID as email if email is not available
            user_email = facebook_user.email if facebook_user.email else f"{facebook_user.id}@facebook.local"
            
            user_data = UserCreate(
                email=user_email,
                name=facebook_user.name,
                facebook_id=facebook_user.id,
                profile_picture_url=facebook_user.get_profile_picture_url()
            )
            return auth_db.create_user(user_data)
    
    def update_existing_user(self, existing_user: User, facebook_user: FacebookUserData) -> User:
        """Update existing user with latest Facebook information"""
        try:
            # Update user with latest Facebook info
            auth_db.update_user_facebook_info(
                existing_user.id,
                facebook_user.name,
                facebook_user.get_profile_picture_url()
            )
            
            # Get updated user from database
            updated_user = auth_db.get_user_by_id(existing_user.id)
            return updated_user if updated_user else existing_user
            
        except Exception as e:
            print(f"Error updating existing user: {e}")
            return existing_user
    
    def link_facebook_to_existing_user(self, existing_user: User, facebook_user: FacebookUserData) -> User:
        """Link Facebook account to existing user and update with Facebook info"""
        try:
            # Link Facebook ID to existing user
            auth_db.link_facebook_account(
                existing_user.id,
                facebook_user.id,
                facebook_user.name,
                facebook_user.get_profile_picture_url()
            )
            
            # Get updated user from database
            updated_user = auth_db.get_user_by_id(existing_user.id)
            return updated_user if updated_user else existing_user
            
        except Exception as e:
            print(f"Error linking Facebook to existing user: {e}")
            return existing_user
    
    def create_jwt_token(self, user: User) -> str:
        """Create JWT token for authenticated user"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expire_hours),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError:
            return None
    
    def get_current_user_from_token(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        return auth_db.get_user_by_id(user_id)


# Global Facebook auth instance
facebook_auth = FacebookAuth()
