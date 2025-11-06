"""
Google Places API Place Types - Simplified
Based on: https://developers.google.com/maps/documentation/places/web-service/place-types
"""

import logging
from typing import List, Set, Optional, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field
from user_profile.models import TravelStyle

if TYPE_CHECKING:
    from user_profile.models import UserPreference
    from user_profile.ephemeral.preference_override_model import PreferenceOverride

logger = logging.getLogger(__name__)


def calculate_place_type_range(duration_days: Optional[int] = None) -> tuple[int, int]:
    """
    Calculate the recommended range of place types based on trip duration.
    
    Args:
        duration_days: Trip duration in days (None defaults to 4-7)
    
    Returns:
        Tuple of (min_types, max_types)
    """
    if duration_days is None:
        return (4, 7)
    
    if duration_days <= 2:
        return (4, 6)
    elif duration_days <= 5:
        return (6, 10)
    elif duration_days <= 10:
        return (10, 15)
    else:
        return (15, 20)


class SelectedPlaceTypes(BaseModel):
    place_types: List[str] = Field(description="Selected place types based on trip duration")
    reason: str = Field(description="Reason for selecting the place types (max 2 sentences)")

class PlaceTypes:
    """Main class for accessing place types"""
    
    @staticmethod
    def get_food_types() -> Set[str]:
        """
        Get all food and drink related place types.
        Used to identify restaurants and food establishments.
        
        Returns:
            Set of food/drink place type strings (lowercase)
        """
        return {
            # Table A - Food & Drink base types
            "bakery",
            "bar",
            "cafe",
            "meal_delivery",
            "meal_takeaway",
            "restaurant",
            "food",
            
            # Table B - Specific restaurant types
            "american_restaurant",
            "asian_restaurant",
            "barbecue_restaurant",
            "brazilian_restaurant",
            "breakfast_restaurant",
            "brunch_restaurant",
            "chinese_restaurant",
            "fast_food_restaurant",
            "french_restaurant",
            "greek_restaurant",
            "hamburger_restaurant",
            "ice_cream_shop",
            "indian_restaurant",
            "indonesian_restaurant",
            "italian_restaurant",
            "japanese_restaurant",
            "korean_restaurant",
            "lebanese_restaurant",
            "mediterranean_restaurant",
            "mexican_restaurant",
            "middle_eastern_restaurant",
            "pizza_restaurant",
            "ramen_restaurant",
            "sandwich_shop",
            "seafood_restaurant",
            "spanish_restaurant",
            "steak_house",
            "sushi_restaurant",
            "thai_restaurant",
            "turkish_restaurant",
            "vegan_restaurant",
            "vegetarian_restaurant",
            "vietnamese_restaurant"
        }
    
    @staticmethod
    def get_trip_planning_types() -> List[str]:
        """
        Get comprehensive list of place types for trip planning.
        Covers common tourist attractions and essential services.
        
        Returns:
            List of place type strings suitable for trip planning searches
        """
        return [
            # 🏙️ Landmarks & Attractions
            "tourist_attraction",
            "point_of_interest",
            "museum",
            "art_gallery",
            "park",
            "amusement_park",
            "aquarium",
            "zoo",
            "natural_feature",
            "historical_landmark",

            # 🌆 Cultural & Heritage
            "church",
            "library",
            "city_hall",
            "university",
            "historical_place",
            "cultural_landmark",
            "museum",
            "monument",

            # entertainment and recreation
            "tourist_attraction",
            "off_roading_area",
            "park",
            "picnic_ground",
            "zoo",
            "amusement_park",
            "cycling_park",
            "cultural_center",
            "childrens_camp",

            # 🧗‍♀️ Outdoor & Nature (Table A only)
            "campground",
            "national_park",
            "beach"
            # Note: beach, mountain, lake, river, hiking_area, scenic_view not in Table A

            # 🍽️ Food & Drink
            "restaurant",
            "cafe",
            "bakery",
            "bar",
            "food_court",
            "ice_cream_shop",

            # 🛍️ Shopping & Local Markets
            "shopping_mall",
            "market",
            "souvenir_shop",
            "book_store",
            "supermarket",

            # 🏖️ Leisure & Entertainment
            "spa",
            "night_club",
            "movie_theater",
            "casino",
            "stadium",
            "event_venue",
            "performing_arts_theater",
        ]
    
    @staticmethod
    def _get_top_preferences(weights: dict, limit: int = 3) -> str:
        """Extract top N preferences as concise string."""
        if not weights:
            return "none"
        sorted_prefs = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:limit]
        return ", ".join([f"{k}:{v:.2f}" for k, v in sorted_prefs])
    
    @staticmethod
    def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize weights to 0-1 range where max weight = 1.0
        
        Args:
            weights: Dictionary of item -> weight
            
        Returns:
            Normalized weights where highest weight is 1.0
        """
        if not weights:
            return {}
        
        max_weight = max(weights.values())
        if max_weight <= 0:
            return weights
        
        # Scale so max weight = 1.0
        return {k: min(v / max_weight, 1.0) for k, v in weights.items()}
    
    @staticmethod
    def _get_base_preferences(
        user_preference: "UserPreference",
        travel_style: TravelStyle
    ) -> tuple:
        """
        Extract base preferences for the specified travel style.
        
        Returns:
            Tuple of (travel_pref, food_pref) or (None, None) if not found
        """
        if not user_preference:
            return None, None
        
        travel_pref = user_preference.travel.get(travel_style.value)
        if not travel_pref:
            # Fallback to first available travel preference
            travel_pref = next(iter(user_preference.travel.values())) if user_preference.travel else None
        
        food_pref = user_preference.food.get(travel_style.value) if travel_pref else None
        
        return travel_pref, food_pref
    
    @staticmethod
    def _merge_override_with_base(
        base_travel_pref,
        base_food_pref,
        ephemeral_override: Optional["PreferenceOverride"],
        override_multiplier: float = 3.0
    ) -> Dict[str, Any]:
        """
        Merge ephemeral override with base preferences.
        Override gets higher weight (3x by default).
        
        Returns:
            Dictionary with merged weights and constraints
        """
        # Initialize with base preferences (handle None)
        merged = {
            "activity_weights": dict(base_travel_pref.activity_weights or {}) if base_travel_pref else {},
            "style_weights": dict(base_travel_pref.travel_style_weights or {}) if base_travel_pref else {},
            "cuisine_weights": dict(base_food_pref.cuisine_weights or {}) if base_food_pref else {},
            "excluded_types": [],
            "must_include_keywords": [],
            "avoided_activities": []
        }
        
        # Merge override if provided and still valid
        if ephemeral_override and ephemeral_override.alive():
            # Merge travel override
            if ephemeral_override.travel:
                # TravelOverride uses 'weights' not 'activity_weights'
                for activity, weight in (ephemeral_override.travel.weights or {}).items():
                    current = merged["activity_weights"].get(activity, 0)
                    # Positive weights boost, negative weights avoid
                    if weight > 0:
                        merged["activity_weights"][activity] = current + (weight * override_multiplier)
                    elif weight < -0.5:
                        merged["avoided_activities"].append(activity)
                        merged["activity_weights"][activity] = 0.05  # Near zero
            
            # Merge food override
            if ephemeral_override.food:
                # FoodOverride uses 'weights' not 'cuisine_weights'
                for cuisine, weight in (ephemeral_override.food.weights or {}).items():
                    current = merged["cuisine_weights"].get(cuisine, 0)
                    if weight > 0:
                        merged["cuisine_weights"][cuisine] = current + (weight * override_multiplier)
                    elif weight < -0.5:
                        # Strongly avoid this cuisine
                        merged["excluded_types"].append(cuisine)
        
        return merged
    
    @staticmethod
    def _format_preferences_for_prompt(
        merged: Dict[str, Any],
        base_food_pref,
        travel_style: str
    ) -> Dict[str, str]:
        """
        Format merged preferences into prompt-ready strings.
        All weights are normalized to 0-1 range.
        
        Returns:
            Dictionary with formatted strings: activities, styles, food_prefs
        """
        from prompt.location_types import STYLE_GUIDANCE
        
        # Normalize weights to 0-1 range
        activity_weights_normalized = PlaceTypes._normalize_weights(merged["activity_weights"])
        style_weights_normalized = PlaceTypes._normalize_weights(merged["style_weights"])
        cuisine_weights_normalized = PlaceTypes._normalize_weights(merged["cuisine_weights"])
        
        # Format activities with avoids
        activities = PlaceTypes._get_top_preferences(activity_weights_normalized)
        if merged["avoided_activities"]:
            activities = f"{activities}, ❌ AVOID: {', '.join(merged['avoided_activities'])}"
        
        # Format styles
        styles = PlaceTypes._get_top_preferences(style_weights_normalized)
        
        # Format food preferences
        food_parts = []
        
        # Add constraints first (most important)
        if merged["must_include_keywords"]:
            food_parts.append(f"✅ MUST HAVE: {', '.join(merged['must_include_keywords'])}")
        if merged["excluded_types"]:
            food_parts.append(f"❌ EXCLUDE: {', '.join(merged['excluded_types'])}")
        
        # Add cuisine preferences
        if cuisine_weights_normalized:
            cuisine = PlaceTypes._get_top_preferences(cuisine_weights_normalized, limit=3)
            food_parts.append(f"cuisine={cuisine}")
        
        # Add base food preferences
        if base_food_pref:
            food_type = PlaceTypes._get_top_preferences(base_food_pref.food_type_weights or {}, limit=2)
            if food_type != "none":
                food_parts.append(f"type={food_type}")
            if base_food_pref.alcohol_weight:
                food_parts.append(f"alcohol:{base_food_pref.alcohol_weight:.2f}")
        
        food_prefs = ", ".join(food_parts) if food_parts else "none"
        
        # Get style guidance
        style_guidance = STYLE_GUIDANCE.get(travel_style, "")
        
        return {
            "activities": activities,
            "styles": styles,
            "food_prefs": food_prefs,
            "style_guidance": style_guidance
        }
    
    @staticmethod
    def _build_selection_prompt(
        destination: str,
        all_types: List[str],
        travel_style: str,
        formatted_prefs: Dict[str, str],
        duration_days: Optional[int] = None
    ) -> str:
        """
        Build LLM prompt for place type selection.
        
        Args:
            destination: Destination name
            all_types: List of all available place types
            travel_style: Travel style string
            formatted_prefs: Formatted preference strings
            duration_days: Trip duration in days
            
        Returns:
            Complete prompt string for LLM
        """
        from prompt.location_types import SELECT_PLACE_TYPES_PROMPT
        
        min_types, max_types = calculate_place_type_range(duration_days)
        duration_context = f"{duration_days}-day trip" if duration_days else "trip"
        
        return SELECT_PLACE_TYPES_PROMPT.format(
            destination=destination,
            all_types=', '.join(all_types),
            travel_style=travel_style,
            activities=formatted_prefs["activities"],
            styles=formatted_prefs["styles"],
            food_prefs=formatted_prefs["food_prefs"],
            style_guidance=formatted_prefs["style_guidance"],
            min_types=min_types,
            max_types=max_types,
            duration_context=duration_context
        )
    
    @staticmethod
    def _validate_and_postprocess(
        llm_response_types: List[str],
        all_types: List[str],
        excluded_types: List[str]
    ) -> List[str]:
        """
        Validate LLM response and apply post-processing rules.
        
        Args:
            llm_response_types: Place types from LLM
            all_types: Valid place types
            excluded_types: Types to exclude
            
        Returns:
            Validated and processed list of 4-7 place types
        """
        # Validate: only keep valid types, cap at 7
        valid_types = [t for t in llm_response_types if t in all_types][:7]
        
        # Apply hard exclusions
        if excluded_types:
            valid_types = [t for t in valid_types if t not in excluded_types]
        
        # Ensure at least one food type
        food_types = {"restaurant", "cafe", "bakery", "bar", "food_court", "ice_cream_shop"}
        if not any(t in food_types for t in valid_types):
            # Add restaurant if not excluded
            if "restaurant" not in excluded_types:
                valid_types.append("restaurant")
            elif "cafe" not in excluded_types:
                valid_types.append("cafe")
        
        # Ensure minimum 4 types
        if len(valid_types) < 4:
            # Return safe defaults
            defaults = ["restaurant", "tourist_attraction", "museum", "park"]
            return [t for t in defaults if t not in excluded_types][:7] or defaults[:4]
        
        return valid_types
    
    @staticmethod
    def select_types_for_user(
        user_preference: "UserPreference",
        destination: str,
        travel_style: TravelStyle = TravelStyle.SOLO,
        ephemeral_override: Optional["PreferenceOverride"] = None,
        model: str = "gemini-flash",
        duration_days: Optional[int] = None
    ) -> List[str]:
        """
        Use LLM to intelligently select place types based on destination and user preferences.
        
        This method combines base preferences with ephemeral overrides (recent user input),
        normalizes all weights to 0-1 scale, and uses LLM to select contextually appropriate
        place types for the destination.
        
        The number of place types scales with trip duration:
        - 1-2 days: 4-6 types
        - 3-5 days: 6-10 types
        - 6-10 days: 10-15 types
        - 11+ days: 15-20 types
        
        Args:
            user_preference: UserPreference object with travel/food/stay preferences
            destination: Destination name (e.g., "Tokyo", "Paris", "New York")
            travel_style: Travel style to use (e.g., SOLO, FAMILY, COUPLE)
            ephemeral_override: Optional recent user input (gets 3x weight vs base preferences)
            model: LLM model to use (default: "gemini-flash")
            duration_days: Trip duration in days (default: None, uses 4-7 types)
            
        Returns:
            List of selected place types chosen by LLM based on destination and duration
        """
        from models.ai_models import create_vertex_ai_model
        
        all_types = PlaceTypes.get_trip_planning_types()
        
        travel_pref, food_pref = PlaceTypes._get_base_preferences(user_preference, travel_style)
        
        # Check if we have ANY preferences (base or override)
        has_base_prefs = travel_pref is not None or food_pref is not None
        has_override = ephemeral_override is not None and (
            ephemeral_override.travel is not None or ephemeral_override.food is not None
        )
        
        logger.info(f"[select_types_for_user] has_base_prefs={has_base_prefs}, has_override={has_override}")
        
        if not has_base_prefs and not has_override:
            # No preferences at all (no base, no override), return defaults
            logger.info("[select_types_for_user] No preferences available, returning defaults")
            return ["restaurant", "tourist_attraction", "museum", "park", "historical_landmark", "spa"]
        
        # Step 2: Merge override with base (override gets 3x weight)
        # This works even if base is None - override will be used
        merged = PlaceTypes._merge_override_with_base(
            travel_pref,
            food_pref,
            ephemeral_override,
            override_multiplier=3.0
        )
        
        # Step 3: Format preferences for prompt (with 0-1 normalized weights)
        formatted_prefs = PlaceTypes._format_preferences_for_prompt(
            merged,
            food_pref,
            travel_style.value
        )
        
        # Step 4: Build LLM prompt
        prompt = PlaceTypes._build_selection_prompt(
            destination,
            all_types,
            travel_style.value,
            formatted_prefs,
            duration_days=duration_days
        )
        
        
        try:
            llm = create_vertex_ai_model(model).with_structured_output(SelectedPlaceTypes)
            response = llm.invoke(prompt)
            
            # Step 6: Validate and post-process
            return PlaceTypes._validate_and_postprocess(
                response.place_types,
                all_types,
                merged["excluded_types"]
            )
            
        except Exception as e:
            logger.error(f"LLM place type selection failed: {e}")
            return ["restaurant", "tourist_attraction", "museum", "park", "cafe", "shopping_mall"]


