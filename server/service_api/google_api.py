"""
Google API client using base API infrastructure with comprehensive caching
"""

import logging
from typing import Optional, Dict, Any, List
from cache.mongo_cache_decorator import mongo_cached, mongo_cached_async
from .base_api import BaseAPI
from models.google_map_models import (
    GooglePlacesRequest,
    GooglePlacesResponse,
    GooglePlacesFieldMasks
)

logger = logging.getLogger(__name__)


# MongoDB cache configuration - handled by decorators


def cache_key_generator(*args, **kwargs):
    """Generate a cache key from function arguments, excluding self object"""
    # Convert all arguments to strings and join them
    key_parts = []
    
    # Add positional arguments (skip first argument if it's self)
    for i, arg in enumerate(args):
        # Skip the first argument if it's a GoogleAPI instance (self)
        if i == 0 and hasattr(arg, 'api_key') and hasattr(arg, 'timeout'):
            continue
            
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, dict):
            # Sort dict items for consistent keys
            sorted_items = sorted(arg.items()) if arg else []
            key_parts.append(str(sorted_items))
        elif isinstance(arg, list):
            key_parts.append(str(sorted(arg) if arg else []))
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for key, value in sorted(kwargs.items()):
        if value is not None:  # Skip None values to avoid cache misses
            key_parts.append(f"{key}={value}")
    
    return "|".join(key_parts)


def cached_with_logging(cache, key=None):
    """Custom cache decorator that logs cache hits and misses, caches both successful and failed responses"""
    def decorator(func):
        import inspect
        
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            # Async version - manual caching to handle exceptions
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = key(*args, **kwargs) if key else None
                
                # Check if in cache
                if cache_key in cache:
                    cached_result = cache[cache_key]
                    
                    # If cached result is an exception, re-raise it
                    if isinstance(cached_result, Exception):
                        raise cached_result
                    return cached_result
                else:
                    
                    try:
                        result = await func(*args, **kwargs)
                        cache[cache_key] = result
                        logger.debug(f"✅ Cached successful result for {func.__name__}")
                        return result
                    except Exception as e:
                        # Cache the exception to avoid repeated failed requests
                        cache[cache_key] = e
                        logger.debug(f"❌ Cached failed result for {func.__name__}: {type(e).__name__}")
                        raise e
            
            return async_wrapper
        else:
            # Sync version - manual caching to handle exceptions
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = key(*args, **kwargs) if key else None
                
                # Check if in cache
                if cache_key in cache:
                    cached_result = cache[cache_key]
                    logger.debug(f"🚀 CACHE HIT for {func.__name__}: {cache_key[:100]}...")
                    
                    # If cached result is an exception, re-raise it
                    if isinstance(cached_result, Exception):
                        raise cached_result
                    return cached_result
                else:
                    logger.debug(f"💾 CACHE MISS for {func.__name__}: {cache_key[:100] if cache_key else 'N/A'}...")
                    
                    try:
                        result = func(*args, **kwargs)
                        cache[cache_key] = result
                        logger.debug(f"✅ Cached successful result for {func.__name__}")
                        return result
                    except Exception as e:
                        # Cache the exception to avoid repeated failed requests
                        cache[cache_key] = e
                        logger.debug(f"❌ Cached failed result for {func.__name__}: {type(e).__name__}")
                        raise e
            
            return sync_wrapper
    
    return decorator


