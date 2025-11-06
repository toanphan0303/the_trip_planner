"""
User Profile Models
Defines user preferences and profile data structures
"""

import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TravelStyle(str, Enum):
    """Travel style preferences"""
    CULTURAL = "cultural"
    FAMILY = "family"
    SOLO = "solo"
    COUPLE = "couple"
    GROUP = "group"


class FoodPreference(BaseModel):
    """
    Food and dining preferences - Hybrid approach matching Override pattern
    
    Weight scale (-1 to +1):
    - +1.0: MUST HAVE / LOVE
    - +0.7: STRONGLY PREFER
    -  0.0: NEUTRAL
    - -0.7: AVOID / DISLIKE
    - -1.0: EXCLUDE / HATE
    
    Score scale (0-1):
    - Budget: 0=cheap, 0.5=moderate, 1=luxury
    - Other scores: 0=low, 0.5=medium, 1=high
    """
    weights: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Food preference weights -1 to +1. "
            "Examples: {'cuisine:japanese': 0.9, 'cuisine:italian': 0.7, "
            "'food_type:fine_dining': 0.8, 'dish:sushi': 0.9, "
            "'seafood': -1.0 (exclude), 'fast_food': -0.7 (avoid)}"
        )
    )
    
    budget_weights: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Budget preference weights 0-1. "
            "Examples: {'cheap': 0.9, 'moderate': 0.5, 'luxury': 0.1}"
        )
    )
    
    # Meta
    notes: str = Field(default="", description="Additional notes")


class StayPreference(BaseModel):
    """
    Accommodation and lodging preferences - Hybrid approach matching Override pattern
    
    Weight scale (-1 to +1):
    - +1.0: MUST HAVE / REQUIRED
    - +0.7: STRONGLY PREFER
    -  0.0: NEUTRAL
    - -0.7: AVOID / DISLIKE
    - -1.0: EXCLUDE / NEVER
    
    Budget scale (0-1):
    - 0.0-0.3: BUDGET
    - 0.4-0.6: MODERATE
    - 0.7-1.0: LUXURY
    """
    weights: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Stay preference weights -1 to +1. "
            "Examples: {'type:hotel': 0.8, 'amenity:wifi': 1.0 (must have), "
            "'location:city_center': 0.6, 'shared_bathroom': -1.0 (exclude)}"
        )
    )
    
    budget_weights: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Budget preference weights 0-1. "
            "Examples: {'budget': 0.8, 'moderate': 0.5, 'luxury': 0.2}"
        )
    )
    
    # Meta
    notes: str = Field(default="", description="Additional notes")
    


class TravelPreference(BaseModel):
    """
    Travel and activity preferences - Hybrid approach matching Override pattern
    
    Weight scale (-1 to +1):
    - +1.0: MUST HAVE / REQUIRED
    - +0.7: STRONGLY PREFER
    -  0.0: NEUTRAL
    - -0.7: AVOID / DISLIKE
    - -1.0: EXCLUDE / NEVER
    
    Budget scale (0-1):
    - 0.0-0.3: BUDGET
    - 0.4-0.6: MODERATE
    - 0.7-1.0: LUXURY
    """
    weights: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Travel preference weights -1 to +1. "
            "Examples: {'activity:museums': 0.9, 'activity:nightlife': 0.3, "
            "'transport:walking': 0.8, 'crowds': -0.9 (avoid), "
            "'kid_friendly': 1.0 (must have)}"
        )
    )
    
    budget_weights: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Budget preference weights 0-1. "
            "Examples: {'budget_friendly': 0.9, 'splurge': 0.2}"
        )
    )
    
    # Meta
    notes: str = Field(default="", description="Additional notes")


