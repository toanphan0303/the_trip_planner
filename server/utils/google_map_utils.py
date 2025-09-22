"""
Google Maps utilities for place search and geocoding operations
"""

import asyncio
from typing import Dict, List
from .radius import calculate_smart_radius, pick_bounds, base_radius_from_bounds, _is_major_city
from service_api.google_api import google_places_nearby_search_async


def _process_and_deduplicate_places(search_results: List[Dict], all_places: Dict) -> List[Dict]:
    """
    Process search results and deduplicate places by ID.
    
    Args:
        search_results: List of search results from async API calls
        all_places: Dictionary to track unique places by ID (modified in place)
        
    Returns:
        List of processed results with deduplicated places
    """
    places_results = []
    
    for result in search_results:
        place_type = result["type"]
        places = result["places"]
        error = result["error"]
        
        if error:
            places_results.append({
                "type": place_type,
                "error": error,
                "places": []
            })
        else:
            # Process places and deduplicate by ID
            type_places = []
            for place in places:
                place_id = place.get("id")
                if place_id and place_id not in all_places:
                    # First time seeing this place - add it
                    all_places[place_id] = place
                    type_places.append(place)
                elif place_id in all_places:
                    # Place already exists - merge types if needed
                    existing_place = all_places[place_id]
                    existing_types = set(existing_place.get("types", []))
                    new_types = set(place.get("types", []))
                    # Merge types and update the existing place
                    existing_place["types"] = list(existing_types.union(new_types))
            
            places_results.append({
                "type": place_type,
                "places": type_places
            })
    
    return places_results


def search_nearby_places_from_geocode(
    geocode_result: Dict,
    days: int,
    mode: str = "transit",
    pace: str = "standard",
    types: List[str] | None = None,
    destination_name: str = None,
    max_results_per_type: int = 5,
) -> Dict:
    """
    Search for nearby places around a geocoded location using Google Places API.
    
    Dynamically calculates search radius based on trip duration, transportation mode,
    and travel pace. For city-scale locations, performs nearby searches for multiple
    place types. For country-scale locations, returns a text search query.
    
    Args:
        geocode_result: Geocoding result from Google API
        days: Trip duration in days
        mode: Transportation mode ("walk", "transit", "car")
        pace: Trip pace ("relaxed", "standard", "aggressive")
        types: List of place types to search for (optional)
        destination_name: Name of destination for smart radius calculation
        max_results_per_type: Maximum number of results per place type
        
    Returns:
      {
        'center': (lat, lng),
        'radius_m': int | None,            # None means use Text Search
        'places_results': [ ... ],         # actual Google Places results (if radius_m not None)
        'textsearch_query': str | None,    # if country-scale
        'debug': {...}                     # R0/ns/ew/bounds etc.
      }
    """
    g = geocode_result["geometry"]
    center = (g["location"]["lat"], g["location"]["lng"])
    bounds = pick_bounds(g)

    # If no bounds present, fall back to a default radius
    if bounds:
        R0_m, ns_m, ew_m = base_radius_from_bounds(bounds)
        # If the area is huge (country/region), skip Nearby → Text Search
        # But allow major cities to use Nearby search even if their bounds are large
        is_major_city = _is_major_city(destination_name, geocode_result)
        too_big = max(ns_m, ew_m) > 120_000 and not is_major_city  # ~120 km heuristic
    else:
        R0_m, ns_m, ew_m, too_big = 10_000, 0.0, 0.0, False

    if too_big:
        query = f"top tourist attractions in {geocode_result['formatted_address']}"
        return {
            "center": center,
            "radius_m": None,
            "places_results": [],
            "textsearch_query": query,
            "debug": {"ns_m": ns_m, "ew_m": ew_m, "R0_m": R0_m, "scale": "country/region"},
        }

    # Smart radius calculation with destination awareness and geocode data
    radius_m = calculate_smart_radius(R0_m, days, mode, pace, destination_name, geocode_result)

    # Default categories to seed diversity (1 request per type)
    if not types:
        from constant.place_types import PlaceTypes
        types = PlaceTypes.get_trip_planning_types()

    lat, lng = center
    location_str = f"{lat:.7f},{lng:.7f}"

    print(f"Searching for places in {location_str} with radius {radius_m} and types {types}")
    
    # Call Google Places API for each type in parallel using async
    places_results = []
    all_places = {}  # Dictionary to store unique places by ID
    
    async def search_place_type(place_type: str) -> Dict:
        """Search for a specific place type asynchronously"""
        try:
            response = await google_places_nearby_search_async(
                location=location_str,
                radius=radius_m,
                place_types=[place_type],
                max_results=max_results_per_type
            )
            return {
                "type": place_type,
                "places": response.places,
                "error": None
            }
        except Exception as e:
            return {
                "type": place_type,
                "places": [],
                "error": str(e)
            }
    
    # Run all searches in parallel
    async def run_parallel_searches():
        tasks = [search_place_type(place_type) for place_type in types]
        return await asyncio.gather(*tasks)
    
    # Execute the async searches
    search_results = asyncio.run(run_parallel_searches())
    
    # Process results and deduplicate
    places_results = _process_and_deduplicate_places(search_results, all_places)

    # Calculate deduplication statistics
    unique_places_count = len(all_places)

    return {
        "center": center,
        "radius_m": radius_m,
        "places_results": places_results,
        "textsearch_query": None,
        "debug": {
            "ns_m": int(ns_m), 
            "ew_m": int(ew_m), 
            "R0_m": int(R0_m), 
            "scale": "city/neighborhood",
            "unique_places": unique_places_count,
        },
    }