class GoogleAPI(BaseAPI):
    """Google API client for Places and Geocoding services with comprehensive caching"""
    
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
    
    def _get_headers(self, field_mask: str) -> Dict[str, str]:
        """
        Generate standard headers for Google Places API requests.
        
        Args:
            field_mask: The field mask for the API request
            
        Returns:
            Dictionary of headers
        """
        return {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
            "Content-Type": "application/json",
        }
    
    @mongo_cached("google_places_search")
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

        headers = self._get_headers(GooglePlacesFieldMasks.TEXT_SEARCH_ESSENTIAL)

        # Make request using Google's built-in TextSearchRequest format
        response_data = self._post(endpoint, data=request.to_google_request(), headers=headers)
        
        # Return response using Google's built-in TextSearchResponse format
        return GooglePlacesResponse.from_google_response(response_data)

    @mongo_cached("google_places_nearby")
    def places_nearby_search(
        self, 
        location: str, 
        radius: int = 1000, 
        place_types: Optional[List[str]] = None, 
        language: Optional[str] = None,
        region_code: Optional[str] = None,
        max_results: int = 20
    ) -> GooglePlacesResponse:
        """
        Call Google Places Nearby Search API v1 and return Python object.
        
        Args:
            location: Latitude,longitude or place_id to search near.
            radius: Search radius in meters (max 50000).
            place_types: Optional list of place types to include (e.g., ['restaurant', 'tourist_attraction']).
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
        if place_types:
            payload["includedTypes"] = place_types
        
        headers = self._get_headers(GooglePlacesFieldMasks.NEARBY_SEARCH_PRO)
        
        response_data = self._post(endpoint, data=payload, headers=headers)
        
        # Return response using Google's built-in models
        return GooglePlacesResponse.from_google_response(response_data)
    
    @mongo_cached_async("google_places_nearby")
    async def places_nearby_search_async(
        self, 
        location: str, 
        radius: int = 1000, 
        place_types: Optional[List[str]] = None, 
        *,
        field_mask: Optional[str] = GooglePlacesFieldMasks.NEARBY_SEARCH_PRO,
        language: Optional[str] = None,
        region_code: Optional[str] = None,
        max_results: int = 20
    ) -> GooglePlacesResponse:
        """
        Call Google Places Nearby Search API v1 asynchronously and return Python object.
        
        Args:
            location: Latitude,longitude or place_id to search near.
            radius: Search radius in meters (max 50000).
            place_types: Optional list of place types to include (e.g., ['restaurant', 'tourist_attraction']).
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
        if place_types:
            payload["includedTypes"] = place_types
        
        headers = self._get_headers(field_mask)
        
        response_data = await self._post_async(endpoint, data=payload, headers=headers)
        
        # Return response using Google's built-in models
        return GooglePlacesResponse.from_google_response(response_data)

    @mongo_cached("google_geocoding")
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

    @mongo_cached("google_place_details")
    def google_place_details(
        self,
        place_id: str,
        *,
        field_mask: Optional[str] = GooglePlacesFieldMasks.PLACE_DETAILS_ESSENTIAL,
        language_code: Optional[str] = None,
        region_code: Optional[str] = None
    ):
        """
        Call Google Places Place Details API v1 to get detailed information about a specific place.
        
        Args:
            place_id: The unique identifier for the place (e.g., "ChIJN1t_tDeuEmsRUsoyG83frY4").
            language_code: Optional BCP-47 language code for results.
            region_code: Optional region code to bias results.
            
        Returns:
            GooglePlace object with detailed place information from Google Places API.
        """
        from models.google_map_models import GooglePlace
        
        endpoint = f"https://places.googleapis.com/v1/places/{place_id}"
        
        # Build query parameters
        params = {}
        if language_code:
            params["languageCode"] = language_code
        if region_code:
            params["regionCode"] = region_code
        
        # Use ESSENTIAL tier for Place Details (basic address fields only)
        # Note: Place Details API uses field names WITHOUT "places." prefix
        field_mask = field_mask
        
        headers = self._get_headers(field_mask)
        
        try:
            # Make GET request to Place Details endpoint
            response_data = self._get(endpoint, params=params, headers=headers)
            
            # Convert to GooglePlace object using model_validate (handles nested structure automatically)
            return GooglePlace.model_validate(response_data)
            
        except Exception as e:
            # Add better error handling and debugging
            logger.error(f"Error calling Google Places Details API for place_id: {place_id}")
            logger.error(f"Endpoint: {endpoint}")
            logger.error(f"Field mask: {field_mask}")
            logger.error(f"Error: {str(e)}")
            raise e
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear MongoDB cache entries.
        
        Args:
            cache_type: Specific cache to clear (e.g., 'google_places_search', 'google_place_details').
                       If None, clears all Google API caches.
        """
        from cache.mongo_db_cache import get_mongo_cache
        cache = get_mongo_cache()
        
        if cache_type:
            if hasattr(cache, 'collections') and cache_type in cache.collections:
                cache.collections[cache_type].delete_many({})
        else:
            # Clear all Google-related caches
            google_cache_types = [
                'google_places_search',
                'google_places_nearby',
                'google_geocoding',
                'google_place_details'
            ]
            for cache_name in google_cache_types:
                if hasattr(cache, 'collections') and cache_name in cache.collections:
                    cache.collections[cache_name].delete_many({})
    
    def get_cache_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about MongoDB cache usage.
        
        Returns:
            Dict with cache statistics for each cache type.
        """
        from cache.mongo_db_cache import get_mongo_cache
        cache = get_mongo_cache()
        
        cache_info = {}
        google_cache_types = [
            'google_places_search',
            'google_places_nearby',
            'google_geocoding',
            'google_place_details'
        ]
        
        for cache_name in google_cache_types:
            if hasattr(cache, 'collections') and cache_name in cache.collections:
                collection = cache.collections[cache_name]
                total = collection.count_documents({})
                cache_info[cache_name] = {
                    'total_entries': total,
                    'backend': 'mongodb',
                    'ttl_days': 30
                }
        
        return cache_info



