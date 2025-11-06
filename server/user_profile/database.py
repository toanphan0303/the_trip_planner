"""
User Profile Database Operations
Handles CRUD operations for user preferences
"""

import os
from typing import Optional, List
from pymongo import MongoClient
from bson import ObjectId
from .models import UserPreference


class UserProfileDatabase:
    """Database operations for user preferences"""
    
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        self.db = self.client[os.getenv("MONGO_DB_NAME", "trip_planner_auth")]
        self.collection = self.db["user_preferences"]
        
        # Create indexes
        self.collection.create_index("user_id", unique=True)
        self.collection.create_index("created_at")
        self.collection.create_index("updated_at")
    
    def create_user_preferences(self, preferences: UserPreference) -> bool:
        """Create new user preferences"""
        try:
            preferences_dict = preferences.to_dict()
            result = self.collection.insert_one(preferences_dict)
            return result.inserted_id is not None
        except Exception as e:
            print(f"Error creating user preferences: {e}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreference]:
        """Get user preferences by user ID"""
        try:
            document = self.collection.find_one({"user_id": user_id})
            if document:
                return UserPreference.from_dict(document)
            return None
        except Exception as e:
            print(f"Error getting user preferences: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, preferences: UserPreference) -> bool:
        """Update user preferences"""
        try:
            preferences.update_timestamp()
            preferences_dict = preferences.to_dict()
            
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": preferences_dict},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"Error updating user preferences: {e}")
            return False
    
    def update_preferences_partial(self, user_id: str, updates: dict) -> bool:
        """Update specific parts of user preferences"""
        try:
            # Get existing preferences
            existing = self.get_user_preferences(user_id)
            if not existing:
                # Create new preferences if none exist
                existing = UserPreference(user_id=user_id)
            
            # Update the specified sections
            if "food" in updates:
                existing.food = existing.food.model_copy(update=updates["food"])
            if "stay" in updates:
                existing.stay = existing.stay.model_copy(update=updates["stay"])
            if "travel" in updates:
                existing.travel = existing.travel.model_copy(update=updates["travel"])
            
            return self.update_user_preferences(user_id, existing)
        except Exception as e:
            print(f"Error updating preferences partially: {e}")
            return False
    
    def delete_user_preferences(self, user_id: str) -> bool:
        """Delete user preferences"""
        try:
            result = self.collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user preferences: {e}")
            return False
    
    def get_all_preferences(self, limit: int = 100, skip: int = 0) -> List[UserPreference]:
        """Get all user preferences (for admin/debugging)"""
        try:
            cursor = self.collection.find().skip(skip).limit(limit).sort("updated_at", -1)
            preferences = []
            for doc in cursor:
                preferences.append(UserPreference.from_dict(doc))
            return preferences
        except Exception as e:
            print(f"Error getting all preferences: {e}")
            return []
    
    def get_preferences_count(self) -> int:
        """Get total count of user preferences"""
        try:
            return self.collection.count_documents({})
        except Exception as e:
            print(f"Error getting preferences count: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'client'):
            self.client.close()


# Global database instance (lazy-initialized)
_user_profile_db_instance = None


def get_user_profile_db() -> UserProfileDatabase:
    """Get or create the global UserProfileDatabase instance"""
    global _user_profile_db_instance
    if _user_profile_db_instance is None:
        _user_profile_db_instance = UserProfileDatabase()
    return _user_profile_db_instance


# Backward compatibility - will initialize on first access
user_profile_db = None  # Will be set when get_user_profile_db() is called
