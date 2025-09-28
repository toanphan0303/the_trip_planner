from pydantic import BaseModel, Field
from typing import List, Literal

class Highlight(BaseModel):
    """Represents one must-try highlight (dish, activity, or tip) for a location."""
    title: str = Field(..., description="Short name of the highlight, e.g., Wagyu Cheeseburger")
    type: Literal["dish", "activity", "tip"] = Field(..., description="Category of the highlight")
    detail: str = Field(..., description="Supporting explanation or context")
    must_do_score: float = Field(..., ge=0.0, le=1.0, description="Importance rating (0=low, 1=must-do)")
    rationale: str = Field(..., description="Reason why this highlight matters")
    confidence: Literal["low", "medium", "high"] = Field(..., description="Confidence in this recommendation")

class LocationHighlights(BaseModel):
    """Collection of highlights for a given location."""
    highlights: List[Highlight] = Field(..., description="List of highlights with scoring and rationale")