"""
Models package for Trip Planner

This package contains:
- AI model management and initialization
- Data models for trip planning (when needed)
"""

# AI Model Management - Only what's actually used
from .ai_models import create_vertex_ai_model

# Data Models - Import when needed
# from .point_of_interest_models import PointOfInterest, Source
# from .yelp_model import YelpPointOfInterest
# from .foursquare_model import FoursquareVenue, FoursquareSearchResponse

__all__ = [
    "create_vertex_ai_model",
]
