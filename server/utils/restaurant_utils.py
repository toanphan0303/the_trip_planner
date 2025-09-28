"""
Shared utilities for restaurant detection and categorization
"""

from typing import Dict, Any, Union
from models.point_of_interest_models import PointOfInterest
from constant.restaurant_constants import RESTAURANT_KEYWORDS, RESTAURANT_PLACE_TYPES


def is_restaurant(place: Union[PointOfInterest, Dict[str, Any]]) -> bool:
    """
    Check if a place is a restaurant based on category, tags, or type.
    
    Args:
        place: Either a PointOfInterest object or a dictionary containing place data
        
    Returns:
        True if the place is a restaurant, False otherwise
    """
    if isinstance(place, PointOfInterest):
        return _is_restaurant_poi(place)
    elif isinstance(place, dict):
        return _is_restaurant_dict(place)
    else:
        return False


def _is_restaurant_poi(place: PointOfInterest) -> bool:
    """Check if a PointOfInterest is a restaurant"""
    if not place:
        return False
    
    # Check types
    if place.types:
        for type_name in place.types:
            type_lower = type_name.lower()
            if any(keyword in type_lower for keyword in RESTAURANT_KEYWORDS) or any(tag in type_lower for tag in RESTAURANT_PLACE_TYPES):
                return True
    
    # Check tags
    tags_lower = [tag.lower() for tag in place.tags]
    if any(keyword in ' '.join(tags_lower) for keyword in RESTAURANT_KEYWORDS):
        return True
    
    # Check if it's explicitly a restaurant type
    return any(rest_type in tags_lower for rest_type in RESTAURANT_PLACE_TYPES)


def _is_restaurant_dict(item_dict: Dict[str, Any]) -> bool:
    """Check if a dictionary item represents a restaurant"""
    if not item_dict:
        return False
    
    # Check category
    category = item_dict.get('category', '').lower()
    if any(keyword in category for keyword in RESTAURANT_KEYWORDS):
        return True
    
    # Check tags
    tags = item_dict.get('tags', [])
    tags_lower = [tag.lower() for tag in tags]
    if any(keyword in ' '.join(tags_lower) for keyword in RESTAURANT_KEYWORDS):
        return True
    
    # Check if it's explicitly a restaurant type
    return any(rest_type in tags_lower for rest_type in RESTAURANT_PLACE_TYPES)


def normalize_restaurant_name(name: str) -> str:
    """
    Normalize restaurant name for comparison by removing common suffixes.
    
    Args:
        name: Restaurant name to normalize
        
    Returns:
        Normalized restaurant name
    """
    if not name:
        return ""
    
    import re
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Remove common business suffixes
    suffixes_to_remove = [
        'inc', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co',
        'restaurant', 'cafe', 'bar', 'grill', 'kitchen', 'diner'
    ]
    
    for suffix in suffixes_to_remove:
        # Remove suffix with optional punctuation
        pattern = r'\s*' + re.escape(suffix) + r'[.,\s]*$'
        normalized = re.sub(pattern, '', normalized)
    
    # Remove extra whitespace and punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized
