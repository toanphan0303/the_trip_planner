from langchain_core.tools import tool
from service_api.google_api import google_places_search_text, google_geocode
from models.args_model import PlanTripForDestinationsArgs
from error.trip_planner_errors import UserClarificationError
from utils.radius import search_nearby_places_from_geocode

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
    try:
        duration_days = kwargs['duration_days']
        destination = kwargs['destination']
        response = google_places_search_text(
            query=destination,
            max_results=10
        )
        
        # Format the response for better readability using Google's built-in models
        if len(response.places) > 1:
            option_places = "\n".join([place.get("displayName", {}).get("text", "") for place in response.places])
            raise UserClarificationError(clarification_questions=["Please provide more information about the destination ", option_places])

        place = response.places[0]
        address = place.get("formattedAddress", "")

        # Get geocoding response and extract the first result
        geocode_response = google_geocode(address)
        if not geocode_response.get("results"):
            return f"No geocoding results found for address: {address}"
        
        # Use the first geocoding result
        geocode_result = geocode_response["results"][0]
        nearby_places = search_nearby_places_from_geocode(geocode_result, days=duration_days, mode="transit", pace="standard")

        return nearby_places

        
    
    except Exception as e:
        return f"Error searching for places: {str(e)}"

