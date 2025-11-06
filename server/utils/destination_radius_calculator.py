"""
Destination Radius Calculator

Determines optimal search radius for POI discovery and clustering using:
1. LLM analysis of destination characteristics (primary)
2. Heuristic calculation with geocode bounds (fallback)
3. Duration-based estimates (last resort)

Results are cached in MongoDB by (destination, duration_days) for instant subsequent calls.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from cache.mongo_db_cache import get_mongo_cache

logger = logging.getLogger(__name__)


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
    duration_days: int,
    geocode_result: dict,
    model: str = "gemini-flash",
    use_cache: bool = True
) -> float:
    """
    Use LLM to determine optimal search radius based on destination characteristics.
    Results are cached in MongoDB by (destination, duration_days) for instant subsequent calls.
    
    Args:
        destination: Destination name (e.g., "Tokyo, Japan", "Paris, France")
        duration_days: Trip duration in days (required)
        geocode_result: Geocoding result with bounds (required for fallback)
        model: LLM model to use (default: "gemini-flash")
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        Search radius in kilometers (float)
    
    Examples:
        >>> radius = determine_search_radius(
        ...     "Tokyo, Japan", 
        ...     duration_days=5,
        ...     geocode_result=geocode_data
        ... )
        >>> print(f"Tokyo radius: {radius}km")
        Tokyo radius: 30.0km
        
        >>> # Second call is instant (cached from MongoDB)
        >>> radius = determine_search_radius("Tokyo, Japan", 5, geocode_data)
        >>> print(f"Cached: {radius}km")
    """
    cache = get_mongo_cache()
    cache_type = "destination_radius"
    
    # Normalize cache key
    cache_key_dest = destination.lower().strip()
    cache_key_days = duration_days
    
    # Check MongoDB cache first
    if use_cache:
        cached_result = cache.get(cache_type, cache_key_dest, cache_key_days)
        if cached_result is not None:
            try:
                # Extract radius from cached result
                radius_km = cached_result.get('search_radius_km')
                if radius_km:
                    logger.info(f"[determine_search_radius] 🚀 MongoDB cache hit: {destination} ({duration_days} days) → {radius_km}km")
                    return radius_km
            except Exception as e:
                logger.warning(f"Failed to get radius from cache: {e}, proceeding with LLM call")
                # Continue to LLM call if cache data is corrupted
    
    # Cache miss - call LLM
    logger.info(f"[determine_search_radius] 💾 MongoDB cache miss: {destination} ({duration_days} days), calling LLM...")
    
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
        
        # Cache the result in MongoDB
        if use_cache:
            cache_data = response.model_dump()  # Convert Pydantic model to dict
            cache.set(cache_type, cache_data, cache_key_dest, cache_key_days)
            logger.info(f"[determine_search_radius] ✅ Cached to MongoDB: destination={cache_key_dest}, days={cache_key_days}")
        
        return response.search_radius_km
        
    except Exception as e:
        logger.error(f"LLM search radius determination failed: {e}")
        
        # Fallback: Use proven heuristic calculation
        from utils.google_map_utils import _calculate_search_radius
        
        try:
            radius_m = _calculate_search_radius(
                geocode_result=geocode_result,
                days=duration_days,
                mode="transit",
                pace="standard",
                destination_name=destination
            )
            fallback_radius_km = radius_m / 1000.0  # Convert to kilometers
            
            logger.warning(f"Using fallback heuristic calculation: {fallback_radius_km}km")
            
            # Cache fallback results for consistency
            if use_cache:
                # Store as DestinationCharacteristics for consistency
                fallback_data = {
                    "city_size": "medium",
                    "density": "moderate",
                    "destination_type": "urban",
                    "search_radius_km": fallback_radius_km,
                    "reasoning": "Fallback using heuristic calculation due to LLM error"
                }
                cache.set(cache_type, fallback_data, cache_key_dest, cache_key_days)
                logger.info(f"[determine_search_radius] ✅ Cached fallback to MongoDB: destination={cache_key_dest}, days={cache_key_days}")
            
            return fallback_radius_km
            
        except Exception as fallback_error:
            logger.error(f"Fallback calculation also failed: {fallback_error}")
            raise RuntimeError(f"Both LLM and heuristic fallback failed for {destination}")

