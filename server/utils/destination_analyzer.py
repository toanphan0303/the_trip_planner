"""
Destination analyzer for determining optimal search parameters
Uses LLM to analyze destination characteristics with caching
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from functools import lru_cache

logger = logging.getLogger(__name__)

# In-memory cache for radius determinations
# Key: (destination_lower, duration_days) → Value: (radius_km, characteristics)
_RADIUS_CACHE = {}


class DestinationCharacteristics(BaseModel):
    """Characteristics of a destination determined by LLM"""
    city_size: str = Field(
        description="City size: 'small' (<500k), 'medium' (500k-2M), 'large' (2M-5M), 'mega' (>5M)"
    )
    density: str = Field(
        description="POI density: 'sparse' (rural/suburban), 'moderate' (typical city), 'dense' (major tourist area), 'very_dense' (downtown/tourist hotspot)"
    )
    destination_type: str = Field(
        description="Primary type: 'urban' (city center), 'suburban', 'resort', 'rural', 'island', 'multiple_areas' (spread out attractions)"
    )
    search_radius_km: float = Field(
        description="Recommended search radius in kilometers (5-100km)",
        ge=5.0,
        le=100.0
    )
    reasoning: str = Field(
        description="Brief explanation for the recommended radius (max 2 sentences)"
    )


DESTINATION_ANALYSIS_PROMPT = """You are a travel geography expert. Analyze the destination and recommend an optimal search radius for finding points of interest.

Destination: {destination}
Trip Duration: {duration_days} days

**Your Task:**
Determine the optimal search radius (in kilometers) for POI discovery based on:

1. **City Size & Population:**
   - Small city (<500k): Typically 5-15km radius
   - Medium city (500k-2M): Typically 10-25km radius
   - Large city (2M-5M): Typically 20-40km radius
   - Mega city (>5M): Typically 30-60km radius

2. **POI Density:**
   - Sparse (rural/suburban): Larger radius needed (20-50km)
   - Moderate (typical city): Medium radius (15-30km)
   - Dense (major tourist area): Smaller radius (10-20km)
   - Very dense (downtown/hotspot): Smallest radius (5-15km)

3. **Destination Type:**
   - Urban center: Compact, smaller radius
   - Suburban: Medium radius
   - Resort/Island: Variable, depends on size
   - Rural: Larger radius needed
   - Multiple areas: Larger radius to cover spread-out attractions

4. **Trip Duration Context:**
   - Shorter trips (1-3 days): Focus on core area, smaller radius
   - Medium trips (4-7 days): Expand to nearby areas
   - Longer trips (8+ days): Include wider region for variety

**Examples:**
- "Tokyo, Japan" (5 days): Mega city, very dense, urban → 25-35km (covers multiple wards)
- "Kyoto, Japan" (3 days): Large city, dense, urban → 15-20km (compact historic areas)
- "Bali, Indonesia" (7 days): Island, multiple areas → 40-60km (Ubud, Seminyak, Uluwatu)
- "Reykjavik, Iceland" (5 days): Small city, sparse → 30-50km (includes Golden Circle)
- "Paris, France" (4 days): Mega city, very dense, urban → 15-25km (core arrondissements)
- "Grand Canyon, USA" (2 days): Rural, sparse → 50-80km (vast natural area)

