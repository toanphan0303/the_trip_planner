from __future__ import annotations
import math
from typing import Dict

EARTH_R_M = 6_371_000  # meters

# ---------- distance & radius helpers ----------

def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate haversine distance between two points in meters"""
    rlat1, rlng1, rlat2, rlng2 = map(math.radians, (lat1, lng1, lat2, lng2))
    dlat = rlat2 - rlat1
    dlng = rlng2 - rlng1
    a = math.sin(dlat/2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng/2)**2
    return 2 * EARTH_R_M * math.asin(math.sqrt(a))

def pick_bounds(geometry: Dict) -> Dict | None:
    """Pick bounds from geometry (bounds or viewport)"""
    return geometry.get("bounds") or geometry.get("viewport")

def base_radius_from_bounds(bounds: Dict) -> tuple[float, float, float]:
    """Calculate base radius from geocoding bounds"""
    ne, sw = bounds["northeast"], bounds["southwest"]
    lat_c = (ne["lat"] + sw["lat"]) / 2.0
    lng_c = (ne["lng"] + sw["lng"]) / 2.0
    ns_m = haversine_m(ne["lat"], lng_c, sw["lat"], lng_c)
    ew_m = haversine_m(lat_c, ne["lng"], lat_c, sw["lng"])
    R0_m = 0.5 * max(ns_m, ew_m)
    return R0_m, ns_m, ew_m

# ---------- radius calculation factors ----------

def f_days(days: int | None) -> float:
    """Enhanced duration factor with better scaling for different trip lengths"""
    d = 4 if not days or days <= 0 else days
    
    # Improved scaling: more gradual increase for longer trips
    if d <= 2:
        # Short trips: focus on immediate area
        return 0.8 + 0.2 * d
    elif d <= 7:
        # Medium trips: moderate expansion
        return 1.0 + 0.15 * (d - 2)
    else:
        # Long trips: more exploration but with diminishing returns
        return 1.75 + 0.1 * min(d - 7, 10)  # Cap at ~2.75 for very long trips

def f_mode(mode: str) -> float:
    """Transportation mode factor"""
    return {"walk": 0.6, "transit": 1.0, "car": 1.3}.get(mode, 1.0)

def f_pace(pace: str) -> float:
    """Trip pace factor"""
    return {"relaxed": 0.8, "standard": 1.0, "aggressive": 1.2}.get(pace, 1.0)

def f_destination_size(destination_name: str = None, geocode_result: Dict = None) -> float:
    """
    Dynamic destination size factor using multiple data sources.
    
    Args:
        destination_name: Name of the destination
        geocode_result: Geocoding result with bounds information
        
    Returns:
        Multiplier for radius (1.0 = default, >1.0 = larger radius needed)
    """
    if not destination_name:
        return 1.0
    
    # Method 1: Use geocoding bounds to estimate city size
    if geocode_result:
        bounds_factor = _estimate_size_from_bounds(geocode_result)
        if bounds_factor != 1.0:
            return bounds_factor
    
    # Method 2: Use destination name patterns and keywords
    name_factor = _estimate_size_from_name_patterns(destination_name)
    if name_factor != 1.0:
        return name_factor
    
    # Method 3: Fallback to simple heuristics
    return _estimate_size_from_heuristics(destination_name)

def _estimate_size_from_bounds(geocode_result: Dict) -> float:
    """Estimate city size from geocoding bounds"""
    try:
        bounds = geocode_result.get("geometry", {}).get("bounds") or geocode_result.get("geometry", {}).get("viewport")
        if not bounds:
            return 1.0
        
        # Calculate area from bounds
        ne = bounds.get("northeast", {})
        sw = bounds.get("southwest", {})
        
        if not ne or not sw:
            return 1.0
        
        # Calculate approximate area in km²
        lat_diff = ne.get("lat", 0) - sw.get("lat", 0)
        lng_diff = ne.get("lng", 0) - sw.get("lng", 0)
        
        # Rough area calculation (not precise but good for relative sizing)
        area_approx = abs(lat_diff * lng_diff) * 111 * 111  # Convert degrees to km²
        
        # Size classification based on area
        if area_approx > 5000:  # Very large metropolitan area
            return 1.8
        elif area_approx > 2000:  # Large city
            return 1.5
        elif area_approx > 500:   # Medium city
            return 1.2
        elif area_approx < 100:   # Small/compact area
            return 0.8
        else:
            return 1.0
            
    except Exception:
        return 1.0

def _estimate_size_from_name_patterns(destination_name: str) -> float:
    """Estimate size from destination name patterns and keywords"""
    destination_lower = destination_name.lower()
    
    # Megacity indicators
    megacity_indicators = [
        "greater", "metropolitan", "metro", "greater", "gtr", 
        "mega", "capital", "national capital"
    ]
    if any(indicator in destination_lower for indicator in megacity_indicators):
        return 1.8
    
    # Country/region indicators (very large)
    country_indicators = [
        "country", "nation", "state", "province", "region", "county"
    ]
    if any(indicator in destination_lower for indicator in country_indicators):
        return 2.0
    
    # Island indicators (often compact)
    island_indicators = [
        "island", "isle", "peninsula", "archipelago", "atoll"
    ]
    if any(indicator in destination_lower for indicator in island_indicators):
        return 0.7
    
    # Mountain/outdoor indicators (may need larger radius for activities)
    mountain_indicators = [
        "mountain", "peak", "alps", "himalaya", "rocky", "national park", 
        "forest", "wilderness", "nature reserve"
    ]
    if any(indicator in destination_lower for indicator in mountain_indicators):
        return 1.4
    
    # Coastal indicators (may spread along coast)
    coastal_indicators = [
        "coast", "beach", "bay", "harbor", "port", "seaside", "riviera"
    ]
    if any(indicator in destination_lower for indicator in coastal_indicators):
        return 1.3
    
    # Urban area indicators
    if "village" in destination_lower or "hamlet" in destination_lower:
        return 0.6
    elif "town" in destination_lower:
        return 0.9
    elif "city" in destination_lower:
        return 1.1
    
    return 1.0

def _estimate_size_from_heuristics(destination_name: str) -> float:
    """
    Fallback heuristics using only linguistic and structural patterns.
    No hardcoded city names - purely pattern-based detection.
    """
    destination_lower = destination_name.lower()
    
    # Multi-word destinations often indicate larger areas
    word_count = len(destination_name.split())
    if word_count >= 4:  # "Greater Tokyo Metropolitan Area" type names
        return 1.6
    elif word_count == 3:  # "New York City" type names
        return 1.3
    elif word_count == 1:  # Single word destinations often smaller
        return 0.9
    
    # Check for administrative level indicators
    admin_indicators = [
        "state", "province", "region", "county", "district", "prefecture",
        "department", "canton", "oblast", "voivodeship"
    ]
    if any(indicator in destination_lower for indicator in admin_indicators):
        return 1.5
    
    # Check for urban hierarchy indicators
    if any(indicator in destination_lower for indicator in ["capital", "metropolitan"]):
        return 1.4
    
    # Check for size-related suffixes or prefixes
    size_indicators = {
        "mega": 1.8,
        "greater": 1.6, 
        "greater metropolitan": 1.8,
        "metro": 1.5,
        "urban": 1.3,
        "downtown": 0.8,
        "center": 0.9,
        "central": 0.9,
        "old town": 0.7,
        "historic": 0.8
    }
    
    for indicator, multiplier in size_indicators.items():
        if indicator in destination_lower:
            return multiplier
    
    # Check for geographical context clues
    if any(geo in destination_lower for geo in ["bay", "harbor", "port", "coast"]):
        return 1.2  # Coastal areas may spread out
    
    # Check for tourism-related terms (often indicate smaller, focused areas)
    tourism_terms = ["resort", "beach", "spa", "hot springs", "national park"]
    if any(term in destination_lower for term in tourism_terms):
        return 0.8
    
    # Check for university towns (often medium-sized)
    if any(term in destination_lower for term in ["university", "college", "campus"]):
        return 1.1
    
    # Check for industrial/commercial indicators (often larger)
    if any(term in destination_lower for term in ["industrial", "business", "financial", "commercial"]):
        return 1.3
    
    # Default based on name length and complexity
    if len(destination_name) > 20:  # Very long names often indicate larger areas
        return 1.2
    elif len(destination_name) < 8:  # Short names often indicate smaller places
        return 0.9
    
    # Default for unknown destinations
    return 1.0

def _is_major_city(destination_name: str = None, geocode_result: Dict = None) -> bool:
    """
    Check if the destination is a major city that should use Nearby search
    even if it has large administrative bounds.
    
    Args:
        destination_name: Name of the destination
        geocode_result: Geocoding result with address components
        
    Returns:
        True if this is a major city that should use Nearby search
    """
    if not destination_name:
        return False
    
    destination_lower = destination_name.lower()
    
    # List of major cities that should use Nearby search despite large bounds
    major_cities = [
        "tokyo", "london", "paris", "new york", "los angeles", "chicago",
        "moscow", "beijing", "shanghai", "mumbai", "delhi", "mexico city",
        "sao paulo", "buenos aires", "sydney", "melbourne", "toronto",
        "vancouver", "miami", "houston", "phoenix", "philadelphia",
        "san antonio", "san diego", "dallas", "san jose", "austin",
        "jacksonville", "fort worth", "columbus", "charlotte", "san francisco",
        "indianapolis", "seattle", "denver", "washington", "boston",
        "nashville", "baltimore", "portland", "las vegas", "milwaukee",
        "albuquerque", "tucson", "fresno", "sacramento", "mesa",
        "kansas city", "atlanta", "long beach", "colorado springs", "raleigh",
        "miami", "virginia beach", "omaha", "oakland", "minneapolis",
        "tulsa", "arlington", "tampa", "new orleans", "wichita"
    ]
    
    # Check if destination name matches any major city
    for city in major_cities:
        if city in destination_lower:
            return True
    
    # Check address components for city indicators
    if geocode_result and "address_components" in geocode_result:
        for component in geocode_result["address_components"]:
            component_name = component.get("long_name", "").lower()
            component_types = component.get("types", [])
            
            # If it's a locality or administrative_area_level_1, check if it's a major city
            if any(t in component_types for t in ["locality", "administrative_area_level_1"]):
                for city in major_cities:
                    if city in component_name:
                        return True
    
    return False

def clamp_radius(r_m: float, soft_min=2_000, soft_max=30_000, hard_max=50_000) -> int:
    """Clamp radius to reasonable bounds"""
    r = max(soft_min, min(r_m, soft_max))
    return int(min(r, hard_max))

def calculate_smart_radius(
    base_radius_m: float,
    days: int,
    mode: str = "transit",
    pace: str = "standard",
    destination_name: str = None,
    geocode_result: Dict = None
) -> int:
    """
    Calculate smart radius using all available factors.
    
    Args:
        base_radius_m: Base radius from geocoding bounds (meters)
        days: Trip duration in days
        mode: Transportation mode
        pace: Trip pace
        destination_name: Destination name for size adjustment
        geocode_result: Geocoding result for bounds-based size estimation
        
    Returns:
        Calculated radius in meters
    """
    # Apply all factors
    radius_raw = base_radius_m * f_days(days) * f_mode(mode) * f_pace(pace)
    
    # Apply destination size factor if provided (with geocode data)
    if destination_name:
        radius_raw *= f_destination_size(destination_name, geocode_result)
    
    return clamp_radius(radius_raw)
