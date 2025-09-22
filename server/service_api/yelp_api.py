"""
Yelp API client using base API infrastructure with comprehensive caching
"""

from typing import Optional, Dict, Any, List
from cache.mongo_cache_decorator import mongo_cached
from .base_api import BaseAPI
from models.yelp_model import YelpPointOfInterest



def cache_key_generator(*args, **kwargs):
    """Generate a cache key from function arguments, excluding self object"""
    # Convert all arguments to strings and join them
    key_parts = []
    
    # Add positional arguments (skip first argument if it's a YelpAPI instance)
    for i, arg in enumerate(args):
        # Skip the first argument if it's a YelpAPI instance (self)
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


# Global flag to control cache logging
CACHE_LOGGING_ENABLED = True

def enable_cache_logging():
    """Enable cache hit/miss logging"""
    global CACHE_LOGGING_ENABLED
    CACHE_LOGGING_ENABLED = True
    print("🔊 Cache logging enabled")

def disable_cache_logging():
    """Disable cache hit/miss logging"""
    global CACHE_LOGGING_ENABLED
    CACHE_LOGGING_ENABLED = False
    print("🔇 Cache logging disabled")

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
                    if CACHE_LOGGING_ENABLED:
                        print(f"🚀 CACHE HIT for {func.__name__}: {cache_key[:100]}...")
                    
                    # If cached result is an exception, re-raise it
                    if isinstance(cached_result, Exception):
                        raise cached_result
                    return cached_result
                else:
                    if CACHE_LOGGING_ENABLED:
                        print(f"💾 CACHE MISS for {func.__name__}: {cache_key[:100] if cache_key else 'N/A'}...")
                    
                    try:
                        result = await func(*args, **kwargs)
                        cache[cache_key] = result
                        if CACHE_LOGGING_ENABLED:
                            print(f"✅ Cached successful result for {func.__name__}")
                        return result
                    except Exception as e:
                        # Cache the exception to avoid repeated failed requests
                        cache[cache_key] = e
                        if CACHE_LOGGING_ENABLED:
                            print(f"❌ Cached failed result for {func.__name__}: {type(e).__name__}")
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
                    if CACHE_LOGGING_ENABLED:
                        print(f"🚀 CACHE HIT for {func.__name__}: {cache_key[:100]}...")
                    
                    # If cached result is an exception, re-raise it
                    if isinstance(cached_result, Exception):
                        raise cached_result
                    return cached_result
                else:
                    if CACHE_LOGGING_ENABLED:
                        print(f"💾 CACHE MISS for {func.__name__}: {cache_key[:100] if cache_key else 'N/A'}...")
                    
                    try:
                        result = func(*args, **kwargs)
                        cache[cache_key] = result
                        if CACHE_LOGGING_ENABLED:
                            print(f"✅ Cached successful result for {func.__name__}")
                        return result
                    except Exception as e:
                        # Cache the exception to avoid repeated failed requests
                        cache[cache_key] = e
                        if CACHE_LOGGING_ENABLED:
                            print(f"❌ Cached failed result for {func.__name__}: {type(e).__name__}")
                        raise e
            
            return sync_wrapper
    
    return decorator