class UserPreference(BaseModel):
    """Complete user preference profile with travel style-specific preferences"""
    user_id: str
    version: str = "1.0.0"
    
    # Style-specific preferences (keyed by TravelStyle)
    food: Dict[TravelStyle, FoodPreference] = Field(default_factory=dict)
    stay: Dict[TravelStyle, StayPreference] = Field(default_factory=dict)
    travel: Dict[TravelStyle, TravelPreference] = Field(default_factory=dict)
    
    # Metadata
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    
    # Additional ML metadata
    preference_completeness: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Completeness score of user preferences")
    last_ml_update: Optional[int] = Field(default=None, description="Last time preferences were updated by ML")
    
    # Cross-category behavioral attributes (0-1, where 1 = highly applicable)
    decision_patterns: Dict[str, float] = Field(default_factory=dict, description="Decision-making patterns (0=not applicable, 1=highly applicable). Example: {'impulsive_booker': 0.7, 'research_intensive': 0.8}")
    experience_convenience: Dict[str, float] = Field(default_factory=dict, description="Experience vs convenience trade-offs (0=not applicable, 1=highly applicable). Example: {'authentic_experience': 0.9, 'tourist_comfort': 0.2}")
    value_perception: Dict[str, float] = Field(default_factory=dict, description="Value perception patterns (0=not applicable, 1=highly applicable). Example: {'value_seeker': 0.8, 'premium_payer': 0.3}")
    
    # Global search controls
    must_include_keywords: List[str] = Field(default_factory=list, description="Global keywords that must be included in all search queries. Example: ['family_friendly', 'accessible', 'pet_friendly']")
    
    # Additional behavioral scores
    decision_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Decision-making confidence (0=very hesitant, 1=very confident). Example: 0.3 for indecisive, 0.9 for decisive")
    experience_orientation: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Experience orientation (0=convenience-focused, 1=authentic experience-focused). Example: 0.2 for convenience-first, 0.8 for experience-first")
    quality_sensitivity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Quality sensitivity (0=price-focused, 1=quality-focused). Example: 0.2 for price-sensitive, 0.9 for quality-focused")
    
    def get_food_preference(self, travel_style: TravelStyle) -> Optional[FoodPreference]:
        """Get food preference for specific travel style"""
        return self.food.get(travel_style)
    
    def get_stay_preference(self, travel_style: TravelStyle) -> Optional[StayPreference]:
        """Get stay preference for specific travel style"""
        return self.stay.get(travel_style)
    
    def get_travel_preference(self, travel_style: TravelStyle) -> Optional[TravelPreference]:
        """Get travel preference for specific travel style"""
        return self.travel.get(travel_style)
    
    def get_all_preferences(self, travel_style: TravelStyle) -> Dict[str, Any]:
        """Get all preferences for specific travel style"""
        food = self.get_food_preference(travel_style)
        stay = self.get_stay_preference(travel_style)
        travel = self.get_travel_preference(travel_style)
        
        return {
            "food": food.model_dump() if food else {},
            "stay": stay.model_dump() if stay else {},
            "travel": travel.model_dump() if travel else {}
        }
    
    def set_preference(self, travel_style: str, category: str, preference: Any):
        """Set preference for specific travel style and category"""
        if category == "food":
            self.food[travel_style] = preference
        elif category == "stay":
            self.stay[travel_style] = preference
        elif category == "travel":
            self.travel[travel_style] = preference
        else:
            raise ValueError(f"Invalid category: {category}")
        
        self.update_timestamp()
    

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "version": self.version,
            "food": {k: v.model_dump() for k, v in self.food.items()},
            "stay": {k: v.model_dump() for k, v in self.stay.items()},
            "travel": {k: v.model_dump() for k, v in self.travel.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "preference_completeness": self.preference_completeness,
            "last_ml_update": self.last_ml_update,
            "decision_patterns": self.decision_patterns,
            "experience_convenience": self.experience_convenience,
            "value_perception": self.value_perception,
            "must_include_keywords": self.must_include_keywords,
            "decision_confidence": self.decision_confidence,
            "experience_orientation": self.experience_orientation,
            "quality_sensitivity": self.quality_sensitivity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreference":
        """Create from dictionary (database data)"""
        # Handle migration from old format
        if "food" in data and not isinstance(data["food"], dict):
            # Old format - single preference objects
            return cls._migrate_from_legacy(data)
        
        # New format - dict of preferences
        food_dict = {}
        if "food" in data:
            for style, pref_data in data["food"].items():
                food_dict[style] = FoodPreference(**pref_data)
        
        stay_dict = {}
        if "stay" in data:
            for style, pref_data in data["stay"].items():
                stay_dict[style] = StayPreference(**pref_data)
        
        travel_dict = {}
        if "travel" in data:
            for style, pref_data in data["travel"].items():
                travel_dict[style] = TravelPreference(**pref_data)
        
        return cls(
            user_id=data["user_id"],
            version=data.get("version", "2.0.0"),
            food=food_dict,
            stay=stay_dict,
            travel=travel_dict,
            created_at=data.get("created_at", int(time.time())),
            updated_at=data.get("updated_at", int(time.time())),
            preference_completeness=data.get("preference_completeness"),
            last_ml_update=data.get("last_ml_update"),
            decision_patterns=data.get("decision_patterns", {}),
            experience_convenience=data.get("experience_convenience", {}),
            value_perception=data.get("value_perception", {}),
            must_include_keywords=data.get("must_include_keywords", []),
            decision_confidence=data.get("decision_confidence"),
            experience_orientation=data.get("experience_orientation"),
            quality_sensitivity=data.get("quality_sensitivity")
        )
    
    @classmethod
    def _migrate_from_legacy(cls, data: Dict[str, Any]) -> "UserPreference":
        """Migrate from legacy single-preference format"""
        # Create new format with defaults
        new_data = {
            "user_id": data["user_id"],
            "version": "2.0.0",
            "food": {TravelStyle.SOLO: data.get("food", {})},
            "stay": {TravelStyle.SOLO: data.get("stay", {})},
            "travel": {TravelStyle.SOLO: data.get("travel", {})},
            "created_at": data.get("created_at", int(time.time())),
            "updated_at": data.get("updated_at", int(time.time())),
            "preference_completeness": data.get("preference_completeness"),
            "last_ml_update": data.get("last_ml_update"),
            "decision_patterns": data.get("decision_patterns", {}),
            "experience_convenience": data.get("experience_convenience", {}),
            "value_perception": data.get("value_perception", {}),
            "must_include_keywords": data.get("must_include_keywords", []),
            "decision_confidence": data.get("decision_confidence"),
            "experience_orientation": data.get("experience_orientation"),
            "quality_sensitivity": data.get("quality_sensitivity")
        }
        
        return cls.from_dict(new_data)
    
    def get_travel_preference_for_style(self, travel_style: str, include_empty: bool = False) -> Dict[str, Any]:
        """
        Get travel preference data for specific travel style
        
        Args:
            travel_style: The travel style to get preferences for
            include_empty: If True, include fields with None/empty values. If False, omit them.
            
        Returns:
            Dictionary representation of travel preferences for the style
        """
        travel_pref = self.get_travel_preference(travel_style)
        return travel_pref.get_travel_preference(include_empty=include_empty)
    

