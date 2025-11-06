"""
Google Maps utilities for place search and geocoding operations
"""

import asyncio
import math
from typing import Dict, List, Tuple, Optional
from .radius import calculate_smart_radius, pick_bounds, base_radius_from_bounds, _is_major_city
from service_api.google_api import google_places_nearby_search_async
from models.google_map_models import GooglePlacesResponse, GooglePlace


# ============================================================================
# Place Processing & Deduplication
# ============================================================================

def _process_and_deduplicate_places(
    search_results: List[GooglePlacesResponse], 
    all_places: Dict
) -> List[GooglePlace]:
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


# ============================================================================
# Location Validation & Setup
# ============================================================================

def _extract_location_info(geocode_result: Dict) -> Tuple[float, float, str]:
    """
    Extract location coordinates from geocoding result.
    
    Args:
        geocode_result: Geocoding result from Google API
        
    Returns:
        Tuple of (latitude, longitude, location_string)
    """
    geometry = geocode_result["geometry"]
    lat = geometry["location"]["lat"]
    lng = geometry["location"]["lng"]
    location_str = f"{lat:.7f},{lng:.7f}"
    
    return lat, lng, location_str


def _check_if_too_big_for_nearby_search(
    geocode_result: Dict,
    destination_name: Optional[str]
) -> bool:
    """
    Check if the destination is too large for Nearby Search API.
    Country-scale locations should use Text Search instead.
    
    Args:
        geocode_result: Geocoding result from Google API
        destination_name: Name of destination
        
    Returns:
        True if too big for nearby search, False otherwise
    """
    geometry = geocode_result["geometry"]
    bounds = pick_bounds(geometry)
    
    if not bounds:
        return False
    
    R0_m, ns_m, ew_m = base_radius_from_bounds(bounds)
    
    # Allow major cities even if their bounds are large
    is_major_city = _is_major_city(destination_name, geocode_result)
    
    # ~120 km heuristic for max dimension
    too_big = max(ns_m, ew_m) > 120_000 and not is_major_city
    
    return too_big


def _calculate_search_radius(
    geocode_result: Dict,
    days: int,
    mode: str,
    pace: str,
    destination_name: Optional[str]
) -> float:
    """
    Calculate optimal search radius based on trip parameters.
    
    Args:
        geocode_result: Geocoding result from Google API
        days: Trip duration in days
        mode: Transportation mode ("walk", "transit", "car")
        pace: Trip pace ("relaxed", "standard", "aggressive")
        destination_name: Name of destination
        
    Returns:
        Search radius in meters
    """
    geometry = geocode_result["geometry"]
    bounds = pick_bounds(geometry)
    
    # Calculate base radius from bounds, or use default
    if bounds:
        R0_m, _, _ = base_radius_from_bounds(bounds)
    else:
        R0_m = 10_000  # 10km default
    
    # Smart radius calculation with destination awareness
    radius_m = calculate_smart_radius(
        R0_m, 
        days, 
        mode, 
        pace, 
        destination_name, 
        geocode_result
    )
    
    return radius_m



# ============================================================================
# Grid Search Functions
# ============================================================================

def _calculate_dynamic_grid_size(
    radius_m: float,
    days: int,
    destination_name: Optional[str] = None
) -> int:
    """
    Dynamically calculate optimal grid size based on search parameters.
    
    Larger areas, longer trips, and major cities benefit from larger grids.
    
    Args:
        radius_m: Search radius in meters
        days: Trip duration in days
        destination_name: Destination name for city-specific adjustments
        
    Returns:
        Grid size (1 = no grid, 2 = 2x2, 3 = 3x3, etc.)
    """
    # Base grid size on search radius
    if radius_m < 5000:  # < 5km - very focused search
        base_grid = 1  # No grid needed
    elif radius_m < 10000:  # 5-10km - small city area
        base_grid = 2  # 2x2 grid (4 cells)
    elif radius_m < 20000:  # 10-20km - medium city
        base_grid = 2  # 2x2 grid
    elif radius_m < 40000:  # 20-40km - large city
        base_grid = 3  # 3x3 grid (9 cells)
    else:  # > 40km - metropolitan area
        base_grid = 3  # 3x3 grid
    
    # Adjust for trip duration
    if days >= 7:
        # Longer trips benefit from more coverage
        base_grid = min(base_grid + 1, 3)  # Cap at 3x3
    elif days <= 2:
        # Short trips need less coverage
        base_grid = max(base_grid - 1, 1)  # Minimum 1 (no grid)
    
    # Adjust for major cities (known to have high POI density)
    major_cities = [
        'tokyo', 'osaka', 'kyoto', 'new york', 'london', 'paris', 
        'singapore', 'hong kong', 'bangkok', 'seoul', 'shanghai',
        'beijing', 'los angeles', 'san francisco', 'chicago'
    ]
    
    if destination_name and any(city in destination_name.lower() for city in major_cities):
        # Major cities have high density - can use larger grid
        base_grid = min(base_grid + 1, 3)
    
    print(f"🔲 Dynamic grid size: {base_grid}x{base_grid} (radius: {radius_m}m, days: {days})")
    
    return base_grid