Use your knowledge about "{destination}" to recommend the optimal search radius."""


def determine_search_radius(
    destination: str,
    duration_days: Optional[int] = None,
    model: str = "gemini-flash",
    use_cache: bool = True,
    geocode_result: Optional[dict] = None
) -> tuple[float, DestinationCharacteristics]:
    """
    Use LLM to determine optimal search radius based on destination characteristics.
    Results are cached by (destination, duration_days) for instant subsequent calls.
    
    Args:
        destination: Destination name (e.g., "Tokyo, Japan", "Paris, France")
        duration_days: Trip duration in days (influences radius for day trips)
        model: LLM model to use (default: "gemini-flash")
        use_cache: Whether to use cached results (default: True)
        geocode_result: Optional geocode result for smarter fallback (if LLM fails)
    
    Returns:
        Tuple of (search_radius_km, destination_characteristics)
    
    Examples:
        >>> radius, chars = determine_search_radius("Tokyo, Japan", 5)
        >>> print(f"Tokyo radius: {radius}km, density: {chars.density}")
        Tokyo radius: 30.0km, density: very_dense
        
        >>> # Second call is instant (cached)
        >>> radius, chars = determine_search_radius("Tokyo, Japan", 5)
        >>> print("Retrieved from cache!")
    """
    # Create cache key
    cache_key = _create_cache_key(destination, duration_days)
    
    # Check cache first
    if use_cache and cache_key in _RADIUS_CACHE:
        radius_km, chars = _RADIUS_CACHE[cache_key]
        logger.info(f"[determine_search_radius] 🚀 Cache hit: {destination} ({duration_days} days) → {radius_km}km")
        return radius_km, chars
    
    # Cache miss - call LLM
    logger.info(f"[determine_search_radius] 🔍 Cache miss: {destination} ({duration_days} days), calling LLM...")
    
    from models.ai_models import create_vertex_ai_model
    
    try:
        # Build prompt
        prompt = DESTINATION_ANALYSIS_PROMPT.format(
            destination=destination,
            duration_days=duration_days or "unknown"
        )
        
        # Call LLM with structured output
        llm = create_vertex_ai_model(model).with_structured_output(DestinationCharacteristics)
        response = llm.invoke(prompt)
        
        logger.info(
            f"[determine_search_radius] ✅ LLM result: {destination} → {response.search_radius_km}km "
            f"(size={response.city_size}, density={response.density}, type={response.destination_type})"
        )
        logger.info(f"[determine_search_radius] Reasoning: {response.reasoning}")
        
        # Cache the result
        if use_cache:
            _RADIUS_CACHE[cache_key] = (response.search_radius_km, response)
            logger.info(f"[determine_search_radius] 💾 Cached result for {cache_key}")
        
        return response.search_radius_km, response
        
    except Exception as e:
        logger.error(f"LLM search radius determination failed: {e}")
        
        # Fallback: Use heuristic calculation (more reliable than simple defaults)
        fallback_radius = _get_fallback_radius(
            duration_days=duration_days,
            geocode_result=geocode_result,
            destination_name=destination
        )
        
        fallback_method = "heuristic calculation" if geocode_result else "duration-based estimate"
        logger.warning(f"Using fallback radius ({fallback_method}): {fallback_radius}km")
        
        fallback_chars = DestinationCharacteristics(
            city_size="medium",
            density="moderate",
            destination_type="urban",
            search_radius_km=fallback_radius,
            reasoning=f"Fallback using {fallback_method} due to LLM error"
        )
        
        # Don't cache fallback results (they're less accurate)
        return fallback_radius, fallback_chars


def _create_cache_key(destination: str, duration_days: Optional[int]) -> str:
    """
    Create a cache key from destination and duration.
    
    Args:
        destination: Destination name
        duration_days: Trip duration
    
    Returns:
        Cache key string
    """
    # Normalize destination (lowercase, strip whitespace)
    dest_normalized = destination.lower().strip()
    days_str = str(duration_days) if duration_days else "none"
    return f"{dest_normalized}_{days_str}days"


def get_cache_stats() -> dict:
    """
    Get statistics about the cache.
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        "size": len(_RADIUS_CACHE),
        "keys": list(_RADIUS_CACHE.keys())
    }


def clear_cache():
    """Clear the radius cache."""
    global _RADIUS_CACHE
    _RADIUS_CACHE.clear()
    logger.info("[determine_search_radius] Cache cleared")


def _get_fallback_radius(
    duration_days: Optional[int] = None,
    geocode_result: Optional[dict] = None,
    destination_name: Optional[str] = None
) -> float:
    """
    Get fallback radius using heuristic calculation when LLM fails.
    
    Uses the existing _calculate_search_radius logic as a reliable fallback.
    
    Args:
        duration_days: Trip duration in days
        geocode_result: Geocoding result with bounds (optional)
        destination_name: Destination name for size estimation (optional)
    
    Returns:
        Search radius in kilometers
    """
    # Use the proven heuristic calculation as fallback
    from utils.google_map_utils import _calculate_search_radius
    
    # If we have geocode result, use full heuristic calculation
    if geocode_result:
        radius_m = _calculate_search_radius(
            geocode_result=geocode_result,
            days=duration_days or 4,
            mode="transit",
            pace="standard",
            destination_name=destination_name
        )
        return radius_m / 1000.0  # Convert meters to kilometers
    
    # Minimal fallback if no geocode data available
    # Use simplified heuristic based on duration only
    if duration_days is None:
        return 20.0
    
    if duration_days <= 2:
        return 15.0
    elif duration_days <= 5:
        return 25.0
    elif duration_days <= 10:
        return 35.0
    else:
        return 45.0