class YelpAPI(BaseAPI):
    """Yelp API client for business search and details with comprehensive caching"""
    
    def __init__(self):
        super().__init__("YELP_API_KEY")
        self.base_url = "https://api.yelp.com/v3"
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """Parse response based on API type - implemented by specific methods"""
        return response_data

    @mongo_cached("yelp_business_search")
    def business_search(
        self,
        location: str,
        *,
        term: Optional[str] = None,
        categories: Optional[List[str]] = None,
        radius: Optional[int] = None,
        price: Optional[str] = None,
        open_now: Optional[bool] = None,
        sort_by: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        attributes: Optional[List[str]] = None
    ) -> List[YelpPointOfInterest]:
        """
        Search for businesses using Yelp API
        
        Args:
            location: Location to search in (e.g., "New York, NY" or "latitude,longitude")
            term: Search term (e.g., "restaurants", "coffee")
            categories: List of categories to filter by
            radius: Search radius in meters (max 40000)
            price: Price range filter (1-4 dollar signs)
            open_now: Filter for businesses currently open
            sort_by: Sort results by (best_match, rating, review_count, distance)
            limit: Number of results to return (max 50)
            offset: Offset for pagination
            attributes: Additional attributes to filter by
            
        Returns:
            List of YelpPointOfInterest objects
        """
        endpoint = f"{self.base_url}/businesses/search"
        
        # Parse location - can be "lat,lng" or address
        if "," in location and len(location.split(",")) == 2:
            try:
                # Try to parse as coordinates
                lat, lng = location.split(",")
                float(lat.strip())
                float(lng.strip())
                location_param = f"{lat.strip()},{lng.strip()}"
            except ValueError:
                # If parsing fails, treat as address
                location_param = location
        else:
            location_param = location
        
        params = {
            "location": location_param,
            "limit": min(limit, 50)  # Yelp API max is 50
        }
        
        if term:
            params["term"] = term
        if categories:
            params["categories"] = ",".join(categories)
        if radius:
            params["radius"] = min(radius, 40000)  # Yelp API max is 40000
        if price:
            params["price"] = price
        if open_now:
            params["open_now"] = "true"
        if sort_by:
            params["sort_by"] = sort_by
        if offset:
            params["offset"] = offset
        if attributes:
            params["attributes"] = ",".join(attributes)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response_data = self._get(endpoint, params=params, headers=headers)
        
        # Convert Yelp businesses to YelpPointOfInterest objects
        yelp_businesses = []
        if 'businesses' in response_data:
            for business in response_data['businesses']:
                yelp_businesses.append(YelpPointOfInterest(**business))
        
        # Convert to dictionaries for MongoDB cache serialization
        return [business.model_dump() for business in yelp_businesses]
    
    @mongo_cached("yelp_business_matches")
    def business_matches(
        self,
        name: str,
        address1: str,
        city: str,
        state: str,
        country: str,
        *,
        address2: Optional[str] = None,
        address3: Optional[str] = None,
        postal_code: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        phone: Optional[str] = None,
        yelp_business_id: Optional[str] = None,
        limit: int = 3,
        match_threshold: str = "default"
    ) -> List[YelpPointOfInterest]:
        """
        Find businesses that match the provided business information using Yelp Business Matches API
        
        Args:
            name: The name of the business (required, max 64 chars)
            address1: The first line of the business's address (required, max 64 chars)
            city: The city of the business (required, 1-64 chars)
            state: The ISO 3166-2 state code (required, 1-3 chars)
            country: The ISO 3166-1 alpha-2 country code (required, 2 chars)
            address2: The second line of the business's address (optional, max 64 chars)
            address3: The third line of the business's address (optional, max 64 chars)
            postal_code: The ZIP code of the business (optional, max 12 chars)
            latitude: Latitude of the location (optional, -90 to 90)
            longitude: Longitude of the location (optional, -180 to 180)
            phone: The phone number of the business (optional, 1-32 chars)
            yelp_business_id: Unique Yelp identifier as a hint (optional, 22 chars)
            limit: Number of results to return (1-10, default 3)
            match_threshold: Match quality threshold (none, default, strict)
            
        Returns:
            List of YelpPointOfInterest objects
        """
        endpoint = f"{self.base_url}/businesses/matches"
        
        params = {
            "name": name,
            "address1": address1,
            "city": city,
            "state": state,
            "country": country,
            "limit": min(limit, 10),  # Yelp API max is 10
            "match_threshold": match_threshold
        }
        
        # Add optional parameters if provided
        if address2 is not None:
            params["address2"] = address2
        if address3 is not None:
            params["address3"] = address3
        if postal_code is not None:
            params["postal_code"] = postal_code
        if latitude is not None:
            params["latitude"] = latitude
        if longitude is not None:
            params["longitude"] = longitude
        if phone is not None:
            params["phone"] = phone
        if yelp_business_id is not None:
            params["yelp_business_id"] = yelp_business_id
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response_data = self._get(endpoint, params=params, headers=headers)
        
        yelp_businesses = []
        if 'businesses' in response_data:
            for business in response_data['businesses']:
                yelp_businesses.append(YelpPointOfInterest(**business))
        
        # Convert to dictionaries for MongoDB cache serialization
        return [business.model_dump() for business in yelp_businesses]
    
    @mongo_cached("yelp_business_details")
    def business_details(self, business_id: str) -> YelpPointOfInterest:
        """
        Get detailed information about a specific business
        
        Args:
            business_id: Yelp business ID
            
        Returns:
            YelpPointOfInterest object with detailed business information
        """
        endpoint = f"{self.base_url}/businesses/{business_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response_data = self._get(endpoint, headers=headers)
        
        # Convert to dictionary for MongoDB cache serialization
        return YelpPointOfInterest(**response_data).model_dump()
    
    @mongo_cached("yelp_business_reviews")
    def business_reviews(
        self, 
        business_id: str, 
        *,
        locale: Optional[str] = None,
        offset: Optional[int] = None,
        limit: int = 20,
        sort_by: str = "yelp_sort"
    ) -> Dict[str, Any]:
        """
        Get reviews for a specific business
        
        Args:
            business_id: Yelp business ID or alias
            locale: Locale code in the format of {language code}_{country code}
            offset: Offset the list of returned results by this amount (0 to 1000)
            limit: Number of reviews to return (0 to 50, defaults to 20)
            sort_by: Sort reviews by (defaults to "yelp_sort")
            
        Returns:
            Dictionary containing reviews and total count
        """
        endpoint = f"{self.base_url}/businesses/{business_id}/reviews"
        
        params = {
            "limit": min(max(limit, 0), 50)  # Clamp between 0 and 50
        }
        
        # Add optional parameters
        if locale is not None:
            params["locale"] = locale
        if offset is not None:
            params["offset"] = max(min(offset, 1000), 0)  # Clamp between 0 and 1000
        if sort_by is not None:
            params["sort_by"] = sort_by
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response_data = self._get(endpoint, params=params, headers=headers)
        
        return response_data
    
    @mongo_cached("yelp_business_search")
    async def business_search_async(
        self,
        location: str,
        *,
        term: Optional[str] = None,
        categories: Optional[List[str]] = None,
        radius: Optional[int] = None,
        price: Optional[str] = None,
        open_now: Optional[bool] = None,
        sort_by: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        attributes: Optional[List[str]] = None
    ) -> List[YelpPointOfInterest]:
        """
        Search for businesses using Yelp API asynchronously
        
        Args:
            location: Location to search in (e.g., "New York, NY" or "latitude,longitude")
            term: Search term (e.g., "restaurants", "coffee")
            categories: List of categories to filter by
            radius: Search radius in meters (max 40000)
            price: Price range filter (1-4 dollar signs)
            open_now: Filter for businesses currently open
            sort_by: Sort results by (best_match, rating, review_count, distance)
            limit: Number of results to return (max 50)
            offset: Offset for pagination
            attributes: Additional attributes to filter by
            
        Returns:
            List of YelpPointOfInterest objects
        """
        endpoint = f"{self.base_url}/businesses/search"
        
        # Parse location - can be "lat,lng" or address
        if "," in location and len(location.split(",")) == 2:
            try:
                # Try to parse as coordinates
                lat, lng = location.split(",")
                float(lat.strip())
                float(lng.strip())
                location_param = f"{lat.strip()},{lng.strip()}"
            except ValueError:
                # If parsing fails, treat as address
                location_param = location
        else:
            location_param = location
        
        params = {
            "location": location_param,
            "limit": min(limit, 50)  # Yelp API max is 50
        }
        
        if term:
            params["term"] = term
        if categories:
            params["categories"] = ",".join(categories)
        if radius:
            params["radius"] = min(radius, 40000)  # Yelp API max is 40000
        if price:
            params["price"] = price
        if open_now:
            params["open_now"] = "true"
        if sort_by:
            params["sort_by"] = sort_by
        if offset:
            params["offset"] = offset
        if attributes:
            params["attributes"] = ",".join(attributes)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response_data = await self._get_async(endpoint, params=params, headers=headers)
        
        # Convert Yelp businesses to YelpPointOfInterest objects
        yelp_businesses = []
        if 'businesses' in response_data:
            for business in response_data['businesses']:
                yelp_businesses.append(YelpPointOfInterest(**business))
        
        # Convert to dictionaries for MongoDB cache serialization
        return [business.model_dump() for business in yelp_businesses]
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            cache_type: Specific cache to clear ('business_search', 'business_details', 'business_reviews').
                       If None, clears all caches.
        """
        # Note: Cache clearing is handled by the mongo_cached decorator
        print(f"Cache clearing requested for: {cache_type or 'all'}")
    
    def get_cache_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about cache usage.
        
        Returns:
            Dict with cache statistics for each cache type.
        """
        # Note: Cache info is handled by the mongo_cached decorator
        return {"message": "Cache info handled by mongo_cached decorator"}


