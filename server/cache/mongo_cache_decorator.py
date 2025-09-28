"""
MongoDB cache decorator for API client methods
"""

import functools
import inspect
from typing import Callable, Any, Optional
from .mongo_db_cache import get_mongo_cache


def mongo_cached(cache_type: str):
    """
    Decorator to cache API method results in MongoDB
    
    Args:
        cache_type: Type of cache (e.g., 'google_places_search', 'yelp_business_search', 'foursquare_venue_search')
    
    Usage:
        @mongo_cached('google_places_search')
        def places_search(self, query: str, location: str, **kwargs):
            # API call implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if it's an async function (handle separately)
            if inspect.iscoroutinefunction(func):
                return func(*args, **kwargs)
            
            cache = get_mongo_cache()
            
            # Generate cache key from function arguments (exclude self for instance methods)
            cache_key_args = args[1:] if args and hasattr(args[0], '__class__') else args
            cache_key_kwargs = kwargs
            
            # Check cache first
            cached_result = cache.get(cache_type, *cache_key_args, **cache_key_kwargs)
            if cached_result is not None:
                print(f"🚀 MongoDB CACHE HIT for {func.__name__}: {cache_type}")
                # Deserialize GooglePlacesResponse if needed
                if cache_type == 'google_places_search' and isinstance(cached_result, dict):
                    from models.google_map_models import GooglePlacesResponse
                    return GooglePlacesResponse.from_dict(cached_result)
                return cached_result
            
            print(f"💾 MongoDB CACHE MISS for {func.__name__}: {cache_type}")
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                
                # Cache successful results
                if result is not None:
                    # Convert result to dict if it's a Pydantic model
                    if hasattr(result, 'to_dict'):
                        cache_data = result.to_dict()
                    elif hasattr(result, 'dict'):
                        cache_data = result.dict()
                    elif hasattr(result, '__dict__'):
                        cache_data = result.__dict__
                    else:
                        cache_data = result
                    
                    cache.set(cache_type, cache_data, *cache_key_args, **cache_key_kwargs)
                    print(f"✅ Cached successful result for {func.__name__}: {cache_type}")
                
                return result
                
            except Exception as e:
                print(f"❌ Failed to execute {func.__name__}: {type(e).__name__}")
                raise e
        
        return wrapper
    return decorator


def mongo_cached_async(cache_type: str):
    """
    Decorator to cache async API method results in MongoDB
    
    Args:
        cache_type: Type of cache (e.g., 'google_places_search', 'yelp_business_search', 'foursquare_venue_search')
    
    Usage:
        @mongo_cached_async('google_places_search')
        async def places_search_async(self, query: str, location: str, **kwargs):
            # API call implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_mongo_cache()
            
            # Generate cache key from function arguments (exclude self for instance methods)
            cache_key_args = args[1:] if args and hasattr(args[0], '__class__') else args
            cache_key_kwargs = kwargs
            
            # Check cache first
            cached_result = cache.get(cache_type, *cache_key_args, **cache_key_kwargs)
            if cached_result is not None:
                print(f"🚀 MongoDB CACHE HIT for {func.__name__}: {cache_type}")
                # Deserialize GooglePlacesResponse if needed
                if cache_type == 'google_places_search' and isinstance(cached_result, dict):
                    from models.google_map_models import GooglePlacesResponse
                    return GooglePlacesResponse.from_dict(cached_result)
                return cached_result
            
            print(f"💾 MongoDB CACHE MISS for {func.__name__}: {cache_type}")
            
            # Execute function and cache result
            try:
                result = await func(*args, **kwargs)
                
                # Cache successful results
                if result is not None:
                    # Convert result to dict if it's a Pydantic model
                    if hasattr(result, 'to_dict'):
                        cache_data = result.to_dict()
                    elif hasattr(result, 'dict'):
                        cache_data = result.dict()
                    elif hasattr(result, '__dict__'):
                        cache_data = result.__dict__
                    else:
                        cache_data = result
                    
                    cache.set(cache_type, cache_data, *cache_key_args, **cache_key_kwargs)
                    print(f"✅ Cached successful result for {func.__name__}: {cache_type}")
                
                return result
                
            except Exception as e:
                print(f"❌ Failed to execute {func.__name__}: {type(e).__name__}")
                raise e
        
        return wrapper
    return decorator


