"""
Google API client using base API infrastructure
"""

from typing import Optional, Dict, Any, List
from .base_api import BaseAPI
from models.google_map_models import (
    GooglePlacesRequest,
    GooglePlacesResponse,
    GooglePlacesFieldMasks
)


class GoogleAPI(BaseAPI):
    """Google API client for Places and Geocoding services"""
    
    def __init__(self):
        super().__init__("GOOGLE_API_KEY")
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """Parse response based on API type - implemented by specific methods"""
        return response_data
    
    def _parse_price_level(self, price_level: Optional[str]) -> Optional[int]:
        """Parse Google Places price level string to integer"""
        if not price_level:
            return None
        
        price_mapping = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4
        }
        
        return price_mapping.get(price_level)
    
    def places_search_text(
        self, 
        query: str, 
        *, 
        language_code: Optional[str] = None,
        region_code: Optional[str] = None,
        included_type: Optional[str] = None,
        open_now: Optional[bool] = None,
        min_rating: Optional[float] = None,
        max_results: int = 20,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
        price_levels: Optional[List[str]] = None,
        strict_type_filtering: Optional[bool] = None,
        location_bias: Optional[Dict[str, Any]] = None,
        location_restriction: Optional[Dict[str, Any]] = None
    ) -> GooglePlacesResponse:
        """
        Call Google Places Text Search API v1 and return Python object.

        Args:
            query: Free-form text query, e.g. "coffee shops in Paris".
            language_code: Optional BCP-47 language code.
            region_code: Optional region code to bias results.
            included_type: Optional place type to include in results.
            open_now: Optional filter for places currently open.
            min_rating: Optional minimum rating filter (0.0-5.0).
            max_results: Maximum number of place results to return (1-20).
            page_size: Optional page size for pagination.
            page_token: Optional token for pagination.
            price_levels: Optional list of price levels (PRICE_LEVEL_FREE, PRICE_LEVEL_INEXPENSIVE, etc.).
            strict_type_filtering: Optional strict type filtering.
            location_bias: Optional location bias object.
            location_restriction: Optional location restriction object.

        Returns:
            GooglePlacesResponse object with Google's built-in place data.
        """
        endpoint = "https://places.googleapis.com/v1/places:searchText"

        # Create request using Google's built-in model format
        request = GooglePlacesRequest(
            text_query=query,
            max_result_count=max_results,
            language_code=language_code,
            region_code=region_code,
            included_type=included_type,
            open_now=open_now,
            min_rating=min_rating,
            price_levels=price_levels,
            location_bias=location_bias,
            location_restriction=location_restriction
        )

        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": GooglePlacesFieldMasks.DETAILED,
            "Content-Type": "application/json",
        }

        # Make request using Google's built-in TextSearchRequest format
        response_data = self._post(endpoint, data=request.to_google_request(), headers=headers)
        
        # Return response using Google's built-in TextSearchResponse format
        return GooglePlacesResponse.from_google_response(response_data)

    def places_nearby_search(
        self, 
        location: str, 
        radius: int = 1000, 
        place_type: Optional[str] = None, 
        keyword: Optional[str] = None, 
        language: Optional[str] = None,
        region_code: Optional[str] = None,
        max_results: int = 20
    ) -> GooglePlacesResponse:
        """
        Call Google Places Nearby Search API v1 and return Python object.
        
        Args:
            location: Latitude,longitude or place_id to search near.
            radius: Search radius in meters (max 50000).
            place_type: Optional place type filter (e.g., 'restaurant', 'tourist_attraction').
            keyword: Optional keyword to search for (not supported in v1, will be ignored).
            language: Optional language code for results.
            region_code: Optional region code to bias results.
            max_results: Maximum number of results to return (1-20).
            
        Returns:
            GooglePlacesResponse object with Google's built-in place data.
        """
        endpoint = "https://places.googleapis.com/v1/places:searchNearby"
        
        # Parse location - can be "lat,lng" or place_id
        if "," in location:
            # Assume it's "lat,lng" format
            lat, lng = location.split(",")
            location_restriction = {
                "circle": {
                    "center": {
                        "latitude": float(lat.strip()),
                        "longitude": float(lng.strip())
                    },
                    "radius": min(float(radius), 50000.0)  # API max is 50000
                }
            }
        else:
            # Assume it's a place_id
            location_restriction = {
                "circle": {
                    "center": {
                        "placeId": location
                    },
                    "radius": min(float(radius), 50000.0)
                }
            }
        
        payload: Dict[str, Any] = {
            "locationRestriction": location_restriction,
            "maxResultCount": max(1, min(int(max_results), 20))
        }
        
        if language:
            payload["languageCode"] = language
        if region_code:
            payload["regionCode"] = region_code
        if place_type:
            payload["includedPrimaryTypes"] = [place_type]
        
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.id,"
                "places.displayName,"
                "places.formattedAddress,"
                "places.location,"
                "places.rating,"
                "places.userRatingCount,"
                "places.types,"
                "places.priceLevel"
            ),
            "Content-Type": "application/json",
        }
        
        response_data = self._post(endpoint, data=payload, headers=headers)
        
        # Return response using Google's built-in models
        return GooglePlacesResponse.from_google_response(response_data)

    def geocode(self, address: str, language: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Call Google Geocoding API to convert addresses to coordinates and vice versa.
        
        Args:
            address: The address to geocode (e.g., "Tokyo", "1600 Amphitheatre Parkway, Mountain View, CA").
            language: Optional language code for results.
            region: Optional region code to bias results (e.g., "us", "uk").
            
        Returns:
            Dict with Google's built-in geocoding data.
        """
        endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            "address": address,
            "key": self.api_key
        }
        
        if language:
            params["language"] = language
        if region:
            params["region"] = region
        
        response_data = self._get(endpoint, params=params)
        
        # Return Google's built-in geocoding response directly
        return response_data


# Convenience functions for backward compatibility
_google_api = GoogleAPI()

def google_places_search_text(query: str, *, max_results: int = 10, language_code: Optional[str] = None) -> GooglePlacesResponse:
    """Convenience function for places text search"""
    return _google_api.places_search_text(query, max_results=max_results, language_code=language_code)

def google_places_nearby_search(location: str, radius: int = 1000, place_type: Optional[str] = None, keyword: Optional[str] = None, language: Optional[str] = None, region_code: Optional[str] = None, max_results: int = 20) -> GooglePlacesResponse:
    """Convenience function for places nearby search"""
    return _google_api.places_nearby_search(location, radius, place_type, keyword, language, region_code, max_results)

def google_geocode(address: str, language: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for geocoding"""
    return _google_api.geocode(address, language, region)