def _calculate_grid_centers(
    center_lat: float,
    center_lng: float,
    base_radius_m: float,
    grid_size: int
) -> List[Tuple[float, float]]:
    """
    Calculate grid cell centers for overlapping searches.
    
    Creates a grid of search points with 20% overlap to ensure complete coverage.
    
    Args:
        center_lat: Center latitude
        center_lng: Center longitude
        base_radius_m: Base search radius in meters
        grid_size: Grid dimensions (2 = 2x2 = 4 cells, 3 = 3x3 = 9 cells)
        
    Returns:
        List of (lat, lng) tuples for each grid cell center
    """
    if grid_size == 1:
        # No grid - return just the center point
        return [(center_lat, center_lng)]
    
    grid_centers = []
    
    # Calculate offset distance for each grid cell
    offset_m = base_radius_m / grid_size
    
    for i in range(grid_size):
        for j in range(grid_size):
            # Calculate offset in degrees
            # 1 degree latitude ≈ 111,000 meters
            # 1 degree longitude ≈ 111,000 * cos(latitude) meters
            
            lat_offset_deg = ((i - grid_size/2 + 0.5) * offset_m) / 111000
            lng_offset_deg = ((j - grid_size/2 + 0.5) * offset_m) / (111000 * math.cos(math.radians(center_lat)))
            
            grid_lat = center_lat + lat_offset_deg
            grid_lng = center_lng + lng_offset_deg
            
            grid_centers.append((grid_lat, grid_lng))
    
    return grid_centers


async def _execute_grid_search(
    center_lat: float,
    center_lng: float,
    radius_m: float,
    place_types: List[str],
    max_results_per_type: int,
    grid_size: int
) -> List[GooglePlacesResponse]:
    """
    Execute grid-based search for better coverage.
    
    Divides the search area into a grid of overlapping circles and searches each cell.
    This bypasses Google's 20-result-per-call limitation.
    
    Args:
        center_lat: Center latitude
        center_lng: Center longitude
        radius_m: Base search radius in meters
        place_types: List of place types to search
        max_results_per_type: Max results per type per grid cell (capped at 20)
        grid_size: Grid dimensions (2 = 2x2 = 4 cells, 3 = 3x3 = 9 cells)
        
    Returns:
        List of GooglePlacesResponse objects from all grid cells
    """
    # Calculate grid cell centers
    grid_centers = _calculate_grid_centers(center_lat, center_lng, radius_m, grid_size)
    
    # Calculate cell radius (smaller than base, with 20% overlap)
    cell_radius_m = radius_m / grid_size * 1.2
    
    print(f"🔍 Grid search: {grid_size}x{grid_size} = {len(grid_centers)} cells")
    print(f"   📍 Base radius: {radius_m}m → Cell radius: {cell_radius_m:.0f}m")
    print(f"   🎯 Expected: ~{len(grid_centers) * len(place_types) * 20} raw results (before dedup)")
    
    # Create search tasks for each grid cell × each place type
    tasks = []
    for grid_idx, (grid_lat, grid_lng) in enumerate(grid_centers):
        location_str = f"{grid_lat:.7f},{grid_lng:.7f}"
        
        for place_type in place_types:
            task = _search_single_place_type(
                location_str,
                cell_radius_m,
                place_type,
                max_results_per_type
            )
            tasks.append(task)
    
    print(f"   🚀 Executing {len(tasks)} parallel API calls...")
    
    # Execute all searches in parallel
    search_results = await asyncio.gather(*tasks)
    
    return search_results


# ============================================================================
# Async Search Execution
# ============================================================================

