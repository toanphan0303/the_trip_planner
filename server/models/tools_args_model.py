"""
Argument schemas for travel planner tools
"""

from pydantic import BaseModel, Field
from typing import Optional


class GeocodeDestinationArgs(BaseModel):
    """Arguments for geocoding a destination"""
    destination: str = Field(description="Destination like 'Tokyo' or 'Paris'")
    is_new_trip: bool = Field(description="Whether this is a new trip")


class SetTravelStyleArgs(BaseModel):
    """Arguments for setting travel style"""
    travel_style: str = Field(description="Travel style: 'family', 'solo', 'couple', or 'group'")


class UpsertPreferenceArgs(BaseModel):
    """Arguments for upserting user preference overrides"""
    user_message: str = Field(description="User's message with preferences")


class SetDurationDaysArgs(BaseModel):
    """Arguments for setting duration days"""
    duration_days: int = Field(description="Trip duration in days")