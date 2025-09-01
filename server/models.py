"""
Shared data models for the Trip Planner application
"""

from typing import List
from pydantic import BaseModel

# Legacy model for backward compatibility
class TripPlannerRequest(BaseModel):
    """Request model for trip planning"""
    destination_preferences: List[str]
    duration_days: int
    budget_range: str
    travel_style: str
    interests: List[str]
    group_size: int

# Import new function calling models
try:
    from .models.function_calling import (
        Destination,
        TripPlan,
        TRIP_PLANNING_FUNCTIONS,
        ALL_FUNCTION_DECLARATIONS,
        get_function_by_name,
        get_all_function_names,
        validate_trip_plan,
        create_sample_trip_plan
    )
except ImportError:
    # Fallback if models package is not available
    pass