async def search_nearby_places_from_geocode_async(
    geocode_result: Dict,
    days: int,
    mode: str = "transit",
    pace: str = "standard",
    types: List[str] | None = None,
    destination_name: str = None,
    max_results_per_type: int = 5,
) -> Dict:
    """
    Async version of search_nearby_places_from_geocode for better performance.
    
    This function performs the same operations as the sync version but uses async
    parallel calls to the Google Places API, significantly improving performance
    when searching for multiple place types.
    
    Args:
        geocode_result: Geocoding result from Google API
        days: Trip duration in days
        mode: Transportation mode ("walk", "transit", "car")
        pace: Trip pace ("relaxed", "standard", "aggressive")
        types: List of place types to search for (optional)
        destination_name: Name of destination for smart radius calculation
        max_results_per_type: Maximum number of results per place type
        
    Returns:
        Same format as search_nearby_places_from_geocode
    """
    g = geocode_result["geometry"]
    center = (g["location"]["lat"], g["location"]["lng"])
    bounds = pick_bounds(g)

    # If no bounds present, fall back to a default radius
    if bounds:
        R0_m, ns_m, ew_m = base_radius_from_bounds(bounds)
        # If the area is huge (country/region), skip Nearby → Text Search
        # But allow major cities to use Nearby search even if their bounds are large
        is_major_city = _is_major_city(destination_name, geocode_result)
        too_big = max(ns_m, ew_m) > 120_000 and not is_major_city  # ~120 km heuristic
    else:
        R0_m, ns_m, ew_m, too_big = 10_000, 0.0, 0.0, False

    if too_big:
        query = f"top tourist attractions in {geocode_result['formatted_address']}"
        return {
            "center": center,
            "radius_m": None,
            "places_results": [],
            "textsearch_query": query,
            "debug": {"ns_m": ns_m, "ew_m": ew_m, "R0_m": R0_m, "scale": "country/region"},
        }

    # Smart radius calculation with destination awareness and geocode data
    radius_m = calculate_smart_radius(R0_m, days, mode, pace, destination_name, geocode_result)

    # Default categories to seed diversity (1 request per type)
    if not types:
        from constant.place_types import PlaceTypes
        types = PlaceTypes.get_trip_planning_types()

    lat, lng = center
    location_str = f"{lat:.7f},{lng:.7f}"

    print(f"Searching for places in {location_str} with radius {radius_m} and types {types} (async)")
    
    # Call Google Places API for each type in parallel using async
    places_results = []
    all_places = {}  # Dictionary to store unique places by ID
    
    async def search_place_type(place_type: str) -> Dict:
        """Search for a specific place type asynchronously"""
        try:
            response = await google_places_nearby_search_async(
                location=location_str,
                radius=radius_m,
                place_types=[place_type],
                max_results=max_results_per_type
            )
            return {
                "type": place_type,
                "places": response.places,
                "error": None
            }
        except Exception as e:
            return {
                "type": place_type,
                "places": [],
                "error": str(e)
            }
    
    # Run all searches in parallel
    search_results = await asyncio.gather(*[search_place_type(place_type) for place_type in types])
    
    # Process results and deduplicate
    places_results = _process_and_deduplicate_places(search_results, all_places)

    # Calculate deduplication statistics
    unique_places_count = len(all_places)

    return {
        "center": center,
        "radius_m": radius_m,
        "places_results": places_results,
        "textsearch_query": None,
        "debug": {
            "ns_m": int(ns_m), 
            "ew_m": int(ew_m), 
            "R0_m": int(R0_m), 
            "scale": "city/neighborhood",
            "unique_places": unique_places_count,
        },
    }