# Convenience functions for backward compatibility
_yelp_api = YelpAPI()

def yelp_business_search(location: str, *, term: Optional[str] = None, categories: Optional[List[str]] = None, 
                        radius: Optional[int] = None, limit: int = 20) -> List[YelpPointOfInterest]:
    """Convenience function for Yelp business search"""
    response = _yelp_api.business_search(location, term=term, categories=categories, radius=radius, limit=limit)
    
    # Convert dictionary responses (from cache) back to YelpPointOfInterest objects
    if isinstance(response, list):
        yelp_businesses = []
        for business_dict in response:
            if isinstance(business_dict, dict):
                yelp_businesses.append(YelpPointOfInterest.model_validate(business_dict))
            else:
                yelp_businesses.append(business_dict)  # Already a YelpPointOfInterest object
        return yelp_businesses
    elif isinstance(response, dict):
        # Handle cached dictionary response with numeric keys
        yelp_businesses = []
        for key in sorted(response.keys()):
            business_dict = response[key]
            if isinstance(business_dict, dict):
                yelp_businesses.append(YelpPointOfInterest.model_validate(business_dict))
            else:
                yelp_businesses.append(business_dict)  # Already a YelpPointOfInterest object
        return yelp_businesses
    else:
        return response

async def yelp_business_search_async(location: str, *, term: Optional[str] = None, categories: Optional[List[str]] = None, 
                                    radius: Optional[int] = None, limit: int = 20) -> List[YelpPointOfInterest]:
    """Convenience function for async Yelp business search"""
    response = await _yelp_api.business_search_async(location, term=term, categories=categories, radius=radius, limit=limit)
    
    # Convert dictionary responses (from cache) back to YelpPointOfInterest objects
    if isinstance(response, list):
        yelp_businesses = []
        for business_dict in response:
            if isinstance(business_dict, dict):
                yelp_businesses.append(YelpPointOfInterest.model_validate(business_dict))
            else:
                yelp_businesses.append(business_dict)  # Already a YelpPointOfInterest object
        return yelp_businesses
    elif isinstance(response, dict):
        # Handle cached dictionary response with numeric keys
        yelp_businesses = []
        for key in sorted(response.keys()):
            business_dict = response[key]
            if isinstance(business_dict, dict):
                yelp_businesses.append(YelpPointOfInterest.model_validate(business_dict))
            else:
                yelp_businesses.append(business_dict)  # Already a YelpPointOfInterest object
        return yelp_businesses
    else:
        return response

