import json
from langchain_core.tools import tool
from service_api.google_api import google_places_search_text, google_geocode
from models.args_model import PlanTripForDestinationsArgs
from error.trip_planner_errors import UserClarificationError
from utils.google_map_utils import search_nearby_places_from_geocode
from utils.utils import normalize_places_and_events, enhance_clusters_with_yelp_data, enhance_clusters_with_foursquare_data
from utils.cluster_locations import cluster_and_anchor_pois, calculate_smart_max_results

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
        max_results = kwargs.get('max_results', 50)  # Default to 10, but allow customization
        
        response = google_places_search_text(
            query=destination,
            max_results=max_results
        )
        
        # Response is now always a GooglePlacesResponse object
        places = response.places
        
        # Format the response for better readability using Google's built-in models
        if len(places) > 1:
            option_places = "\n".join([place.get("displayName", {}).get("text", "") for place in places])
            raise UserClarificationError(clarification_questions=["Please provide more information about the destination ", option_places])

        place = places[0]
        address = place.get("formattedAddress", "")

        # Get geocoding response and extract the first result
        geocode_response = google_geocode(address)
        if not geocode_response.get("results"):
            return f"No geocoding results found for address: {address}"
        
        # Use the first geocoding result
        geocode_result = geocode_response["results"][0]
        
        # Calculate smart max_results now that we have geocode information
        max_results = calculate_smart_max_results(
            days=duration_days,
            destination_name=destination,
            geocode_result=geocode_result
        )
        
        nearby_places = search_nearby_places_from_geocode(
            geocode_result, 
            days=duration_days, 
            mode="transit", 
            pace="standard",
            destination_name=destination,  # Pass destination for smart radius calculation
            max_results_per_type=max_results  # Use smart or user-provided max_results
        )
        print("Number of nearby places: ", len(nearby_places))
        
        # Convert nearby_places to PointOfInterest objects
        point_of_interest_search_result = normalize_places_and_events(places_data=nearby_places)
        
        clusters, anchors = cluster_and_anchor_pois(
            pois=point_of_interest_search_result.items,  # Use items from search result
            search_radius_km=point_of_interest_search_result.search_radius_km,
            # Smart parameters will be automatically calculated based on dataset characteristics
            # and trip duration to create one cluster per day
            use_smart_params=True,
            target_clusters=duration_days,  # Force one cluster per day
            anchor_method="centroid"
        )
        
        # Enhance restaurants with Yelp data AFTER clustering and filtering
        # This reduces API calls by only enhancing restaurants that made it through clustering
        enhanced_clusters = enhance_clusters_with_yelp_data(
            clusters,
            search_radius_m=500,
            name_similarity_threshold=0.6,
            enable_linking=True
        )
        
        # Enhance restaurants with Foursquare data AFTER Yelp enhancement
        # This provides additional venue information and social data
        # enhanced_clusters = enhance_clusters_with_foursquare_data(
        #     enhanced_clusters,
        #     search_radius_m=100,
        #     name_similarity_threshold=0.7,
        #     enable_linking=True
        # )

        return enhanced_clusters
        
    except Exception as e:
        return f"Error searching for places: {str(e)}"

