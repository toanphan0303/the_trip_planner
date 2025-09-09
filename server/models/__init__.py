"""
Models package for Trip Planner

This package contains:
- AI model management and initialization
- Data models for trip planning (when needed)
"""

# AI Model Management - Only what's actually used
from .ai_models import create_vertex_ai_model


# Note: Most function calling models are not currently used in the codebase
# They can be imported directly when needed:
# from .function_calling import Destination, TripPlan, etc.

__all__ = [
    "create_vertex_ai_model",
]
