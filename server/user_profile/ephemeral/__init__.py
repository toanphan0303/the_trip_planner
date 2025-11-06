"""
Ephemeral Override System
Short-term preference patches that don't mutate permanent user preferences
"""

from .preference_override_model import (
    PreferenceOverride,
    PreferenceHistory,
    FoodOverride,
    StayOverride,
    TravelOverride,
    PreferenceStyleType,
    PreferenceCategory
)

from .override_parser import (
    get_preferences_from_message,
    OverrideParsingResult
)

__all__ = [
    # Core models
    "PreferenceOverride",
    "PreferenceHistory",
    "FoodOverride",
    "StayOverride",
    "TravelOverride",
    
    # Parser
    "get_preferences_from_message",
    "OverrideParsingResult",
    
    # Type aliases
    "PreferenceStyleType",
    "PreferenceCategory",
]

