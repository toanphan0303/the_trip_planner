from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field

class PlanTripForDestinationsArgs(BaseModel):
    destination: str = Field(
        ...,
        description="Primary location for the trip (city, region, or country). Example: 'Tokyo', 'Okinawa', 'Japan'."
    )
    duration_days: Optional[int] = Field(
        ...,
        description="Number of days for the trip. If not provided, defaults may be inferred (e.g., 3–5 days for a city)."
    )
    start_date: Optional[date] = Field(
        None,
        description="Trip start date (YYYY-MM-DD). If missing, trip is treated as flexible."
    )
    end_date: Optional[date] = Field(
        None,
        description="Trip end date (YYYY-MM-DD). Can be derived from start_date + duration_days."
    )
    lodging: Optional[str] = Field(
        None,
        description="Optional lodging location (hotel address, neighborhood, or lat/lng). Used to anchor travel-time calculations."
    )
    num_people: Optional[int] = Field(
        None,
        description="Total number of travelers. Useful for group logistics and ticket booking."
    )
    kids_ages: Optional[List[int]] = Field(
        None,
        description="Ages of children traveling. Drives kid-friendliness filters (e.g., stroller access, nap breaks, ride restrictions)."
    )
    budget: Optional[str] = Field(
        None,
        description="Budget level: 'low', 'mid', or 'high'. Guides activity/restaurant recommendations."
    )
    max_results: Optional[int] = Field(
        10,
        description="Maximum number of places to return per category. Higher values provide more comprehensive results but may increase processing time. Default: 10."
    )