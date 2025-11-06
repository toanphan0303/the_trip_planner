"""
Utility functions for POI (Point of Interest) operations and search optimization
"""

from models.point_of_interest_models import PointOfInterest
from constant.place_types import PlaceTypes


def is_restaurant(poi: PointOfInterest) -> bool:
    """
    Check if a PointOfInterest is a restaurant based on its category.
    Uses the official place types from PlaceTypes constants.
    
    Args:
        poi: PointOfInterest object to check
        
    Returns:
        True if the POI is a restaurant, False otherwise
    """
    if not poi.types:
        return False
    
    # Get all food and drink related place types from the constants
    food_types = PlaceTypes.get_food_types()
    
    # Check if any of the POI's types match food types
    for type_name in poi.types:
        if type_name.lower() in food_types:
            return True
    
    return False
