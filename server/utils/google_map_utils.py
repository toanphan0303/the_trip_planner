"""
Google Maps utilities for place search and geocoding operations
"""

import asyncio
from typing import Dict, List
from .radius import calculate_smart_radius, pick_bounds, base_radius_from_bounds, _is_major_city
from service_api.google_api import google_places_nearby_search_async
from models.google_map_models import GooglePlacesResponse, GooglePlace


def _process_and_deduplicate_places(search_results: List[GooglePlacesResponse], all_places: Dict) -> List[GooglePlace]:
    """
    Process search results and deduplicate places by ID.
    
    Args:
        search_results: List of GooglePlacesResponse objects from async API calls
        all_places: Dictionary to track unique places by ID (modified in place)
        
    Returns:
        List of deduplicated GooglePlace objects
    """
    deduplicated_places = []
    
    for result in search_results:
        places = result.places
        
        # Process places and deduplicate by ID
        for place in places:
            place_id = place.id
            if place_id and place_id not in all_places:
                # First time seeing this place - add it
                all_places[place_id] = place
                deduplicated_places.append(place)
            elif place_id in all_places:
                # Place already exists - merge types if needed
                existing_place = all_places[place_id]
                existing_types = set(existing_place.types)
                new_types = set(place.types)
                # Merge types and update the existing place
                existing_place.types = list(existing_types.union(new_types))
    
    return deduplicated_places


def search_nearby_places_from_geocode(
    geocode_result: Dict,
    days: int,
    mode: str = "transit",
    pace: str = "standard",
    types: List[str] | None = None,
    destination_name: str = None,
    max_results_per_type: int = 5,
) -> List[GooglePlace]:
    """
    Search for nearby places around a geocoded location using Google Places API.
    
    Dynamically calculates search radius based on trip duration, transportation mode,
    and travel pace. For city-scale locations, performs nearby searches for multiple
    place types. For country-scale locations, returns empty list.
    
    Args:
        geocode_result: Geocoding result from Google API
        days: Trip duration in days
        mode: Transportation mode ("walk", "transit", "car")
        pace: Trip pace ("relaxed", "standard", "aggressive")
        types: List of place types to search for (optional)
        destination_name: Name of destination for smart radius calculation
        max_results_per_type: Maximum number of results per place type
        
    Returns:
        List of GooglePlace objects found in the area
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
        # For country-scale locations, return empty list
        return []

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
    all_places = {}  # Dictionary to store unique places by ID
    
    async def search_place_type(place_type: str) -> GooglePlacesResponse:
        """Search for a specific place type asynchronously"""
        try:
            response = await google_places_nearby_search_async(
                location=location_str,
                radius=radius_m,
                place_types=[place_type],
                max_results=max_results_per_type
            )
            return response
        except Exception:
            # Return empty GooglePlacesResponse on error
            return GooglePlacesResponse(places=[], next_page_token=None)
    
    # Run all searches in parallel
    async def run_parallel_searches():
        tasks = [search_place_type(place_type) for place_type in types]
        return await asyncio.gather(*tasks)
    
    # Execute the async searches
    search_results = asyncio.run(run_parallel_searches())
    
    # Process results and deduplicate
    places_results = _process_and_deduplicate_places(search_results, all_places)

    return places_results


async def search_nearby_places_from_geocode_async(
    geocode_result: Dict,
    days: int,
    mode: str = "transit",
    pace: str = "standard",
    types: List[str] | None = None,
    destination_name: str = None,
    max_results_per_type: int = 5,
) -> List[GooglePlace]:
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
        List of GooglePlace objects found in the area
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
        # For country-scale locations, return empty list
        return []

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
    
    async def search_place_type(place_type: str) -> GooglePlacesResponse:
        """Search for a specific place type asynchronously"""
        try:
            response = await google_places_nearby_search_async(
                location=location_str,
                radius=radius_m,
                place_types=[place_type],
                max_results=max_results_per_type
            )
            return response
        except Exception:
            # Return empty GooglePlacesResponse on error
            return GooglePlacesResponse(places=[], next_page_token=None)
    
    # Run all searches in parallel
    search_results = await asyncio.gather(*[search_place_type(place_type) for place_type in types])
    
    # Process results and deduplicate
    places_results = _process_and_deduplicate_places(search_results, all_places)

    return places_results
