# Google Places API Base Types System

This module provides a comprehensive system for managing Google Places API place types based on the [official Google Places API documentation](https://developers.google.com/maps/documentation/places/web-service/place-types).

## Overview

The base types system organizes all Google Places API place types into logical categories and provides easy access methods for trip planning applications.

### Key Features

- **Comprehensive Coverage**: Includes all Table A and Table B place types from Google's documentation
- **Categorized Organization**: Types are organized into 19 logical categories
- **Trip Planning Focus**: Curated lists optimized for tourism and travel planning
- **Validation Support**: Built-in validation for place types
- **Easy Integration**: Simple API for accessing types by category or use case

## Table A vs Table B Types

### Table A Types (113 types)
- Can be used in **both requests and responses**
- Used for filtering in Nearby Search, Text Search, and Autocomplete requests
- Examples: `restaurant`, `tourist_attraction`, `museum`, `park`

### Table B Types (90 types)
- Primarily for **responses only**
- Can only be used in Autocomplete `includedPrimaryTypes` parameter
- Examples: `mexican_restaurant`, `sushi_restaurant`, `steak_house`

## Categories

The system organizes types into 19 categories:

1. **Automotive** - Car dealers, gas stations, parking, etc.
2. **Business** - Banks, ATMs, post offices, etc.
3. **Culture** - Museums, art galleries, tourist attractions
4. **Education** - Schools, universities, libraries
5. **Entertainment & Recreation** - Parks, zoos, amusement parks, etc.
6. **Facilities** - Hospitals, police stations, courthouses
7. **Finance** - Banks, ATMs, insurance agencies
8. **Food & Drink** - Restaurants, cafes, bars, bakeries
9. **Geographical Areas** - Administrative areas, localities, etc.
10. **Government** - Government offices, embassies, courthouses
11. **Health & Wellness** - Hospitals, pharmacies, doctors, dentists
12. **Housing** - Lodging and accommodation
13. **Lodging** - Hotels, motels, hostels
14. **Natural Features** - Parks, natural landmarks
15. **Places of Worship** - Churches, mosques, temples, synagogues
16. **Services** - Beauty salons, repair shops, legal services
17. **Shopping** - Stores, malls, markets, supermarkets
18. **Sports** - Gyms, stadiums, sports facilities
19. **Transportation** - Airports, train stations, bus stops

## Usage Examples

### Basic Usage

```python
from constant.place_types import (
    PlaceTypes, 
    PlaceTypeCategory, 
    get_trip_planning_types,
    get_food_types,
    is_valid_place_type
)

# Get curated types for trip planning
trip_types = get_trip_planning_types()
print(f"Found {len(trip_types)} trip planning types")

# Get all food types
food_types = get_food_types()
print(f"Found {len(food_types)} food types")

# Get types by category
culture_types = PlaceTypes.get_types_by_category(PlaceTypeCategory.CULTURE, "A")
print(f"Culture types: {culture_types}")

# Validate a place type
is_valid = is_valid_place_type("restaurant", "A")
print(f"restaurant is valid for Table A: {is_valid}")
```

### Advanced Usage

```python
# Get category for a specific type
category = PlaceTypes.get_category_for_type("restaurant")
print(f"restaurant belongs to: {category.value}")

# Get all Table A types (for requests)
all_table_a = PlaceTypes.get_all_table_a_types()
print(f"Total Table A types: {len(all_table_a)}")

# Get all Table B types (for responses)
all_table_b = PlaceTypes.get_all_table_b_types()
print(f"Total Table B types: {len(all_table_b)}")

# Get all types from both tables
all_types = PlaceTypes.get_all_types()
print(f"Total unique types: {len(all_types)}")
```

### Integration with Google Places API

```python
# Use in Google Places API calls
from constant.place_types import get_trip_planning_types

# Get types for nearby search
place_types = get_trip_planning_types()

# Use in your API calls
for place_type in place_types:
    response = google_places_nearby_search(
        location="40.7128,-74.0060",
        radius=1000,
        place_type=place_type,
        max_results=5
    )
    # Process response...
```

## Curated Lists

### Trip Planning Types (27 types)
Optimized for tourism and travel planning:
- Attractions: `tourist_attraction`, `museum`, `art_gallery`, `park`, `zoo`
- Food: `restaurant`, `cafe`, `bar`, `bakery`
- Shopping: `shopping_mall`, `store`, `market`
- Entertainment: `movie_theater`, `night_club`, `casino`
- Transportation: `airport`, `train_station`, `bus_station`
- Services: `lodging`, `atm`, `bank`, `pharmacy`

### Food Types (42 types)
All food and drink related types including:
- General: `restaurant`, `cafe`, `bar`, `bakery`
- Cuisine-specific: `mexican_restaurant`, `italian_restaurant`, `japanese_restaurant`
- Meal types: `breakfast_restaurant`, `brunch_restaurant`
- Specialized: `ice_cream_shop`, `sandwich_shop`, `pizza_restaurant`

### Attraction Types (13 types)
Entertainment and cultural attractions:
- `amusement_park`, `aquarium`, `art_gallery`, `bowling_alley`
- `casino`, `movie_theater`, `night_club`, `park`
- `tourist_attraction`, `zoo`, `museum`

### Shopping Types (38 types)
All shopping related types including:
- General: `store`, `shopping_mall`, `supermarket`
- Specific: `clothing_store`, `electronics_store`, `book_store`
- Specialized: `florist`, `jewelry_store`, `pet_store`

## Validation

The system provides validation to ensure you're using correct place types:

```python
# Validate Table A types (for requests)
is_valid_a = is_valid_place_type("restaurant", "A")  # True
is_valid_a = is_valid_place_type("invalid_type", "A")  # False

# Validate Table B types (for responses)
is_valid_b = is_valid_place_type("mexican_restaurant", "B")  # True
is_valid_b = is_valid_place_type("restaurant", "B")  # True (also in Table A)
```

## Integration with Existing Code

The system is already integrated with your trip planning code:

```python
# In utils/radius.py
from constant.place_types import get_trip_planning_types

# Default categories to seed diversity
if not types:
    types = get_trip_planning_types()
```

## Best Practices

1. **Use Table A types for requests** - These are the only types that can be used in API requests
2. **Use curated lists** - The `get_trip_planning_types()` function provides optimized types for tourism
3. **Validate types** - Always validate place types before using them in API calls
4. **Consider your use case** - Use specific category functions like `get_food_types()` for targeted searches
5. **Handle both tables** - Table B types may appear in responses even if not requested

## Statistics

- **Table A types**: 113 (request/response)
- **Table B types**: 90 (response only)
- **Total unique types**: 151
- **Trip planning types**: 27 (curated)
- **Food & drink types**: 42
- **Attraction types**: 13
- **Shopping types**: 38

## References

- [Google Places API Place Types Documentation](https://developers.google.com/maps/documentation/places/web-service/place-types)
- [Google Places API Nearby Search](https://developers.google.com/maps/documentation/places/web-service/search-nearby)
- [Google Places API Text Search](https://developers.google.com/maps/documentation/places/web-service/search-text)
