from pydantic import BaseModel, Field
from typing import List, Literal

class LocationPreferenceMatch(BaseModel):
    """Represents how well a location matches user preferences"""
    fit_score: float = Field(..., ge=0.0, le=1.0, description="How well the location fits user preferences (0=no fit, 1=perfect fit)")
    reason: str = Field(..., description="Brief explanation of why this location fits or doesn't fit the user's preferences")
    highlights: str = Field(..., description="Short paragraph highlighting things to do in this location tailored to the user's preferences")
    confidence: Literal["low", "medium", "high"] = Field(..., description="Confidence level in this evaluation")
    key_attractions: List[str] = Field(..., description="List of 2-3 key attractions or activities that align with user preferences")
    travel_style_match: str = Field(..., description="How this location matches the user's travel style (family/couple/solo)")

class LocationPreferenceEvaluation(BaseModel):
    """Collection of location preference evaluations"""
    location_name: str = Field(..., description="Name of the location being evaluated")
    evaluations: List[LocationPreferenceMatch] = Field(..., description="List of preference matches for this location")
    overall_fit: float = Field(..., description="Overall fit score across all preference dimensions")
    recommendation: Literal["strongly_recommend", "recommend", "consider", "not_recommend"] = Field(..., description="Overall recommendation level")
