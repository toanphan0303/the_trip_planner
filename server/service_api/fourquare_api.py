"""
Foursquare API client using base API infrastructure with comprehensive caching
"""

from typing import Optional, Dict, Any, List
from cache.mongo_cache_decorator import mongo_cached
from .base_api import BaseAPI
from models.point_of_interest_models import PointOfInterest, Location, POIType, Source
# from models.foursquare_model import FoursquareSearchResponse, FoursquareVenueDetailResponse



def cache_key_generator(*args, **kwargs):
    """Generate a cache key from function arguments, excluding self object"""
    # Convert all arguments to strings and join them
    key_parts = []
    
    # Add positional arguments (skip first argument if it's a FoursquareAPI instance)
    for i, arg in enumerate(args):
        # Skip the first argument if it's a FoursquareAPI instance (self)
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


class FoursquareAPI(BaseAPI):
    """Foursquare API client for venue search and details with comprehensive caching"""
    
    def __init__(self):
        super().__init__("FOURSQUARE_API_KEY")
        self.base_url = "https://places-api.foursquare.com"
        self.version = "2025-06-17"  # API version date (YYYY-MM-DD)
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """Parse response based on API type - implemented by specific methods"""
        return response_data
    
    def _convert_foursquare_venue_to_poi(self, venue: Dict[str, Any]) -> PointOfInterest:
        """
        Convert Foursquare venue data to PointOfInterest model using the new Foursquare models
        
        Args:
            venue: Foursquare venue data from API
            
        Returns:
            PointOfInterest object with Foursquare data
        """
        # Convert Foursquare venue to PointOfInterest
        # This is a placeholder implementation - you may need to adjust based on your needs
        return PointOfInterest(
            id=venue.get('id', ''),
            name=venue.get('name', ''),
            type=POIType.place,
            category='restaurant',  # Default category
            description=venue.get('description', ''),
            address=venue.get('location', {}).get('formattedAddress', ''),
            location=Location(
                latitude=venue.get('location', {}).get('lat', 0.0),
                longitude=venue.get('location', {}).get('lng', 0.0)
            ),
            rating=venue.get('rating', 0.0),
            user_rating_count=venue.get('stats', {}).get('totalCheckins', 0),
            source=Source.foursquare,
            raw_data=venue
        )
    
    @mongo_cached("foursquare_venue_search")
    def venue_search(
        self,
        query: str,
        *,
        ll: Optional[str] = None,  # latitude,longitude
        near: Optional[str] = None,  # near location
        radius: Optional[int] = None,  # radius in meters
        categories: Optional[List[str]] = None,  # category IDs
        price: Optional[List[int]] = None,  # price levels 1-4
        open_now: Optional[bool] = None,
        sort: Optional[str] = None,  # DISTANCE, POPULARITY, RATING
        limit: int = 20,
        offset: int = 0
    ) -> List[PointOfInterest]:
        """
        Search for venues using Foursquare API
        
        Args:
            query: Search query (e.g., "coffee", "restaurants")
            ll: Latitude and longitude (e.g., "37.7749,-122.4194")
            near: Location to search near (e.g., "San Francisco, CA")
            radius: Search radius in meters (max 100000)
            categories: List of category IDs to filter by
            price: List of price levels to filter by (1-4)
            open_now: Filter for venues currently open
            sort: Sort results by (DISTANCE, POPULARITY, RATING)
            limit: Number of results to return (max 50)
            offset: Offset for pagination
            
        Returns:
            PointOfInterestSearchResult with Foursquare venues
        """
        endpoint = f"{self.base_url}/places/search"
        
        params = {
            "query": query,
            "limit": min(limit, 50),  # Foursquare API max is 50
        }
        
        if ll:
            params["ll"] = ll
        if near:
            params["near"] = near
        if radius:
            params["radius"] = min(radius, 100000)  # Foursquare API max is 100000
        if categories:
            params["categories"] = ",".join(categories)
        if price:
            params["price"] = ",".join(map(str, price))
        if open_now:
            params["open_now"] = "true"
        if sort:
            params["sort"] = sort
        if offset:
            params["offset"] = offset
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "X-Places-Api-Version": self.version,
        }
        
        response_data = self._get(endpoint, params=params, headers=headers)
        
        # Convert Foursquare venues to PointOfInterest objects
        poi_items = []
        if 'results' in response_data:
            for venue in response_data['results']:
                poi_items.append(self._convert_foursquare_venue_to_poi(venue))
        
        # Create search center location if possible
        search_center = None
        if ll and "," in ll:
            try:
                lat, lng = ll.split(",")
                search_center = Location(latitude=float(lat.strip()), longitude=float(lng.strip()))
            except ValueError:
                pass
        
        return poi_items
    
    @mongo_cached("foursquare_venue_details")
    def venue_details(self, venue_id: str, fields: Optional[List[str]] = None) -> PointOfInterest:
        """
        Get detailed information about a specific venue
        
        Args:
            venue_id: Foursquare venue ID
            fields: List of fields to include in response
            
        Returns:
            PointOfInterest object with detailed venue information
        """
        endpoint = f"{self.base_url}/places/{venue_id}"
        
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "X-Places-Api-Version": self.version,
        }
        
        response_data = self._get(endpoint, params=params, headers=headers)
        
        return self._convert_foursquare_venue_to_poi(response_data)
    
    @mongo_cached("foursquare_places_match")
    def places_match(
        self,
        name: str,
        *,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        cc: Optional[str] = None,
        ll: Optional[str] = None,
        fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Match a place using Foursquare Places API
        
        Args:
            name: Name of the place to match (required)
            address: Street address of the place to match (e.g. 1060 W Addison St)
            city: City, or Locality, where the place is located (e.g. Chicago)
            state: State, or Region, where the place is located (e.g. Illinois)
            postal_code: The postal code for the address where the place is located (e.g. 60613)
            cc: The 2-digit country code where the place is located (e.g. US)
            ll: The latitude/longitude of the venue location (e.g., ll=41.9484,-87.6553)
            fields: Indicate which fields to return in the response, separated by commas
            
        Returns:
            Dictionary containing matched place data
        """
        endpoint = f"{self.base_url}/places/match"
        
        params = {
            "name": name
        }
        
        # Add optional parameters
        if address is not None:
            params["address"] = address
        if city is not None:
            params["city"] = city
        if state is not None:
            params["state"] = state
        if postal_code is not None:
            params["postal_code"] = postal_code
        if cc is not None:
            params["cc"] = cc
        if ll is not None:
            params["ll"] = ll
        if fields is not None:
            params["fields"] = fields
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "X-Places-Api-Version": self.version,
        }
        
        response_data = self._get(endpoint, params=params, headers=headers)
        
        return response_data
    
    @mongo_cached("foursquare_venue_tips")
    def venue_tips(self, venue_id: str, limit: int = 10, sort: str = "POPULAR") -> List[Dict[str, Any]]:
        """
        Get tips for a specific venue
        
        Args:
            venue_id: Foursquare venue ID
            limit: Number of tips to return (max 50)
            sort: Sort order (NEWEST, POPULAR)
            
        Returns:
            List of tip dictionaries
        """
        endpoint = f"{self.base_url}/places/{venue_id}/tips"
        
        params = {
            "limit": min(limit, 50),  # Foursquare API max is 50
            "sort": sort,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "X-Places-Api-Version": self.version,
        }
        
        response_data = self._get(endpoint, params=params, headers=headers)
        
        # Handle both list and dict responses
        if isinstance(response_data, list):
            return response_data
        elif isinstance(response_data, dict):
            return response_data.get('results', [])
        else:
            return []
    
    @mongo_cached("foursquare_venue_search")
    async def venue_search_async(
        self,
        query: str,
        *,
        ll: Optional[str] = None,
        near: Optional[str] = None,
        radius: Optional[int] = None,
        categories: Optional[List[str]] = None,
        price: Optional[List[int]] = None,
        open_now: Optional[bool] = None,
        sort: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[PointOfInterest]:
        """
        Search for venues using Foursquare API asynchronously
        
        Args:
            query: Search query (e.g., "coffee", "restaurants")
            ll: Latitude and longitude (e.g., "37.7749,-122.4194")
            near: Location to search near (e.g., "San Francisco, CA")
            radius: Search radius in meters (max 100000)
            categories: List of category IDs to filter by
            price: List of price levels to filter by (1-4)
            open_now: Filter for venues currently open
            sort: Sort results by (DISTANCE, POPULARITY, RATING)
            limit: Number of results to return (max 50)
            offset: Offset for pagination
            
        Returns:
            PointOfInterestSearchResult with Foursquare venues
        """
        endpoint = f"{self.base_url}/places/search"
        
        params = {
            "query": query,
            "limit": min(limit, 50),  # Foursquare API max is 50
        }
        
        if ll:
            params["ll"] = ll
        if near:
            params["near"] = near
        if radius:
            params["radius"] = min(radius, 100000)  # Foursquare API max is 100000
        if categories:
            params["categories"] = ",".join(categories)
        if price:
            params["price"] = ",".join(map(str, price))
        if open_now:
            params["open_now"] = "true"
        if sort:
            params["sort"] = sort
        if offset:
            params["offset"] = offset
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "X-Places-Api-Version": self.version,
        }
        
        response_data = await self._get_async(endpoint, params=params, headers=headers)
        
        # Convert Foursquare venues to PointOfInterest objects
        poi_items = []
        if 'results' in response_data:
            for venue in response_data['results']:
                poi_items.append(self._convert_foursquare_venue_to_poi(venue))
        
        # Create search center location if possible
        search_center = None
        if ll and "," in ll:
            try:
                lat, lng = ll.split(",")
                search_center = Location(latitude=float(lat.strip()), longitude=float(lng.strip()))
            except ValueError:
                pass
        
        return poi_items
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            cache_type: Specific cache to clear ('venue_search', 'venue_details', 'venue_tips').
                       If None, clears all caches.
        """
        if cache_type:
            if cache_type in CACHE_CONFIG:
                None.clear()
                print(f"Cleared {cache_type} cache")
            else:
                print(f"Unknown cache type: {cache_type}")
        else:
            for cache_name, cache in CACHE_CONFIG.items():
                cache.clear()
            print("Cleared all caches")
    
    def get_cache_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about cache usage.
        
        Returns:
            Dict with cache statistics for each cache type.
        """
        cache_info = {}
        for cache_name, cache in CACHE_CONFIG.items():
            cache_info[cache_name] = {
                'size': len(cache),
                'maxsize': cache.maxsize,
                'ttl': cache.ttl,
                'hits': getattr(cache, 'hits', 0),
                'misses': getattr(cache, 'misses', 0)
            }
        return cache_info


# Convenience functions for backward compatibility
# Initialize Foursquare API only if API key is available
try:
    _foursquare_api = FoursquareAPI()
except ValueError:
    print("⚠️  Foursquare API key not available, Foursquare features disabled")
    _foursquare_api = None

def foursquare_venue_search(query: str, *, ll: Optional[str] = None, near: Optional[str] = None, 
                           radius: Optional[int] = None, limit: int = 20) -> List[PointOfInterest]:
    """Convenience function for Foursquare venue search"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.venue_search(query, ll=ll, near=near, radius=radius, limit=limit)

async def foursquare_venue_search_async(query: str, *, ll: Optional[str] = None, near: Optional[str] = None, 
                                       radius: Optional[int] = None, limit: int = 20) -> List[PointOfInterest]:
    """Convenience function for async Foursquare venue search"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return await _foursquare_api.venue_search_async(query, ll=ll, near=near, radius=radius, limit=limit)

def foursquare_venue_details(venue_id: str, fields: Optional[List[str]] = None) -> PointOfInterest:
    """Convenience function for Foursquare venue details"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.venue_details(venue_id, fields=fields)

def foursquare_venue_tips(venue_id: str, limit: int = 10, sort: str = "POPULAR") -> List[Dict[str, Any]]:
    """Convenience function for Foursquare venue tips"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.venue_tips(venue_id, limit=limit, sort=sort)

def foursquare_places_match(
    name: str,
    *,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    cc: Optional[str] = None,
    ll: Optional[str] = None,
    fields: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for Foursquare places match"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.places_match(
        name,
        address=address,
        city=city,
        state=state,
        postal_code=postal_code,
        cc=cc,
        ll=ll,
        fields=fields
    )


def foursquare_places_match_with_request(request: 'FoursquarePlacesMatchRequest') -> Dict[str, Any]:
    """Convenience function for Foursquare places match using request model"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.places_match(**request.to_params())


def foursquare_venue_search_with_request(request: 'FoursquareVenueSearchRequest') -> List[PointOfInterest]:
    """Convenience function for Foursquare venue search using request model"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.venue_search(**request.to_params())


def foursquare_venue_details_with_request(request: 'FoursquareVenueDetailsRequest') -> Dict[str, Any]:
    """Convenience function for Foursquare venue details using request model"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.venue_details(request.venue_id, **request.to_params())


def foursquare_venue_tips_with_request(request: 'FoursquareVenueTipsRequest') -> List[Dict[str, Any]]:
    """Convenience function for Foursquare venue tips using request model"""
    if _foursquare_api is None:
        raise ValueError("Foursquare API not available - API key not set")
    return _foursquare_api.venue_tips(request.venue_id, **request.to_params())


# Cache management convenience functions
def clear_foursquare_api_cache(cache_type: Optional[str] = None):
    """Clear Foursquare API cache entries"""
    if _foursquare_api is None:
        return
    _foursquare_api.clear_cache(cache_type)

def get_foursquare_api_cache_info() -> Dict[str, Dict[str, Any]]:
    """Get Foursquare API cache information"""
    if _foursquare_api is None:
        return {}
    return _foursquare_api.get_cache_info()

# Cache logging convenience functions
def enable_foursquare_api_cache_logging():
    """Enable cache hit/miss logging for Foursquare API calls"""
    enable_cache_logging()

def disable_foursquare_api_cache_logging():
    """Disable cache hit/miss logging for Foursquare API calls"""
    disable_cache_logging()