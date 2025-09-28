"""
LLM call for evaluating how well locations match user preferences
"""

from models.ai_models import create_vertex_ai_model
from models.location_preference_model import LocationPreferenceEvaluation
from models.point_of_interest_models import PointOfInterest
from prompt.location_preference import format_travel_preference_prompt
from typing import List, Dict, Any

def evaluate_travel_preferences(
    locations: List[PointOfInterest], 
    travel_preferences: Dict[str, Any],
    model: str = "gemini-flash"
) -> LocationPreferenceEvaluation:
    """
    Evaluate how well PointOfInterest locations match user travel preferences
    
    Args:
        locations: List of PointOfInterest objects from enhanced_clusters
        travel_preferences: TravelPreference dictionary from user profile
        model: LLM model to use (default: "gemini-flash")
        
    Returns:
        LocationPreferenceEvaluation with fit scores and recommendations
    """
    
    # Create the model
    llm_model = create_vertex_ai_model(model)
    
    # Format the prompt with actual data
    prompt = format_travel_preference_prompt(locations, travel_preferences)
    
    # Make the LLM call with structured output
    try:
        structured_model = llm_model.with_structured_output(LocationPreferenceEvaluation)
        response = structured_model.invoke(prompt)
        return response
    except Exception as e:
        print(f"Error in location preference evaluation: {e}")
        # Return a default response if evaluation fails
        return LocationPreferenceEvaluation(
            location_name="Evaluation Failed",
            evaluations=[],
            overall_fit=0.0,
            recommendation="not_recommend"
        )

