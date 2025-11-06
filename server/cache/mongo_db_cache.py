"""
MongoDB-based caching implementation for API clients
"""

import os
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration for different API types"""
    collection_name: str
    ttl_days: int = 7  # Default TTL in days
    max_size_mb: int = 100  # Maximum collection size in MB
    index_fields: list = None  # Fields to index for faster lookups
    
    def __post_init__(self):
        if self.index_fields is None:
            self.index_fields = ['cache_key', 'created_at', 'expires_at']


class MongoDBCache:
    """MongoDB-based cache implementation for API responses"""
    
    def __init__(self, 
                 mongo_uri: Optional[str] = None,
                 database_name: str = "trip_planner_cache",
                 default_ttl_days: int = 7):
        """
        Initialize MongoDB cache
        
        Args:
            mongo_uri: MongoDB connection URI. If None, uses environment variable MONGODB_URI
            database_name: Database name for cache storage
            default_ttl_days: Default TTL in days for cache entries
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = database_name
        self.default_ttl_days = default_ttl_days
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collections: Dict[str, Any] = {}
        
        # Cache configurations for different API types
        self.cache_configs = {
            # Google API caches
            'google_places_search': CacheConfig(
                collection_name='google_places_search',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'query', 'location']
            ),
            'google_places_nearby': CacheConfig(
                collection_name='google_places_nearby',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'location', 'radius']
            ),
            'google_geocoding': CacheConfig(
                collection_name='google_geocoding',
                ttl_days=30,  # Geocoding results are very stable
                index_fields=['cache_key', 'created_at', 'expires_at', 'address']
            ),
            'google_place_details': CacheConfig(
                collection_name='google_place_details',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'place_id']
            ),
            
            # Yelp API caches
            'yelp_business_search': CacheConfig(
                collection_name='yelp_business_search',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'term', 'location']
            ),
            'yelp_business_details': CacheConfig(
                collection_name='yelp_business_details',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'business_id']
            ),
            'yelp_business_reviews': CacheConfig(
                collection_name='yelp_business_reviews',
                ttl_days=30,  # Reviews change more frequently
                index_fields=['cache_key', 'created_at', 'expires_at', 'business_id']
            ),
            
            # Foursquare API caches
            'foursquare_venue_search': CacheConfig(
                collection_name='foursquare_venue_search',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'query', 'll']
            ),
            'foursquare_venue_details': CacheConfig(
                collection_name='foursquare_venue_details',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'venue_id']
            ),
            'foursquare_venue_tips': CacheConfig(
                collection_name='foursquare_venue_tips',
                ttl_days=30,  # Tips change more frequently
                index_fields=['cache_key', 'created_at', 'expires_at', 'venue_id']
            ),
            'foursquare_places_match': CacheConfig(
                collection_name='foursquare_places_match',
                ttl_days=30,
                index_fields=['cache_key', 'created_at', 'expires_at', 'name', 'city', 'cc']
            ),
            
            # LLM Analysis caches
            'destination_radius': CacheConfig(
                collection_name='destination_radius',
                ttl_days=90,  # Destination characteristics rarely change
                index_fields=['cache_key', 'created_at', 'expires_at', 'destination', 'duration_days']
            ),
        }
        
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB and initialize collections"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            
            # Initialize collections and indexes
            self._setup_collections()
            
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    def _setup_collections(self):
        """Setup collections and indexes"""
        for cache_type, config in self.cache_configs.items():
            collection = self.db[config.collection_name]
            self.collections[cache_type] = collection
            
            # Create TTL index for automatic expiration
            collection.create_index("expires_at", expireAfterSeconds=0)
            
            # Create other indexes for faster lookups
            for field in config.index_fields:
                if field != "expires_at":  # Skip TTL index field
                    collection.create_index(field)
            
            logger.info(f"Setup collection: {config.collection_name}")
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from function arguments"""
        # Convert all arguments to strings and create a hash
        key_parts = []
        
        # Add positional arguments
        for arg in args:
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
            if value is not None:
                key_parts.append(f"{key}={value}")
        
        # Create hash from combined key parts
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, cache_type: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached data
        
        Args:
            cache_type: Type of cache (e.g., 'google_places_search')
            *args, **kwargs: Arguments to generate cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        if cache_type not in self.cache_configs:
            logger.warning(f"Unknown cache type: {cache_type}")
            return None
        
        try:
            cache_key = self._generate_cache_key(*args, **kwargs)
            collection = self.collections[cache_type]
            
            # Find cached document
            doc = collection.find_one({
                "cache_key": cache_key,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if doc:
                logger.debug(f"Cache HIT for {cache_type}: {cache_key[:16]}...")
                return doc.get("data")
            else:
                logger.debug(f"Cache MISS for {cache_type}: {cache_key[:16]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cache for {cache_type}: {e}")
            return None
    
    def set(self, cache_type: str, data: Dict[str, Any], *args, **kwargs) -> bool:
        """
        Set cached data
        
        Args:
            cache_type: Type of cache (e.g., 'google_places_search')
            data: Data to cache
            *args, **kwargs: Arguments to generate cache key
            
        Returns:
            True if successful, False otherwise
        """
        if cache_type not in self.cache_configs:
            logger.warning(f"Unknown cache type: {cache_type}")
            return False
        
        try:
            cache_key = self._generate_cache_key(*args, **kwargs)
            config = self.cache_configs[cache_type]
            collection = self.collections[cache_type]
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(days=config.ttl_days)
            
            # Create document
            doc = {
                "cache_key": cache_key,
                "data": data,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "cache_type": cache_type,
                "ttl_days": config.ttl_days
            }
            
            # Cache key is sufficient for lookups - no need to store parameters
            
            # Upsert document (update if exists, insert if not)
            collection.replace_one(
                {"cache_key": cache_key},
                doc,
                upsert=True
            )
            
            logger.debug(f"Cached data for {cache_type}: {cache_key[:16]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache for {cache_type}: {e}")
            return False
    
    
    def delete(self, cache_type: str, *args, **kwargs) -> bool:
        """
        Delete cached data
        
        Args:
            cache_type: Type of cache
            *args, **kwargs: Arguments to generate cache key
            
        Returns:
            True if successful, False otherwise
        """
        if cache_type not in self.cache_configs:
            logger.warning(f"Unknown cache type: {cache_type}")
            return False
        
        try:
            cache_key = self._generate_cache_key(*args, **kwargs)
            collection = self.collections[cache_type]
            
            result = collection.delete_one({"cache_key": cache_key})
            
            if result.deleted_count > 0:
                logger.debug(f"Deleted cache for {cache_type}: {cache_key[:16]}...")
                return True
            else:
                logger.debug(f"Cache not found for deletion: {cache_type}: {cache_key[:16]}...")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting cache for {cache_type}: {e}")
            return False
    
    def clear(self, cache_type: Optional[str] = None) -> bool:
        """
        Clear cache
        
        Args:
            cache_type: Specific cache type to clear. If None, clears all caches
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if cache_type:
                if cache_type in self.cache_configs:
                    collection = self.collections[cache_type]
                    collection.drop()
                    logger.info(f"Cleared cache: {cache_type}")
                    return True
                else:
                    logger.warning(f"Unknown cache type: {cache_type}")
                    return False
            else:
                # Clear all caches
                for cache_type_name, collection in self.collections.items():
                    collection.drop()
                logger.info("Cleared all caches")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "database": self.database_name,
            "collections": {},
            "total_documents": 0,
            "total_size_mb": 0
        }
        
        try:
            for cache_type, collection in self.collections.items():
                config = self.cache_configs[cache_type]
                
                # Count documents
                doc_count = collection.count_documents({})
                
                # Get collection stats
                try:
                    coll_stats = self.db.command("collStats", config.collection_name)
                    size_mb = coll_stats.get("size", 0) / (1024 * 1024)
                except Exception:
                    size_mb = 0
                
                stats["collections"][cache_type] = {
                    "documents": doc_count,
                    "size_mb": round(size_mb, 2),
                    "ttl_days": config.ttl_days,
                    "max_size_mb": config.max_size_mb
                }
                
                stats["total_documents"] += doc_count
                stats["total_size_mb"] += size_mb
            
            stats["total_size_mb"] = round(stats["total_size_mb"], 2)
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return stats
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")


# Global cache instance
_mongo_cache: Optional[MongoDBCache] = None


def get_mongo_cache() -> MongoDBCache:
    """Get or create global MongoDB cache instance"""
    global _mongo_cache
    if _mongo_cache is None:
        _mongo_cache = MongoDBCache()
    return _mongo_cache


def clear_mongo_cache(cache_type: Optional[str] = None) -> bool:
    """Clear MongoDB cache"""
    cache = get_mongo_cache()
    return cache.clear(cache_type)


def get_mongo_cache_stats() -> Dict[str, Any]:
    """Get MongoDB cache statistics"""
    cache = get_mongo_cache()
    return cache.get_stats()


def close_mongo_cache():
    """Close MongoDB cache connection"""
    global _mongo_cache
    if _mongo_cache:
        _mongo_cache.close()
        _mongo_cache = None
