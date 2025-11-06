from langgraph.prebuilt.chat_agent_executor import AgentState, add_messages
from typing import Optional, Dict, List, Annotated, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime, date
import re
from user_profile.models import TravelStyle
from user_profile.ephemeral.preference_override_model import PreferenceOverride


class MainState(AgentState):
    """
    State for the main graph
    """
    user_id: Optional[str] = None  # User ID for fetching preferences and storing overlays
    ...


def generate_trip_id(formatted_address: Optional[str] = None) -> str:
    """
    Generate incremental trip_id: {destination_slug}_{timestamp}
    
    Examples:
    - tokyo_1762297485.123
    - paris_france_1762297486.456
    - new_york_usa_1762297487.789
    
    Allows sorting by timestamp and identifying destination at a glance.
    """
    timestamp = datetime.now().timestamp()
    
    if formatted_address:
        # Sanitize address to create slug
        slug = re.sub(r'[^a-z0-9]+', '_', formatted_address.lower())
        slug = slug.strip('_')[:30]  # Limit length
        return f"{slug}_{timestamp}"
    else:
        return f"trip_{timestamp}"


class TripState(BaseModel):
    """Represents a single trip being planned or completed"""
    trip_id: str = Field(default_factory=lambda: generate_trip_id())
    formatted_address: Optional[str] = None
    geocode_result: Optional[Dict] = None
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    travel_style: Optional[TravelStyle] = None
    
    # Trip planning data
    search_radius_km: Optional[float] = None  # LLM-determined optimal search radius
    pois: List[Dict] = Field(default_factory=list)  # Raw places from search
    clustered_pois: Optional[Dict] = None  # Clustered and organized POIs
    pois_preference_evaluated: Optional[Dict] = None  # POIs with preference evaluation


class TripData(TypedDict, total=False):
    """Container for trip state and history"""
    current_trip: Optional[TripState]
    history_trips: Optional[List[TripState]]


def merge_trip_data(old: Optional[TripData], new: Optional[TripData]) -> TripData:
    """
    Merge trip data with automatic history archival.
    If new current_trip has different trip_id, auto-moves old trip to history.
    """
    if not new:
        return old or {"current_trip": None, "history_trips": []}
    if not old:
        return new
    
    old_current = old.get("current_trip")
    new_current = new.get("current_trip")
    history = old.get("history_trips") or []  # Only ONE history list
    
    result_current = new_current
    result_history = list(history)
    
    # Check if new_current is a different trip (different trip_id)
    if old_current and new_current:
        old_id = old_current.trip_id if hasattr(old_current, 'trip_id') else None
        new_id = new_current.trip_id if hasattr(new_current, 'trip_id') else None
        
        if old_id and new_id and old_id != new_id:
            # Different trip - archive the old one automatically
            old_current.status = "completed"
            old_current.completed_at = datetime.now()
            result_history.append(old_current)
            print(f"[AUTO-ARCHIVE] Moved trip '{old_current.formatted_address}' to history")
        elif old_id == new_id:
            # Same trip - merge fields
            result_current = merge_trip_state(old_current, new_current)
    
    return {
        "current_trip": result_current,
        "history_trips": result_history if result_history else None
    }


def append_to_history(old: Optional[List[TripState]], new: Optional[List[TripState]]) -> List[TripState]:
    """Append new trips to history"""
    return (old or []) + (new or [])


def merge_trip_state(old: Optional[TripState], new: Optional[TripState]) -> Optional[TripState]:
    """
    Merge TripState fields. Updates only the fields that are provided in new.
    If trip_id differs, returns new trip (old should be moved to history by tool).
    """
    if not new:
        return old
    if not old:
        return new
    
    # Check if this is a different trip (different trip_id)
    old_id = old.trip_id if hasattr(old, 'trip_id') else None
    new_id = new.trip_id if hasattr(new, 'trip_id') else None
    
    if old_id and new_id and old_id != new_id:
        # Different trip - return new trip as-is
        # (Tool should have moved old to history already)
        return new
    
    # Same trip - merge fields
    old_dict = old.model_dump()
    new_dict = new.model_dump() if isinstance(new, TripState) else new
    
    # Merge: new values override old, but only if they're not None/empty
    for key, value in new_dict.items():
        # Skip default/empty values that shouldn't override
        if key in ['created_at', 'trip_id']:
            continue  # Don't override these
        if value is not None and value != [] and value != {}:
            old_dict[key] = value
    
    # Update timestamp
    old_dict['updated_at'] = datetime.now()
    
    return TripState(**old_dict)


def create_trip_update(new_trip: TripState) -> Dict[str, Any]:
    """
    Helper: Creates a trip_data update.
    Reducer will handle archiving automatically if trip_id changes.
    """
    return {
        "trip_data": {
            "current_trip": new_trip
        }
    }


def merge_preference_overrides(
    old: Optional[Dict[TravelStyle, PreferenceOverride]], 
    new: Optional[Dict[TravelStyle, PreferenceOverride]]
) -> Dict[TravelStyle, PreferenceOverride]:
    """
    Deep merge PreferenceOverride dicts.
    Merges PreferenceOverride fields (food/stay/travel) for the same TravelStyle.
    """
    result = dict(old or {})
    
    for style, new_override in (new or {}).items():
        if style in result:
            # Merge PreferenceOverride fields
            existing = result[style]
            result[style] = PreferenceOverride(
                user_id=new_override.user_id or existing.user_id,
                food=new_override.food or existing.food,
                stay=new_override.stay or existing.stay,
                travel=new_override.travel or existing.travel
            )
        else:
            # New style, just add it
            result[style] = new_override
    
    return result


def pick_last(old, new):
    """For scalars: take the most recent value returned by a tool."""
    return new if new is not None else old


class TravelPlannerState(TypedDict, total=False):
    """State for the travel planner graph with automatic reducers"""
    # Messages channel (let LLM & tools talk)
    messages: Annotated[List[dict], add_messages]
    
    # User and travel style fields
    user_id: Annotated[Optional[str], pick_last]
    current_travel_style: Annotated[Optional[TravelStyle], pick_last]
    
    # Preference overrides - deep merged with PreferenceOverride field merging
    preference_overrides: Annotated[Optional[Dict[TravelStyle, PreferenceOverride]], merge_preference_overrides]
    
    # Trip management - single reducer handles current trip + auto-archive to history
    trip_data: Annotated[Optional[TripData], merge_trip_data]
