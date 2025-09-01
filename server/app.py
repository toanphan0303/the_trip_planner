"""
LangGraph Trip Planner - Basic Structure
This module contains the basic LangGraph workflow structure
Ready for user to add nodes back later
"""

from langgraph_trip_planner import LangGraphTripPlanner
from models import TripPlannerRequest

# Initialize LangGraph trip planner
langgraph_planner = LangGraphTripPlanner()

def plan_trip_with_langgraph(destination_preferences, duration_days, budget_range, 
                           travel_style, interests, group_size):
    """
    Basic trip planning function - ready for user to implement nodes
    
    This function is used by LangGraph Studio for testing
    """
    try:
        # Create trip request
        trip_request = TripPlannerRequest(
            destination_preferences=destination_preferences,
            duration_days=duration_days,
            budget_range=budget_range,
            travel_style=travel_style,
            interests=interests,
            group_size=group_size
        )
        
        # Use basic LangGraph workflow (no nodes implemented yet)
        result = langgraph_planner.plan_trip(trip_request)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "trip_plan": result.get("trip_plan", {}),
            "workflow_info": {
                "workflow_steps": result.get("workflow_steps", 0),
                "workflow_type": "Basic Structure (no nodes)",
                "nodes": [],
                "data_collection": "LangSmith"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in basic LangGraph trip planning: {str(e)}",
            "trip_plan": {},
            "workflow_info": {
                "workflow_type": "Basic Structure (no nodes)",
                "error": str(e)
            }
        }

# Export the main function for LangGraph Studio
__all__ = ['plan_trip_with_langgraph', 'langgraph_planner']
