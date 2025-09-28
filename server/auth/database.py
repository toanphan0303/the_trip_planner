"""
Authentication database operations
Handles user data persistence and retrieval using MongoDB
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from bson import ObjectId
from .models import User, UserCreate, UserResponse


class AuthDatabase:
    """Database operations for authentication"""
    
    def __init__(self):
        """Initialize database connection"""
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://admin:trip_planner_pass@localhost:27017/")
        self.database_name = "trip_planner_auth"
        self.collection_name = "users"
        
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better performance
            self.collection.create_index("email", unique=True)
            self.collection.create_index("facebook_id", unique=True, sparse=True)
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user in the database"""
        try:
            user_dict = {
                "email": user_data.email,
                "name": user_data.name,
                "facebook_id": user_data.facebook_id,
                "profile_picture_url": user_data.profile_picture_url,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "is_active": True,
                "preferences": {}
            }
            
            result = self.collection.insert_one(user_dict)
            user_dict["_id"] = result.inserted_id
            
            return User(
                id=str(result.inserted_id),
                email=user_dict["email"],
                name=user_dict["name"],
                facebook_id=user_dict["facebook_id"],
                profile_picture_url=user_dict["profile_picture_url"],
                created_at=user_dict["created_at"],
                last_login=user_dict["last_login"],
                is_active=user_dict["is_active"],
                preferences=user_dict["preferences"]
            )
            
        except Exception as e:
            print(f"Error creating user: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            user_doc = self.collection.find_one({"email": email})
            if user_doc:
                return self._document_to_user(user_doc)
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_facebook_id(self, facebook_id: str) -> Optional[User]:
        """Get user by Facebook ID"""
        try:
            user_doc = self.collection.find_one({"facebook_id": facebook_id})
            if user_doc:
                return self._document_to_user(user_doc)
            return None
        except Exception as e:
            print(f"Error getting user by Facebook ID: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_doc = self.collection.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return self._document_to_user(user_doc)
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def update_user_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user login: {e}")
            return False
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"preferences": preferences}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user preferences: {e}")
            return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False
    
    def _document_to_user(self, doc: Dict[str, Any]) -> User:
        """Convert MongoDB document to User model"""
        return User(
            id=str(doc["_id"]),
            email=doc["email"],
            name=doc["name"],
            facebook_id=doc.get("facebook_id"),
            profile_picture_url=doc.get("profile_picture_url"),
            created_at=doc["created_at"],
            last_login=doc.get("last_login"),
            is_active=doc["is_active"],
            preferences=doc.get("preferences", {})
        )
    
    def get_all_users(self) -> List[User]:
        """Get all users from the database"""
        try:
            cursor = self.collection.find({"is_active": True})
            users = []
            for doc in cursor:
                users.append(self._document_to_user(doc))
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"preferences": preferences}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user preferences: {e}")
            return False
    
    def update_user_facebook_info(self, user_id: str, name: str, profile_picture_url: Optional[str]) -> bool:
        """Update user's Facebook information (name and profile picture)"""
        try:
            update_data = {
                "name": name,
                "last_login": datetime.utcnow()
            }
            if profile_picture_url:
                update_data["profile_picture_url"] = profile_picture_url
            
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user Facebook info: {e}")
            return False
    
    def link_facebook_account(self, user_id: str, facebook_id: str, name: str, profile_picture_url: Optional[str]) -> bool:
        """Link Facebook account to existing user"""
        try:
            update_data = {
                "facebook_id": facebook_id,
                "name": name,
                "last_login": datetime.utcnow()
            }
            if profile_picture_url:
                update_data["profile_picture_url"] = profile_picture_url
            
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error linking Facebook account: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'client'):
            self.client.close()


# Global database instance
auth_db = AuthDatabase()
