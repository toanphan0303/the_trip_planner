# MongoDB Cache System

This directory contains a comprehensive MongoDB-based caching system for API clients (Google, Yelp, and Foursquare).

## Features

- **Persistent Caching**: Cache API responses in MongoDB for better performance and cost savings
- **Automatic Expiration**: TTL-based expiration with MongoDB's built-in TTL indexes
- **Multiple Cache Types**: Separate collections for different API endpoints and data types
- **Efficient Indexing**: Optimized indexes for fast cache lookups
- **Statistics & Monitoring**: Built-in cache statistics and monitoring capabilities
- **Easy Integration**: Simple decorators for adding caching to existing API methods

## Files

- `mongo_db_cache.py` - Core MongoDB cache implementation
- `mongo_cache_decorator.py` - Decorators for easy integration
- `mongo_cache_example.py` - Usage examples and demonstrations
- `migrate_to_mongo_cache.py` - Migration script for existing APIs

## Setup

### 1. Install Dependencies

```bash
pip install pymongo>=4.6.0
```

### 2. Configure MongoDB

Set the MongoDB connection URI in your environment:

```bash
export MONGODB_URI="mongodb://localhost:27017/"
```

Or add to your `.env` file:
```
MONGODB_URI=mongodb://localhost:27017/
```

### 3. Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Using local installation
mongod
```

## Usage

### Basic Usage

```python
from server.cache.mongo_db_cache import get_mongo_cache

# Get cache instance
cache = get_mongo_cache()

# Cache data
cache.set('google_places_search', response_data, 'coffee', 'San Francisco, CA')

# Retrieve cached data
cached_data = cache.get('google_places_search', 'coffee', 'San Francisco, CA')
```

### Using Decorators

```python
from server.cache.mongo_cache_decorator import mongo_cached

class MyAPI:
    @mongo_cached('google_places_search')
    def places_search(self, query: str, location: str, **kwargs):
        # Your API call here
        return api_response
```

### Cache Types

The system supports these cache types:

#### Google API
- `google_places_search` - Places search results (7 days TTL)
- `google_places_nearby` - Nearby search results (7 days TTL)
- `google_geocoding` - Geocoding results (30 days TTL)
- `google_place_details` - Place details (7 days TTL)

#### Yelp API
- `yelp_business_search` - Business search results (7 days TTL)
- `yelp_business_details` - Business details (7 days TTL)
- `yelp_business_reviews` - Business reviews (3 days TTL)

#### Foursquare API
- `foursquare_venue_search` - Venue search results (7 days TTL)
- `foursquare_venue_details` - Venue details (7 days TTL)
- `foursquare_venue_tips` - Venue tips (3 days TTL)

## Migration

To migrate existing API clients to use MongoDB caching:

```bash
python -m server.cache.migrate_to_mongo_cache
```

This will:
1. Patch existing API client methods with MongoDB caching
2. Test the integration
3. Show migration status

## Cache Management

### View Statistics

```python
from server.cache.mongo_db_cache import get_mongo_cache_stats

stats = get_mongo_cache_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Total size: {stats['total_size_mb']} MB")
```

### Clear Cache

```python
from server.cache.mongo_db_cache import clear_mongo_cache

# Clear specific cache type
clear_mongo_cache('google_places_search')

# Clear all caches
clear_mongo_cache()
```

### Manual Cache Operations

```python
from server.cache.mongo_db_cache import get_mongo_cache

cache = get_mongo_cache()

# Set cache
cache.set('cache_type', data, *args, **kwargs)

# Get cache
data = cache.get('cache_type', *args, **kwargs)

# Delete cache
cache.delete('cache_type', *args, **kwargs)
```

## Configuration

### TTL Settings

Default TTL values by cache type:

- **Geocoding**: 30 days (addresses rarely change)
- **Places/Businesses**: 7 days (relatively stable)
- **Reviews/Tips**: 3 days (change more frequently)

### Collection Settings

Each cache type has its own MongoDB collection with:
- TTL index on `expires_at` field for automatic cleanup
- Indexes on common search fields for fast lookups
- Configurable maximum size limits

## Manual MongoDB Inspection

### Using MongoDB Shell (mongosh)

Connect to your MongoDB instance and inspect the cache data:

```bash
# Connect to MongoDB (using Docker container credentials)
mongosh "mongodb://admin:trip_planner_pass@localhost:27017/"

