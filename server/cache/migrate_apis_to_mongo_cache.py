"""
Migration script to replace TTLCache with MongoDB cache in all API services
"""

import os
import sys
from typing import Dict, Any

# Add the server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cache.mongo_cache_decorator import mongo_cached
from cache.mongo_db_cache import get_mongo_cache


def migrate_google_api():
    """Migrate Google API from TTLCache to MongoDB cache"""
    
    print("🔄 Migrating Google API to MongoDB cache...")
    
    # Read the current Google API file
    google_api_path = os.path.join(os.path.dirname(__file__), '..', 'service_api', 'google_api.py')
    
    with open(google_api_path, 'r') as f:
        content = f.read()
    
    # Replace TTLCache imports and configuration
    new_content = content.replace(
        'from cachetools import TTLCache',
        'from cache.mongo_cache_decorator import mongo_cached'
    )
    
    # Remove TTLCache configuration
    new_content = new_content.replace(
        """# Cache configuration with different TTL values for different API types
CACHE_CONFIG = {
    # Places search results - cache for 7 days (604800 seconds) - places don't change often
    'places_search': TTLCache(maxsize=1000, ttl=604800),
    
    # Nearby search results - cache for 7 days (604800 seconds) - business locations are stable
    'places_nearby': TTLCache(maxsize=2000, ttl=604800),
    
    # Geocoding results - cache for 7 days (604800 seconds) - addresses rarely change
    'geocoding': TTLCache(maxsize=5000, ttl=604800),
    
    # Place details - cache for 7 days (604800 seconds) - place info is relatively stable
    'place_details': TTLCache(maxsize=2000, ttl=604800),
}""",
        """# MongoDB cache configuration - handled by decorators"""
    )
    
    # Add MongoDB cache decorators to methods
    methods_to_decorate = [
        ('def places_search_text', 'google_places_search'),
        ('def places_nearby_search', 'google_places_nearby'),
        ('def geocode', 'google_geocoding'),
        ('def place_details', 'google_place_details')
    ]
    
    for method_def, cache_type in methods_to_decorate:
        if method_def in new_content:
            new_content = new_content.replace(
                method_def,
                f'@mongo_cached("{cache_type}")\n    {method_def}'
            )
    
    # Remove cache-related code from methods
    new_content = new_content.replace(
        'cache_key = cache_key_generator(*args, **kwargs)\n        \n        # Check cache first\n        if cache_key in self._cache[',
        '# Cache handled by MongoDB decorator\n        # '
    )
    
    new_content = new_content.replace(
        'self._cache[',
        '# self._cache['
    )
    
    # Write the updated content
    with open(google_api_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Google API migrated to MongoDB cache")


def migrate_yelp_api():
    """Migrate Yelp API from TTLCache to MongoDB cache"""
    
    print("🔄 Migrating Yelp API to MongoDB cache...")
    
    yelp_api_path = os.path.join(os.path.dirname(__file__), '..', 'service_api', 'yelp_api.py')
    
    with open(yelp_api_path, 'r') as f:
        content = f.read()
    
    # Replace TTLCache imports and configuration
    new_content = content.replace(
        'from cachetools import TTLCache',
        'from cache.mongo_cache_decorator import mongo_cached'
    )
    
    # Remove TTLCache configuration
    new_content = new_content.replace(
        """# Cache configuration with different TTL values for different API types
CACHE_CONFIG = {
    # Business search results - cache for 7 days (604800 seconds) - businesses don't change often
    'business_search': TTLCache(maxsize=1000, ttl=604800),
    
    # Business details - cache for 7 days (604800 seconds) - business info is relatively stable
    'business_details': TTLCache(maxsize=2000, ttl=604800),
    
    # Business reviews - cache for 3 days (259200 seconds) - reviews change more frequently
    'business_reviews': TTLCache(maxsize=1000, ttl=259200),
}""",
        """# MongoDB cache configuration - handled by decorators"""
    )
    
    # Add MongoDB cache decorators to methods
    methods_to_decorate = [
        ('def business_search', 'yelp_business_search'),
        ('def business_details', 'yelp_business_details'),
        ('def business_reviews', 'yelp_business_reviews')
    ]
    
    for method_def, cache_type in methods_to_decorate:
        if method_def in new_content:
            new_content = new_content.replace(
                method_def,
                f'@mongo_cached("{cache_type}")\n    {method_def}'
            )
    
    # Remove cache-related code from methods
    new_content = new_content.replace(
        'cache_key = cache_key_generator(*args, **kwargs)\n        \n        # Check cache first\n        if cache_key in self._cache[',
        '# Cache handled by MongoDB decorator\n        # '
    )
    
    new_content = new_content.replace(
        'self._cache[',
        '# self._cache['
    )
    
    # Write the updated content
    with open(yelp_api_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Yelp API migrated to MongoDB cache")


def migrate_foursquare_api():
    """Migrate Foursquare API from TTLCache to MongoDB cache"""
    
    print("🔄 Migrating Foursquare API to MongoDB cache...")
    
    foursquare_api_path = os.path.join(os.path.dirname(__file__), '..', 'service_api', 'fourquare_api.py')
    
    with open(foursquare_api_path, 'r') as f:
        content = f.read()
    
    # Replace TTLCache imports and configuration
    new_content = content.replace(
        'from cachetools import TTLCache',
        'from cache.mongo_cache_decorator import mongo_cached'
    )
    
    # Remove TTLCache configuration
    new_content = new_content.replace(
        """# Cache configuration with different TTL values for different API types
CACHE_CONFIG = {
    # Venue search results - cache for 7 days (604800 seconds) - venues don't change often
    'venue_search': TTLCache(maxsize=1000, ttl=604800),
    
    # Venue details - cache for 7 days (604800 seconds) - venue info is relatively stable
    'venue_details': TTLCache(maxsize=2000, ttl=604800),
    
    # Venue tips - cache for 3 days (259200 seconds) - tips change more frequently
    'venue_tips': TTLCache(maxsize=1000, ttl=259200),
}""",
        """# MongoDB cache configuration - handled by decorators"""
    )
    
    # Add MongoDB cache decorators to methods
    methods_to_decorate = [
        ('def venue_search', 'foursquare_venue_search'),
        ('def venue_details', 'foursquare_venue_details'),
        ('def venue_tips', 'foursquare_venue_tips')
    ]
    
    for method_def, cache_type in methods_to_decorate:
        if method_def in new_content:
            new_content = new_content.replace(
                method_def,
                f'@mongo_cached("{cache_type}")\n    {method_def}'
            )
    
    # Remove cache-related code from methods
    new_content = new_content.replace(
        'cache_key = cache_key_generator(*args, **kwargs)\n        \n        # Check cache first\n        if cache_key in self._cache[',
        '# Cache handled by MongoDB decorator\n        # '
    )
    
    new_content = new_content.replace(
        'self._cache[',
        '# self._cache['
    )
    
    # Write the updated content
    with open(foursquare_api_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Foursquare API migrated to MongoDB cache")


def migrate_ticketmaster_api():
    """Add MongoDB cache to Ticketmaster API"""
    
    print("🔄 Adding MongoDB cache to Ticketmaster API...")
    
    ticketmaster_api_path = os.path.join(os.path.dirname(__file__), '..', 'service_api', 'ticketmaster_api.py')
    
    with open(ticketmaster_api_path, 'r') as f:
        content = f.read()
    
    # Add MongoDB cache import
    if 'from cache.mongo_cache_decorator import mongo_cached' not in content:
        new_content = content.replace(
            'from typing import Optional, Dict, Any, List\nfrom .base_api import BaseAPI',
            'from typing import Optional, Dict, Any, List\nfrom .base_api import BaseAPI\nfrom cache.mongo_cache_decorator import mongo_cached'
        )
    else:
        new_content = content
    
    # Add MongoDB cache decorators to methods
    methods_to_decorate = [
        ('def search_events', 'ticketmaster_events_search'),
        ('def event_details', 'ticketmaster_event_details'),
        ('def venue_search', 'ticketmaster_venue_search')
    ]
    
    for method_def, cache_type in methods_to_decorate:
        if method_def in new_content and f'@mongo_cached("{cache_type}")' not in new_content:
            new_content = new_content.replace(
                method_def,
                f'@mongo_cached("{cache_type}")\n    {method_def}'
            )
    
    # Write the updated content
    with open(ticketmaster_api_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Ticketmaster API updated with MongoDB cache")


def test_mongodb_cache_connection():
    """Test MongoDB cache connection"""
    
    print("🧪 Testing MongoDB cache connection...")
    
    try:
        cache = get_mongo_cache()
        print("✅ MongoDB cache connection successful")
        
        # Test basic cache operations
        test_data = {"test": "data", "timestamp": "2025-09-20"}
        cache.set('google_places_search', test_data, 'test_key')
        
        retrieved_data = cache.get('google_places_search', 'test_key')
        if retrieved_data and retrieved_data.get('test') == 'data':
            print("✅ MongoDB cache operations working")
            cache.delete('google_places_search', 'test_key')
            print("✅ Test data cleaned up")
            return True
        else:
            print("❌ MongoDB cache operations failed")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB cache connection failed: {e}")
        return False


def main():
    """Main migration function"""
    
    print("🚀 Starting API Cache Migration to MongoDB")
    print("=" * 60)
    
    # Test MongoDB connection first
    if not test_mongodb_cache_connection():
        print("❌ MongoDB cache not available. Please check MongoDB connection.")
        return False
    
    print()
    
    # Migrate all APIs
    try:
        migrate_google_api()
        migrate_yelp_api()
        migrate_foursquare_api()
        migrate_ticketmaster_api()
        
        print()
        print("🎉 All APIs successfully migrated to MongoDB cache!")
        print()
        print("📋 Migration Summary:")
        print("✅ Google API - Now uses MongoDB cache")
        print("✅ Yelp API - Now uses MongoDB cache")
        print("✅ Foursquare API - Now uses MongoDB cache")
        print("✅ Ticketmaster API - Now uses MongoDB cache")
        print()
        print("🚀 Benefits:")
        print("- Persistent caching across process restarts")
        print("- Faster API responses after first call")
        print("- Reduced API costs and rate limiting")
        print("- Better performance for repeated queries")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
