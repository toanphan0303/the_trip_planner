from pydantic import BaseModel, Field
from typing import List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.point_of_interest_models import Location

class LocationPreferenceMatch(BaseModel):
    """Represents how well a location matches user preferences for a specific travel style"""
    name: str = Field(..., description="The name of the location")
    fit_score: float = Field(..., ge=0.0, le=1.0, description="How well the location fits user preferences (0=no fit, 1=perfect fit)")
    reason: str = Field(..., description="Brief explanation of why this location fits or doesn't fit the user's preferences")
    highlights: str = Field(..., description="Short paragraph highlighting things to do in this location tailored to the user's preferences")
    confidence: Literal["low", "medium", "high"] = Field(default="medium", description="Confidence level in this evaluation")
    key_attractions: List[str] = Field(default_factory=list, description="List of 2-3 key attractions or activities that align with user preferences")
    travel_style_match: Literal["cultural", "family", "solo", "couple", "group"] = Field(
        ..., 
        description="Travel style this evaluation was made for (cultural/family/solo/couple/group)"
    )
    concern: Optional[str] = Field(default=None, description="Safety, weather, or other concerns travelers should be aware of")
    tips: Optional[str] = Field(default=None, description="Helpful tips for travelers visiting this location")
    location: Optional[object] = Field(default=None, description="Geographic coordinates (Location object)")

class LocationPreferenceMatches(BaseModel):
    """Wrapper for location preference matches indexed by location name"""
    matches: List[LocationPreferenceMatch] = Field(..., description="List of location preference matches")