def yelp_business_details(business_id: str) -> YelpPointOfInterest:
    """Convenience function for Yelp business details"""
    response = _yelp_api.business_details(business_id)
    
    # Convert dictionary response (from cache) back to YelpPointOfInterest object
    if isinstance(response, dict):
        return YelpPointOfInterest.model_validate(response)
    else:
        return response

def yelp_business_reviews(
    business_id: str, 
    *,
    locale: Optional[str] = None,
    offset: Optional[int] = None,
    limit: int = 20,
    sort_by: str = "yelp_sort"
) -> Dict[str, Any]:
    """Convenience function for Yelp business reviews"""
    return _yelp_api.business_reviews(
        business_id, 
        locale=locale, 
        offset=offset, 
        limit=limit, 
        sort_by=sort_by
    )


# Cache management convenience functions
def clear_yelp_api_cache(cache_type: Optional[str] = None):
    """Clear Yelp API cache entries"""
    _yelp_api.clear_cache(cache_type)

def yelp_business_matches(
    name: str,
    address1: str,
    city: str,
    state: str,
    country: str,
    *,
    address2: Optional[str] = None,
    address3: Optional[str] = None,
    postal_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    phone: Optional[str] = None,
    yelp_business_id: Optional[str] = None,
    limit: int = 3,
    match_threshold: str = "default"
) -> List[YelpPointOfInterest]:
    """Convenience function for Yelp business matches"""
    response = _yelp_api.business_matches(
        name=name,
        address1=address1,
        city=city,
        state=state,
        country=country,
        address2=address2,
        address3=address3,
        postal_code=postal_code,
        latitude=latitude,
        longitude=longitude,
        phone=phone,
        yelp_business_id=yelp_business_id,
        limit=limit,
        match_threshold=match_threshold
    )
    
    # Convert dictionary responses (from cache) back to YelpPointOfInterest objects
    if isinstance(response, list):
        yelp_businesses = []
        for business_dict in response:
            if isinstance(business_dict, dict):
                yelp_businesses.append(YelpPointOfInterest.model_validate(business_dict))
            else:
                yelp_businesses.append(business_dict)  # Already a YelpPointOfInterest object
        return yelp_businesses
    elif isinstance(response, dict):
        # Handle cached dictionary response with numeric keys
        yelp_businesses = []
        for key in sorted(response.keys()):
            business_dict = response[key]
            if isinstance(business_dict, dict):
                yelp_businesses.append(YelpPointOfInterest.model_validate(business_dict))
            else:
                yelp_businesses.append(business_dict)  # Already a YelpPointOfInterest object
        return yelp_businesses
    else:
        return response

def get_yelp_api_cache_info() -> Dict[str, Dict[str, Any]]:
    """Get Yelp API cache information"""
    return _yelp_api.get_cache_info()

# Cache logging convenience functions
def enable_yelp_api_cache_logging():
    """Enable cache hit/miss logging for Yelp API calls"""
    enable_cache_logging()

def disable_yelp_api_cache_logging():
    """Disable cache hit/miss logging for Yelp API calls"""
    disable_cache_logging()
