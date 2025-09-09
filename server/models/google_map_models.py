"""
Google Places API Models - Using Google's Built-in Models
This module uses Google's built-in request/response models directly
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class GooglePlacesRequest:
    """Wrapper for Google Places API requests using built-in models"""
    text_query: str
    max_result_count: int = 20
    language_code: Optional[str] = None
    region_code: Optional[str] = None
    included_type: Optional[str] = None
    open_now: Optional[bool] = None
    min_rating: Optional[float] = None
    price_levels: Optional[List[str]] = None
    location_bias: Optional[Dict[str, Any]] = None
    location_restriction: Optional[Dict[str, Any]] = None

    def to_google_request(self) -> Dict[str, Any]:
        """Convert to Google's built-in TextSearchRequest format"""
        request = {
            "textQuery": self.text_query,
            "maxResultCount": min(max(self.max_result_count, 1), 20)
        }
        
        if self.language_code:
            request["languageCode"] = self.language_code
        if self.region_code:
            request["regionCode"] = self.region_code
        if self.included_type:
            request["includedType"] = self.included_type
        if self.open_now is not None:
            request["openNow"] = self.open_now
        if self.min_rating is not None:
            request["minRating"] = max(0.0, min(self.min_rating, 5.0))
        if self.price_levels:
            request["priceLevels"] = self.price_levels
        if self.location_bias:
            request["locationBias"] = self.location_bias
        if self.location_restriction:
            request["locationRestriction"] = self.location_restriction
            
        return request


@dataclass
class GooglePlacesResponse:
    """Wrapper for Google Places API responses using built-in models"""
    places: List[Dict[str, Any]]
    next_page_token: Optional[str] = None
    
    @classmethod
    def from_google_response(cls, response_data: Dict[str, Any]) -> 'GooglePlacesResponse':
        """Create from Google's built-in TextSearchResponse format"""
        return cls(
            places=response_data.get("places", []),
            next_page_token=response_data.get("nextPageToken")
        )
    
    def get_place_summary(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from a Google Place object"""
        return {
            "id": place.get("id", ""),
            "name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "location": place.get("location", {}),
            "rating": place.get("rating"),
            "types": place.get("types", []),
            "price_level": place.get("priceLevel"),
            "business_status": place.get("businessStatus"),
            "website": place.get("websiteUri"),
            "opening_hours": place.get("currentOpeningHours", {})
        }
    
    def get_formatted_places(self) -> List[Dict[str, Any]]:
        """Get formatted list of places with key information"""
        return [self.get_place_summary(place) for place in self.places]


# Field masks for different use cases
class GooglePlacesFieldMasks:
    """Predefined field masks for Google Places API requests"""
    
    BASIC = "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.types"
    
    DETAILED = (
        "places.id,places.displayName,places.formattedAddress,places.location,"
        "places.rating,places.types,places.priceLevel,places.businessStatus,"
        "places.currentOpeningHours,places.websiteUri"
    )
    
    COMPREHENSIVE = (
        "places.id,places.displayName,places.formattedAddress,places.location,"
        "places.rating,places.types,places.priceLevel,places.businessStatus,"
        "places.currentOpeningHours,places.websiteUri,places.userRatingCount,"
        "places.reviews,places.photos"
    )


# Backward compatibility aliases (for existing code)
PlacesSearchResponse = GooglePlacesResponse
PlacesNearbyResponse = GooglePlacesResponse
Place = Dict[str, Any]  # Google's built-in Place is just a dict