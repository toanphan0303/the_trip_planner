"""
Preference Override System
Short-term preference overrides that don't mutate permanent user preferences
Structured to mirror UserPreference (food, stay, travel)
"""

from __future__ import annotations
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Literal, Any
import time

# Type aliases
PreferenceStyleType = Literal["solo", "couple", "family", "friends", "group"]
PreferenceCategory = Literal["food", "stay", "travel"]


class FoodOverride(BaseModel):
    """
    Food preference override
    
    Weight scale (-1 to +1):
    - +1.0: MUST HAVE
    - +0.7: STRONGLY PREFER
    -  0.0: NEUTRAL
    - -0.7: AVOID
    - -1.0: EXCLUDE
    
    Budget scale (0-1):
    - 0.0-0.3: BUDGET/CHEAP
    - 0.4-0.6: MODERATE
    - 0.7-1.0: UPSCALE/SPLURGE
    """
    weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Preference weights -1 to +1. Example: {'italian': 0.9, 'vegetarian': 1.0, 'fast_food': -0.8}"
    )
    budget_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Budget preferences 0-1. Example: {'cheap': 0.9, 'moderate': 0.5, 'luxury': 0.1}"
    )


class StayOverride(BaseModel):
    """
    Stay preference override
    
    Scales: Same as FoodOverride
    """
    weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Preference weights -1 to +1. Example: {'hotel': 0.8, 'wifi': 1.0, 'hostel': -1.0}"
    )
    budget_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Budget preferences 0-1. Example: {'budget': 0.8, 'luxury': 0.2}"
    )


class TravelOverride(BaseModel):
    """
    Travel preference override
    
    Scales: Same as FoodOverride
    """
    weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Preference weights -1 to +1. Example: {'museums': 0.9, 'kid_friendly': 1.0, 'crowds': -0.8}"
    )
    budget_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Budget preferences 0-1. Example: {'budget_friendly': 0.9}"
    )


class PreferenceHistory(BaseModel):
    """
    Minimal audit trail for preference changes
    
    Event-sourcing: Each user message → one immutable event
    One message can change multiple categories (food + travel + stay)
    
    Example:
        "I want Italian food and no museums" →
        {
            raw_message: "I want Italian food and no museums",
            food: FoodOverride(weights={"italian": 0.9}),
            travel: TravelOverride(weights={"museums": -0.9}),
            stay: None
        }
    """
    
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")
    raw_message: str = Field(..., description="Original user message")
    detected_at: int = Field(default_factory=lambda: int(time.time()), description="Unix timestamp")
    
    # Multiple categories per message
    food: Optional[FoodOverride] = Field(None, description="Food changes detected")
    stay: Optional[StayOverride] = Field(None, description="Stay changes detected")
    travel: Optional[TravelOverride] = Field(None, description="Travel changes detected")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreferenceHistory':
        """Create from dictionary"""
        return cls(**data)


class PreferenceOverride(BaseModel):
    """
    Aggregated preference override (current state)
    
    Redis key: override:{user_id}
    One override per user, incrementally updated
    """
    
    user_id: str = Field(..., description="User ID")
    expires_at: int = Field(default_factory=lambda: int(time.time()) + 48*3600, description="Expiration timestamp")
    
    # Aggregated preferences
    food: Optional[FoodOverride] = Field(None, description="Food preference override")
    stay: Optional[StayOverride] = Field(None, description="Stay preference override")
    travel: Optional[TravelOverride] = Field(None, description="Travel preference override")
    
    # Audit metadata
    last_updated: int = Field(default_factory=lambda: int(time.time()), description="Last modification timestamp")
    
    @validator("expires_at")
    def _ensure_min_ttl(cls, v):
        """Ensure minimum 1 hour TTL"""
        now = int(time.time())
        return max(v, now + 3600)
    
    def alive(self) -> bool:
        """Check if override is still valid"""
        return time.time() < self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PreferenceOverride':
        """Create from dictionary"""
        return cls(**data)