# Convenience functions for backward compatibility
_google_api = GoogleAPI()

def google_places_search_text(query: str, *, max_results: int = 10, language_code: Optional[str] = None) -> GooglePlacesResponse:
    """Convenience function for places text search"""
    response = _google_api.places_search_text(query, max_results=max_results, language_code=language_code)
    
    # Handle both object and dictionary responses (from cache)
    if isinstance(response, dict):
        return GooglePlacesResponse.from_google_response(response)
    else:
        return response

def google_places_nearby_search(location: str, radius: int = 1000, place_types: Optional[List[str]] = None, language: Optional[str] = None, region_code: Optional[str] = None, max_results: int = 20) -> GooglePlacesResponse:
    """Convenience function for places nearby search"""
    response = _google_api.places_nearby_search(
        location, 
        radius, 
        place_types, 
        language=language, 
        region_code=region_code, 
        max_results=max_results
    )
    
    # Handle both object and dictionary responses (from cache)
    if isinstance(response, dict):
        return GooglePlacesResponse.from_google_response(response)
    else:
        return response

async def google_places_nearby_search_async(location: str, radius: int = 1000, place_types: Optional[List[str]] = None, language: Optional[str] = None, region_code: Optional[str] = None, max_results: int = 20) -> GooglePlacesResponse:
    """Convenience function for async places nearby search"""
    response = await _google_api.places_nearby_search_async(
        location, 
        radius, 
        place_types, 
        language=language, 
        region_code=region_code, 
        max_results=max_results
    )
    
    # Handle both object and dictionary responses (from cache)
    if isinstance(response, dict):
        return GooglePlacesResponse.from_google_response(response)
    else:
        return response

def google_geocode(address: str, language: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for geocoding"""
    return _google_api.geocode(address, language, region)

def google_place_details(place_id: str, *, language_code: Optional[str] = None, region_code: Optional[str] = None):
    """Convenience function for place details - returns GooglePlace object"""
    return _google_api.google_place_details(place_id, language_code=language_code, region_code=region_code)


# Cache management convenience functions
def clear_google_api_cache(cache_type: Optional[str] = None):
    """Clear Google API cache entries"""
    _google_api.clear_cache(cache_type)


def get_google_api_cache_info() -> Dict[str, Dict[str, Any]]:
    """Get Google API cache information"""
    return _google_api.get_cache_info()


