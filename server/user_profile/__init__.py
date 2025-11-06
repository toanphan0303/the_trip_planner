"""
User Profile Package
Handles user preferences and profile management
"""

from .models import (
    UserPreference,
    FoodPreference,
    StayPreference,
    TravelPreference,
    TravelStyle
)

__all__ = [
    "UserPreference",
    "FoodPreference", 
    "StayPreference",
    "TravelPreference",
    "TravelStyle"
]
