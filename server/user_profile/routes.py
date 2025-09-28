"""
User Profile API Routes
FastAPI routes for user preference management
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from .models import (
    UserPreference,
    PreferenceUpdateRequest,
    PreferenceResponse,
    FoodPreference,
    StayPreference,
    TravelPreference
)
from .database import user_profile_db
from auth.middleware import get_current_user
from auth.models import UserResponse

router = APIRouter(prefix="/user-profile", tags=["user-profile"])


@router.get("/preferences", response_model=PreferenceResponse)
async def get_user_preferences(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user's preferences"""
    try:
        preferences = user_profile_db.get_user_preferences(current_user.id)
        
        if preferences:
            return PreferenceResponse(
                success=True,
                message="User preferences retrieved successfully",
                preferences=preferences
            )
        else:
            # Return default preferences if none exist
            default_preferences = UserPreference(user_id=current_user.id)
            return PreferenceResponse(
                success=True,
                message="No preferences found, returning defaults",
                preferences=default_preferences
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user preferences: {str(e)}"
        )


@router.post("/preferences", response_model=PreferenceResponse)
async def create_user_preferences(
    preferences: UserPreference,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create or update user preferences"""
    try:
        # Ensure the user_id matches the authenticated user
        preferences.user_id = current_user.id
        
        success = user_profile_db.update_user_preferences(current_user.id, preferences)
        
        if success:
            return PreferenceResponse(
                success=True,
                message="User preferences created/updated successfully",
                preferences=preferences
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create/update user preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating/updating user preferences: {str(e)}"
        )


@router.patch("/preferences", response_model=PreferenceResponse)
async def update_user_preferences_partial(
    updates: PreferenceUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update specific parts of user preferences"""
    try:
        # Convert updates to dict format expected by database
        updates_dict = {}
        if updates.food:
            updates_dict["food"] = updates.food
        if updates.stay:
            updates_dict["stay"] = updates.stay
        if updates.travel:
            updates_dict["travel"] = updates.travel
        
        if not updates_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )
        
        success = user_profile_db.update_preferences_partial(current_user.id, updates_dict)
        
        if success:
            # Get updated preferences
            updated_preferences = user_profile_db.get_user_preferences(current_user.id)
            return PreferenceResponse(
                success=True,
                message="User preferences updated successfully",
                preferences=updated_preferences
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user preferences: {str(e)}"
        )


@router.put("/preferences/food", response_model=PreferenceResponse)
async def update_food_preferences(
    food_prefs: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """Update only food preferences"""
    try:
        success = user_profile_db.update_preferences_partial(
            current_user.id, 
            {"food": food_prefs}
        )
        
        if success:
            updated_preferences = user_profile_db.get_user_preferences(current_user.id)
            return PreferenceResponse(
                success=True,
                message="Food preferences updated successfully",
                preferences=updated_preferences
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update food preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating food preferences: {str(e)}"
        )


@router.put("/preferences/stay", response_model=PreferenceResponse)
async def update_stay_preferences(
    stay_prefs: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """Update only stay preferences"""
    try:
        success = user_profile_db.update_preferences_partial(
            current_user.id, 
            {"stay": stay_prefs}
        )
        
        if success:
            updated_preferences = user_profile_db.get_user_preferences(current_user.id)
            return PreferenceResponse(
                success=True,
                message="Stay preferences updated successfully",
                preferences=updated_preferences
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update stay preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating stay preferences: {str(e)}"
        )


@router.put("/preferences/travel", response_model=PreferenceResponse)
async def update_travel_preferences(
    travel_prefs: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """Update only travel preferences"""
    try:
        success = user_profile_db.update_preferences_partial(
            current_user.id, 
            {"travel": travel_prefs}
        )
        
        if success:
            updated_preferences = user_profile_db.get_user_preferences(current_user.id)
            return PreferenceResponse(
                success=True,
                message="Travel preferences updated successfully",
                preferences=updated_preferences
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update travel preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating travel preferences: {str(e)}"
        )


@router.delete("/preferences", response_model=PreferenceResponse)
async def delete_user_preferences(
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete user preferences"""
    try:
        success = user_profile_db.delete_user_preferences(current_user.id)
        
        if success:
            return PreferenceResponse(
                success=True,
                message="User preferences deleted successfully",
                preferences=None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No preferences found to delete"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user preferences: {str(e)}"
        )


@router.get("/preferences/schema")
async def get_preferences_schema():
    """Get the schema for user preferences (for frontend form generation)"""
    return {
        "food": {
            "preferred_cuisines": list(FoodPreference.model_fields["preferred_cuisines"].annotation.__args__[0].__members__.keys()),
            "food_types": list(FoodPreference.model_fields["food_types"].annotation.__args__[0].__members__.keys()),
            "budget_levels": list(FoodPreference.model_fields["budget_level"].annotation.__members__.keys()),
            "spice_tolerance": {"min": 1, "max": 5, "default": 3}
        },
        "stay": {
            "preferred_types": list(StayPreference.model_fields["preferred_types"].annotation.__args__[0].__members__.keys()),
            "budget_levels": list(StayPreference.model_fields["budget_level"].annotation.__members__.keys()),
            "amenities": ["wifi", "air_conditioning", "parking", "breakfast", "gym", "pool", "spa"]
        },
        "travel": {
            "travel_styles": list(TravelPreference.model_fields["travel_style"].annotation.__members__.keys()),
            "transport_modes": list(TravelPreference.model_fields["preferred_transport"].annotation.__args__[0].__members__.keys()),
            "activity_types": list(TravelPreference.model_fields["activity_interests"].annotation.__args__[0].__members__.keys()),
            "budget_levels": list(TravelPreference.model_fields["budget_level"].annotation.__members__.keys())
        }
    }
