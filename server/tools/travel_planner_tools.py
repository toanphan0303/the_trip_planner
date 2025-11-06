from langchain_core.tools import tool
from logger import get_logger
from typing import Dict, Any

from user_profile.ephemeral import PreferenceOverride
from user_profile.ephemeral.override_parser import get_preferences_from_message
from state import TravelPlannerState, TripState, generate_trip_id
from utils.google_map_utils import search_nearby_places_from_geocode
from models.tools_args_model import SetTravelStyleArgs, UpsertPreferenceArgs, GeocodeDestinationArgs, SetDurationDaysArgs
from service_api.google_api import google_places_search_text, google_geocode
from utils.destination_radius_calculator import determine_search_radius
from user_profile.models import TravelStyle
from error.trip_planner_errors import ToolExecutionError
from constant.place_types import PlaceTypes
from user_profile.database import get_user_profile_db
from utils.cluster_locations import cluster_and_anchor_pois
from utils.location_user_preference_evaluator import evaluate_locations
logger = get_logger(__name__)


@tool(args_schema=SetTravelStyleArgs)
def set_travel_style(state: TravelPlannerState, **kwargs) -> Dict[str, Any]:
    """
    Set the current travel style for this trip.
    
    Use when user mentions their travel type:
    - "I'm traveling with family" → family
    - "Solo trip" → solo  
    - "Romantic getaway with my wife" → couple
    - "Group vacation with friends" → group
    
    Args:
        state: Graph state (auto-injected)
        travel_style: Travel style string ('family', 'solo', 'couple', 'group')
        
    Returns:
        Dict with current_travel_style update
    """
    travel_style_str = kwargs.get("travel_style")
    
    try:
        # Validate and convert to enum
        travel_style = TravelStyle(travel_style_str)
        
        logger.info(f"Set travel style to: {travel_style.value}")
        
        return {
            "current_travel_style": travel_style
        }
        
    except ValueError:
        logger.error(f"Invalid travel style: {travel_style_str}")
        return {"error": "Invalid travel style. Must be one of: family, solo, couple, group"}

@tool(args_schema=SetDurationDaysArgs)
def set_duration_days(state: TravelPlannerState, **kwargs) -> Dict[str, Any]:
    """
    Set the duration of the trip in days.
    """
    duration_days = kwargs.get("duration_days")
    return {
        "duration_days": duration_days
    }


@tool(args_schema=UpsertPreferenceArgs)  
def upsert_preference_override(state: TravelPlannerState, **kwargs) -> Dict[str, Any]:
    """
    Save or update user preferences for this trip using LLM to parse user message.
    
    Use when user mentions specific preferences:
    - Food: "I want vegetarian food", "love Italian cuisine", "no spicy food", "cheap eats"
    - Activities: "prefer museums", "love hiking", "skip nightlife", "enjoy shopping"
    - Stay: "need WiFi", "want a pool", "no hostels", "prefer hotels"
    
    The AI just needs to pass the user's message - an LLM will extract the preferences.
    
    Args:
        state: Graph state (auto-injected)
        user_message: User's message containing preferences
        travel_style: Optional travel style (uses current if not provided)
        
    Returns:
        Dict with preference_overrides update
    """
    user_id = state.get("user_id", "anonymous")
    user_message = kwargs.get("user_message")
    
    # Get or use current travel style
    travel_style_str = kwargs.get("travel_style")
    if travel_style_str:
        travel_style = TravelStyle(travel_style_str)
    else:
        travel_style = state.get("current_travel_style") or TravelStyle.FAMILY

    try:
        result = get_preferences_from_message(
            message=user_message,
            travel_style=travel_style
        )
        
        if not result or not result.has_override:
            logger.info("No preferences detected in message")
            return {"error": "No preferences detected"}
        
        new_override = PreferenceOverride(
            user_id=user_id,
            food=result.food,
            stay=result.stay,
            travel=result.travel
        )
        
        return {
            "preference_overrides": {travel_style: new_override},
            "current_travel_style": travel_style
        }
        
    except Exception as e:
        logger.error(f"Failed to upsert preferences: {e}")
        return {"error": f"Failed to save preferences: {str(e)}"}



@tool(args_schema=GeocodeDestinationArgs)
def geocode_destination(state: TravelPlannerState, **kwargs) -> Dict[str, Any]:
    """
    Geocode a destination and update trip with location details.
    Use when user mentions a new trip destination.
    """
    destination = kwargs.get("destination")
    is_new_trip = kwargs.get("is_new_trip", False)
    
    try:
        # Search for destination
        response = google_places_search_text(query=destination, max_results=5)
        if not response.places:
            return {"error": f"Destination '{destination}' not found"}
        
        response.handle_multiple_places()
        place = response.places[0]
        
        # Geocode the address
        geocode_response = google_geocode(place.formatted_address)
        if not geocode_response.get("results"):
            return {"error": f"Failed to geocode '{destination}'"}
        
        geocode_result = geocode_response["results"][0]
    
        
        if is_new_trip:
            new_trip = TripState(
                trip_id=generate_trip_id(place.formatted_address),
                formatted_address=place.formatted_address,
                geocode_result=geocode_result,
            )
            logger.info(f"Started new trip to {destination}")
            return {
                "trip_data": {
                    "current_trip": new_trip
                }
            }
        else:
            # Update current trip (keep same trip_id to merge fields)
            trip_data = state.get("trip_data") or {}
            current = trip_data.get("current_trip")
            
            if current:
                # Partial update - keep same trip_id to trigger merge
                updated_trip = TripState(
                    trip_id=current.trip_id,  # Same ID = merge
                    formatted_address=place.formatted_address,
                    geocode_result=geocode_result,
                )
            else:
                # No current trip - create new one
                updated_trip = TripState(
                    formatted_address=place.formatted_address,
                    geocode_result=geocode_result,
                )
            
            return { 
                "trip_data": { 
                    "current_trip": updated_trip
                }
            }
        
    except Exception as e:
        logger.error(f"Failed to geocode destination: {e}")
        return {"error": f"Failed to geocode '{destination}': {str(e)}"}