# Or connect to the Docker container directly
docker exec -it trip_planner_mongodb mongosh
```

Once connected, you can inspect the cache:

```bash
# Switch to the cache database
use trip_planner_cache

# List all collections
show collections

# View documents in a specific cache collection
db.google_places_search.find().pretty()

# Count documents in a collection
db.google_places_search.countDocuments()

# Find specific cache entries
db.google_places_search.find({"query": "coffee"}).pretty()

# View cache statistics
db.google_places_search.stats()

# Check TTL indexes
db.google_places_search.getIndexes()

# View all cache entries with expiration info
db.google_places_search.find({}, {
    cache_key: 1, 
    created_at: 1, 
    expires_at: 1, 
    cache_type: 1
}).pretty()
```

### Using MongoDB Compass (GUI)

1. **Download MongoDB Compass**: https://www.mongodb.com/products/compass
2. **Connect using connection string**: `mongodb://admin:trip_planner_pass@localhost:27017/`
3. **Navigate to database**: `trip_planner_cache`
4. **Browse collections**: Explore cache collections visually
5. **Run queries**: Use the built-in query interface


### Quick Inspection Commands

```bash
# Check if MongoDB container is running
docker ps --filter name=trip_planner_mongodb

# View MongoDB logs
docker logs trip_planner_mongodb

# Connect to MongoDB shell
docker exec -it trip_planner_mongodb mongosh

# Quick database stats
docker exec -it trip_planner_mongodb mongosh --eval "db.stats()" trip_planner_cache

# List all databases
docker exec -it trip_planner_mongodb mongosh --eval "show dbs"

# Count documents in all cache collections
docker exec -it trip_planner_mongodb mongosh --eval "
use trip_planner_cache;
db.google_places_search.countDocuments();
db.yelp_business_search.countDocuments();
db.foursquare_venue_search.countDocuments();
" --quiet
```

## Monitoring

### Cache Statistics

```python
from server.cache.mongo_db_cache import get_mongo_cache_stats

stats = get_mongo_cache_stats()
for cache_type, cache_stats in stats['collections'].items():
    print(f"{cache_type}: {cache_stats['documents']} docs, {cache_stats['size_mb']} MB")
```

### Performance Metrics

The cache system provides:
- Hit/miss logging with emoji indicators
- Document counts per collection
- Storage size per collection
- TTL information

## Troubleshooting

### Connection Issues

```python
# Test MongoDB connection
from server.cache.mongo_db_cache import get_mongo_cache

try:
    cache = get_mongo_cache()
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
```

### Common Issues

1. **MongoDB not running**: Start MongoDB service
2. **Wrong URI**: Check `MONGODB_URI` environment variable
3. **Permission issues**: Ensure MongoDB user has read/write permissions
4. **Network issues**: Check firewall and network connectivity

### Debug Mode

Enable debug logging to see cache operations:

```python
import logging
logging.getLogger('server.cache.mongo_db_cache').setLevel(logging.DEBUG)
```

## Best Practices

1. **Use appropriate TTL**: Set longer TTL for stable data, shorter for dynamic data
2. **Monitor cache size**: Regularly check cache statistics to prevent storage issues
3. **Handle failures gracefully**: Cache failures shouldn't break API functionality
4. **Use specific cache types**: Use the most specific cache type for your data
5. **Clean up old caches**: Periodically clear unused cache types

## Performance Benefits

- **Reduced API calls**: Significantly reduce external API usage and costs
- **Faster response times**: Cached responses return instantly
- **Better reliability**: Reduced dependency on external API availability
- **Cost savings**: Lower API usage means lower costs
- **Improved user experience**: Faster search results and recommendations
