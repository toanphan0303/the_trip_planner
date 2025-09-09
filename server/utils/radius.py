from __future__ import annotations
import math
from typing import Dict, List
from service_api.google_api import google_places_nearby_search

EARTH_R_M = 6_371_000  # meters

# ---------- distance & radius helpers ----------

def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    rlat1, rlng1, rlat2, rlng2 = map(math.radians, (lat1, lng1, lat2, lng2))
    dlat = rlat2 - rlat1
    dlng = rlng2 - rlng1
    a = math.sin(dlat/2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng/2)**2
    return 2 * EARTH_R_M * math.asin(math.sqrt(a))

def pick_bounds(geometry: Dict) -> Dict | None:
    return geometry.get("bounds") or geometry.get("viewport")

def base_radius_from_bounds(bounds: Dict) -> tuple[float, float, float]:
    ne, sw = bounds["northeast"], bounds["southwest"]
    lat_c = (ne["lat"] + sw["lat"]) / 2.0
    lng_c = (ne["lng"] + sw["lng"]) / 2.0
    ns_m = haversine_m(ne["lat"], lng_c, sw["lat"], lng_c)
    ew_m = haversine_m(lat_c, ne["lng"], lat_c, sw["lng"])
    R0_m = 0.5 * max(ns_m, ew_m)
    return R0_m, ns_m, ew_m

def f_days(days: int | None) -> float:
    d = 4 if not days or days <= 0 else days
    val = 0.9 + 0.35 * math.log2(d + 1.0)
    return min(val, 1.9)

def f_mode(mode: str) -> float:
    return {"walk": 0.6, "transit": 1.0, "car": 1.3}.get(mode, 1.0)

def f_pace(pace: str) -> float:
    return {"relaxed": 0.9, "standard": 1.0, "aggressive": 1.2}.get(pace, 1.0)

def clamp_radius(r_m: float, soft_min=2_000, soft_max=30_000, hard_max=50_000) -> int:
    r = max(soft_min, min(r_m, soft_max))
    return int(min(r, hard_max))

# ---------- main planner helper ----------

def search_nearby_places_from_geocode(
    geocode_result: Dict,
    days: int,
    mode: str = "transit",
    pace: str = "standard",
    types: List[str] | None = None,
) -> Dict:
    """
    Search for nearby places around a geocoded location using Google Places API.
    
    Dynamically calculates search radius based on trip duration, transportation mode,
    and travel pace. For city-scale locations, performs nearby searches for multiple
    place types. For country-scale locations, returns a text search query.
    
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
        too_big = max(ns_m, ew_m) > 120_000  # ~120 km heuristic
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

    # Dynamic radius for city scale
    radius_raw = R0_m * f_days(days) * f_mode(mode) * f_pace(pace)
    radius_m = clamp_radius(radius_raw)

    # Default categories to seed diversity (1 request per type)
    if not types:
        types = [
            "tourist_attraction", 
            # "museum", "park", "zoo", "aquarium", "art_gallery", "amusement_park", "shopping_mall", "restaurant", "cafe"
        ]

    lat, lng = center
    location_str = f"{lat:.7f},{lng:.7f}"
    
    # Call Google Places API for each type
    places_results = []
    for place_type in types:
        try:
            response = google_places_nearby_search(
                location=location_str,
                radius=radius_m,
                place_type=place_type,
                max_results=20
            )
            places_results.append({
                "type": place_type,
                "places": response.places
            })
        except Exception as e:
            # Log error but continue with other types
            places_results.append({
                "type": place_type,
                "error": str(e),
                "places": []
            })

    return {
        "center": center,
        "radius_m": radius_m,
        "places_results": places_results,
        "textsearch_query": None,
        "debug": {"ns_m": int(ns_m), "ew_m": int(ew_m), "R0_m": int(R0_m), "scale": "city/neighborhood"},
    }