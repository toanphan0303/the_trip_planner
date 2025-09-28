from typing import List
from models.point_of_interest_models import PointOfInterest

TRAVEL_PREFERENCE_EVALUATION_PROMPT = """
You are an expert travel advisor who evaluates how well PointOfInterest locations match user travel preferences.

You will be given:
1. A list of PointOfInterest objects from enhanced_clusters (attractions, museums, parks, etc.)
2. User TravelPreference from their profile

Your task is to evaluate each location and determine:
- How well it fits the user's travel preferences (fit_score: 0-1)
- Why it fits or doesn't fit (reason)
- What the user can do there tailored to their travel preferences (highlights)
- Key attractions that align with their travel style
- How it matches their travel style (family/couple/solo)

Focus on these location types:
- Tourist attractions and landmarks
- Museums and cultural institutions
- Parks and outdoor spaces
- Shopping areas and markets
- Entertainment venues (theaters, concert halls, etc.)
- Cultural and historical sites
- Outdoor activities and recreation
- Religious and spiritual sites
- Educational institutions
- Sports and recreation facilities

Consider these TravelPreference dimensions:

TRAVEL STYLE WEIGHTS (0-1, where 1=highly preferred):
- adventure: Thrill-seeking, extreme sports, adrenaline activities
- relaxation: Peaceful, spa, wellness, quiet environments
- cultural: Museums, historical sites, art galleries, cultural experiences
- business: Professional, convenient, meeting-friendly locations
- family: Child-friendly, educational, safe, family activities
- solo: Independent, self-guided, personal exploration
- couple: Romantic, intimate, shared experiences
- group: Social, group activities, team experiences
- backpacking: Budget-friendly, authentic, local experiences
- luxury: High-end, premium, exclusive experiences

ACTIVITY WEIGHTS (0-1, where 1=highly preferred):
- museums: Art, history, science, cultural institutions
- nightlife: Bars, clubs, evening entertainment
- shopping: Retail, markets, souvenirs, luxury goods
- outdoor: Nature, hiking, parks, outdoor activities
- sports: Athletic activities, sports venues, fitness
- wellness: Spa, meditation, health, relaxation
- entertainment: Shows, concerts, theaters, amusement
- sightseeing: Tourist attractions, landmarks, scenic views

BEHAVIORAL PREFERENCES:
- budget_score: 0=budget, 0.5=moderate, 1=luxury
- group_size_preference: 0=solo, 1=large group
- adventure_score: 0=safe, 1=extreme adventure
- physical_fitness_score: 0=poor fitness, 1=excellent fitness
- spontaneity: 0=planned, 1=spontaneous
- social_interaction: 0=solitary, 1=social
- cultural_immersion: 0=tourist, 1=local experience
- queue_tolerance: 0=avoid queues, 1=don't mind waiting
- daily_walk_km_target: Daily walking distance preference

ACCESSIBILITY & SAFETY:
- accessibility_weights: Wheelchair accessible, elevator, mobility needs
- activity_preference_weights: Hiking, shopping, photography, specific activities
- avoids: Activities to avoid (crowds, heights, water activities, etc.)

For each location, provide:
1. fit_score (0.0-1.0): How well it matches user travel preferences
2. reason: Brief explanation of why this location fits or doesn't fit
3. highlights: Short paragraph describing tailored activities and experiences
4. confidence: Your confidence level in this evaluation
5. key_attractions: 2-3 specific attractions, exhibits, or activities
6. travel_style_match: How it aligns with their travel style (family/couple/solo)

Be specific and personalized to the user's actual travel preferences for activities and attractions.
"""

def format_travel_preference_prompt(locations: List[PointOfInterest], travel_preferences: dict) -> str:
    """
    Format the travel preference evaluation prompt with actual data
    
    Args:
        locations: List of PointOfInterest objects from enhanced_clusters
        travel_preferences: TravelPreference dictionary from user profile
        
    Returns:
        Formatted prompt string for travel preference evaluation
    """
    
    # Filter out restaurants and format locations
    non_restaurant_locations = []
    for location in locations:
        # Skip restaurants - focus on attractions, museums, parks, etc.
        if not _is_restaurant_location(location):
            non_restaurant_locations.append(location)
    
    if not non_restaurant_locations:
        return "No locations found to evaluate."
    
    # Format locations data
    locations_text = "LOCATIONS TO EVALUATE:\n"
    for i, location in enumerate(non_restaurant_locations[:10], 1):  # Limit to 10 for prompt size
        locations_text += f"\n{i}. {location.name}\n"
        locations_text += f"   Type: {', '.join(location.types) if location.types else 'N/A'}\n"
        locations_text += f"   Rating: {location.rating if location.rating else 'N/A'}\n"
        if location.description:
            locations_text += f"   Description: {location.description[:200]}...\n"
        if location.address:
            locations_text += f"   Address: {location.address}\n"
    
    # Format travel preferences (only include fields with meaningful values)
    preferences_text = "TRAVEL PREFERENCES:\n"
    
    # Only include fields that have actual values (not None, not empty)
    for key, value in travel_preferences.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)) and len(value) == 0:
            continue
        if isinstance(value, str) and value == "":
            continue
            
        # Format the field name nicely
        field_name = key.replace('_', ' ').title()
        preferences_text += f"{field_name}: {value}\n"
    
    return f"{TRAVEL_PREFERENCE_EVALUATION_PROMPT}\n\n{locations_text}\n\n{preferences_text}"

def _is_restaurant_location(location) -> bool:
    """Check if a PointOfInterest location is a restaurant based on its types"""
    if not location.types:
        return False
    
    restaurant_indicators = [
        'restaurant', 'food', 'dining', 'cafe', 'bar', 'pub', 
        'bistro', 'eatery', 'kitchen', 'grill', 'diner'
    ]
    
    # Check if any of the location's types match restaurant indicators
    for type_name in location.types:
        type_lower = type_name.lower()
        if any(indicator in type_lower for indicator in restaurant_indicators):
            return True
    
    return False