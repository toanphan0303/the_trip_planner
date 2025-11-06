from langchain_core.tools import tool
from service_api.google_api import google_places_search_text, google_geocode
from models.args_model import PlanTripForDestinationsArgs
from utils.google_map_utils import search_nearby_places_from_geocode
from utils.utils import normalize_places_and_events, enhance_clusters_with_yelp_data
from utils.cluster_locations import cluster_and_anchor_pois
# Note: User profile evaluation temporarily disabled - mock profiles have been removed
# from llm.location_preference_evaluation import (
#     evaluate_family_travel_preferences_batched,
#     evaluate_family_restaurant_preferences_batched
# )
# from user_profile.models import TravelPreference


@tool(args_schema=PlanTripForDestinationsArgs)
def plan_trip_for_destinations(**kwargs) -> str:
    """
    Plan a comprehensive list of places for any destination. This tool is responsible for discovering and curating places including:

    - Finding diverse types of places (restaurants, attractions, hotels, shopping, entertainment, cultural sites)
    - Providing detailed information about each place (ratings, addresses, locations, types, price levels)
    - Creating a comprehensive list of places to visit based on destination and preferences
    - Offering practical place information for trip planning

    Use this tool when users ask about:
    - "plan a trip to [destination]"
    - "places to visit in [location]"
    - "what places are in [city]"
    - "travel recommendations for [destination]"
    - "things to do in [location]"
    - "where to go in [destination]"

    Returns:
        Comprehensive list of places with detailed information including names, addresses, ratings, types, locations, price levels, business status, and websites
    """
    return "This tool is not implemented yet."