async def _search_single_place_type(
    location_str: str,
    radius_m: float,
    place_type: str,
    max_results: int
) -> GooglePlacesResponse:
    """
    Search for a single place type asynchronously.
    
    Args:
        location_str: Location string "lat,lng"
        radius_m: Search radius in meters
        place_type: Place type to search for
        max_results: Maximum results to return
        
    Returns:
        GooglePlacesResponse with search results
    """
    try:
        response = await google_places_nearby_search_async(
            location=location_str,
            radius=radius_m,
            place_types=[place_type],
            max_results=max_results
        )
        return response
    except Exception as e:
        print(f"⚠️  Search failed for type '{place_type}': {e}")
        # Return empty response on error
        return GooglePlacesResponse(places=[], next_page_token=None)


async def _execute_parallel_searches(
    location_str: str,
    radius_m: float,
    place_types: List[str],
    max_results_per_type: int
) -> List[GooglePlacesResponse]:
    """
    Execute searches for multiple place types in parallel.
    
    Args:
        location_str: Location string "lat,lng"
        radius_m: Search radius in meters
        place_types: List of place types to search
        max_results_per_type: Max results per type
        
    Returns:
        List of GooglePlacesResponse objects
    """
    # Create search tasks for all place types
    tasks = [
        _search_single_place_type(
            location_str, 
            radius_m, 
            place_type, 
            max_results_per_type
        )
        for place_type in place_types
    ]
    
    # Execute all searches in parallel
    search_results = await asyncio.gather(*tasks)
    
    return search_results


# ============================================================================
# Main Search Function
# ============================================================================

def search_nearby_places_from_geocode(
    geocode_result: Dict,
    days: int,
    place_types: List[str],
    mode: str = "transit",
    pace: str = "standard",
    destination_name: Optional[str] = None,
    max_results_per_type: int = 20,
    use_grid_search: bool = False,
    search_radius_km: Optional[float] = None,
) -> List[GooglePlace]:
    """
    Search for nearby places around a geocoded location using Google Places API.
    
    This function orchestrates the entire search process:
    1. Validates the location isn't too large for Nearby Search
    2. Calculates optimal search radius based on trip parameters (or uses provided radius)
    3. Determines place types to search
    4. Dynamically calculates grid size (if grid search enabled)
    5. Executes parallel searches (with or without grid)
    6. Deduplicates and returns results
    
    Args:
        geocode_result: Geocoding result from Google API
        days: Trip duration in days
        mode: Transportation mode ("walk", "transit", "car")
        pace: Trip pace ("relaxed", "standard", "aggressive")
        types: List of place types to search for (optional)
        destination_name: Name of destination for smart radius calculation
        max_results_per_type: Maximum number of results per place type (capped at 20 by Google API)
        use_grid_search: Whether to use grid-based search for more results (default: True)
        search_radius_km: Optional override for search radius in kilometers (default: None, auto-calculated)
        
    Returns:
        List of GooglePlace objects found in the area
    """
    # Step 1: Check if location is too large for Nearby Search
    if _check_if_too_big_for_nearby_search(geocode_result, destination_name):
        print("⚠️  Destination too large for Nearby Search, use Text Search instead")
        return []
    
    # Step 2: Extract location coordinates
    lat, lng, location_str = _extract_location_info(geocode_result)
    
    # Step 3: Calculate or use provided search radius
    if search_radius_km is not None:
        # Use LLM-determined radius (convert km to meters)
        radius_m = int(search_radius_km * 1000)
        print(f"📍 Using LLM-determined radius: {search_radius_km}km ({radius_m}m)")
    else:
        # Fallback to heuristic calculation
        radius_m = _calculate_search_radius(
            geocode_result,
            days,
            mode,
            pace,
            destination_name
        )
        print(f"📍 Using calculated radius: {radius_m/1000:.1f}km ({radius_m}m)")

    
    # Log search parameters
    print(f"Searching for places in {location_str} with radius {radius_m} and types {place_types}")
    
    # Step 5: Calculate dynamic grid size and execute searches
    async def run_searches():
        if use_grid_search:
            # Calculate optimal grid size dynamically
            grid_size = _calculate_dynamic_grid_size(radius_m, days, destination_name)
            
            # Execute grid search
            return await _execute_grid_search(
                lat,
                lng,
                radius_m,
                place_types,
                max_results_per_type,
                grid_size
            )
        else:
            # Execute simple single-point search
            return await _execute_parallel_searches(
                location_str,
                radius_m,
                place_types,
                max_results_per_type
            )
    
    search_results = asyncio.run(run_searches())
    
    # Step 6: Deduplicate and return results
    all_places = {}  # Track unique places by ID
    places_results = _process_and_deduplicate_places(search_results, all_places)
    
    print(f"✅ Search complete: {len(places_results)} unique places found")
    
    return places_results