@tool
def search_nearby_places(state: TravelPlannerState, **kwargs) -> Dict[str, Any]:
    """
    This tool is used to search for nearby places for a destination.
    
    It automatically determines the optimal search radius based on destination characteristics
    (city size, density, type) using LLM analysis.
    """
    current_trip = state.get("trip_data").get("current_trip")

    if not current_trip or not current_trip.geocode_result:
        raise ToolExecutionError("No current trip found or geocoding result found, need to call geocode_destination tool to get the current trip")
    try:        
        search_radius_km = determine_search_radius(
            destination=current_trip.formatted_address,
            duration_days=current_trip.duration_days,
            geocode_result=current_trip.geocode_result
        )
        logger.info(f"Determined search radius: {current_trip.formatted_address} → {search_radius_km}km")
        
        # Step 2: Get user preferences
        user_id = state.get("user_id")
        if user_id:
            user_preference = get_user_profile_db().get_user_preferences(user_id)
        else:
            user_preference = None
        
        # Get preference override for current travel style
        preference_overrides = state.get("preference_overrides") or {}
        ephemeral_override = preference_overrides.get(current_trip.travel_style)
        
        # Step 3: Select place types
        place_types = PlaceTypes.select_types_for_user(
            user_preference=user_preference,
            travel_style=current_trip.travel_style,
            destination=current_trip.formatted_address,
            ephemeral_override=ephemeral_override,
            duration_days=current_trip.duration_days,
        )
        logger.info(f"Selected {len(place_types)} place types: {place_types}")
        
        # Step 4: Search for POIs with dynamic radius
        pois = search_nearby_places_from_geocode(
            geocode_result=current_trip.geocode_result,
            days=current_trip.duration_days,
            mode="transit",
            pace="standard",
            place_types=place_types,
            use_grid_search=False,
            search_radius_km=search_radius_km,  # Use LLM-determined radius
        )
        logger.info(f"Found {len(pois)} nearby places within {search_radius_km}km radius")
        
        # Convert GooglePlace objects to dicts for TripState
        pois_dicts = [poi.model_dump() if hasattr(poi, 'model_dump') else poi for poi in pois]
        
        trip_id = current_trip.trip_id
        return {
            "trip_data": {
                "current_trip": TripState(
                    trip_id=trip_id,
                    search_radius_km=search_radius_km,  # Store for clustering
                    pois=pois_dicts
                )
            }
        }
    except Exception as e:
        logger.error(f"Failed to search for nearby places: {e}")
        raise ToolExecutionError(f"Failed to search for nearby places: {str(e)}")

@tool
def cluster_places(state: TravelPlannerState, **kwargs) -> Dict[str, Any]:
    """
    This tool is used to cluster places for a destination for a desired number of days.
    
    Uses the same search radius that was determined during POI search for consistent
    geographic scoping.
    """
    current_trip = state.get("trip_data").get("current_trip")
    destination = current_trip.formatted_address
    duration_days = current_trip.duration_days
    pois = current_trip.pois
    
    search_radius_km = current_trip.search_radius_km
    if search_radius_km is None:
        search_radius_km = determine_search_radius(
            destination=destination,
            duration_days=duration_days,
            geocode_result=current_trip.geocode_result
        )
        logger.warning(f"search_radius_km not found in trip state, determined: {search_radius_km}km")
    
    logger.info(f"Clustering {len(pois)} POIs with {search_radius_km}km radius for {duration_days} days")
    
    clusters = cluster_and_anchor_pois(
        pois=pois,
        search_radius_km=search_radius_km,  # Use consistent radius
        target_clusters=duration_days,
        anchor_method="centroid",
        max_pois_per_cluster=40,
    )
    return {
        "clusters": clusters
    }

@tool
def filter_places_by_preferences(state: TravelPlannerState, **kwargs) -> Dict[str, Any]:
    """
    This tool is used to filter places by user preferences.
    """
    current_trip = state.get("trip_data").get("current_trip")
    pois = current_trip.pois
    user_preference = state.get("user_preference")
    preference_overrides = state.get("preference_overrides")
    pois_preference_evaluated = evaluate_locations(pois=pois, travel_style=current_trip.travel_style, user_preference=user_preference, preference_overrides=preference_overrides)
    return { ""
        "trip_data": {
            "current_trip": TripState(
                pois_preference_evaluated=pois_preference_evaluated
            )
        }
    }

