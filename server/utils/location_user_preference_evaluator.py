"""
Generic location/POI evaluation against user preferences

Evaluates how well locations match user preferences, considering both:
- UserPreference: Long-term user profile preferences
- PreferenceOverride: Recent user input (higher priority)
"""

import logging
from typing import List, Optional
from models.ai_models import create_vertex_ai_model
from models.point_of_interest_models import PointOfInterest
from models.location_preference_model import LocationPreferenceMatch, LocationPreferenceMatches
from user_profile.models import UserPreference, TravelStyle
from user_profile.ephemeral.preference_override_model import PreferenceOverride
from prompt.location_evaluation import get_evaluation_prompt
from utils.poi_utils import is_restaurant

logger = logging.getLogger(__name__)


def _format_preferences_as_text(
    user_preference: Optional[UserPreference],
    travel_style: TravelStyle,
    preference_override: Optional[PreferenceOverride] = None
) -> str:
    """
    Format preferences as text for LLM prompt.
    Shows both base and override with clear priority.
    """
    lines = []
    
    has_base = False
    has_override = False
    
    # Check what we have
    if user_preference:
        food_pref = user_preference.get_food_preference(travel_style)
        stay_pref = user_preference.get_stay_preference(travel_style)
        travel_pref = user_preference.get_travel_preference(travel_style)
        has_base = any([food_pref, stay_pref, travel_pref])
    
    if preference_override:
        has_override = any([
            preference_override.food,
            preference_override.stay,
            preference_override.travel
        ])
    
    # Priority note
    if has_override and has_base:
        lines.append("⚠️ PRIORITY: Recent overrides (🔥) MUST take precedence over base preferences (📋) when they conflict.")
        lines.append("")
    elif has_override:
        lines.append("Using recent user input (overrides only).")
        lines.append("")
    elif has_base:
        lines.append("Using user profile preferences.")
        lines.append("")
    else:
        return "No specific preferences. Use general recommendations for {}.".format(travel_style.value)
    
    # Base preferences
    if has_base:
        lines.append("📋 BASE PREFERENCES (User Profile):")
        
        food_pref = user_preference.get_food_preference(travel_style) if user_preference else None
        if food_pref and (food_pref.weights or food_pref.budget_weights):
            lines.append("  Food:")
            if food_pref.weights:
                lines.append(f"    {_format_weights(food_pref.weights)}")
            if food_pref.budget_weights:
                lines.append(f"    Budget: {food_pref.budget_weights}")
        
        stay_pref = user_preference.get_stay_preference(travel_style) if user_preference else None
        if stay_pref and (stay_pref.weights or stay_pref.budget_weights):
            lines.append("  Stay:")
            if stay_pref.weights:
                lines.append(f"    {_format_weights(stay_pref.weights)}")
            if stay_pref.budget_weights:
                lines.append(f"    Budget: {stay_pref.budget_weights}")
        
        travel_pref = user_preference.get_travel_preference(travel_style) if user_preference else None
        if travel_pref and (travel_pref.weights or travel_pref.budget_weights):
            lines.append("  Travel:")
            if travel_pref.weights:
                lines.append(f"    {_format_weights(travel_pref.weights)}")
            if travel_pref.budget_weights:
                lines.append(f"    Budget: {travel_pref.budget_weights}")
        
        lines.append("")
    
    # Override preferences
    if has_override:
        lines.append("🔥 OVERRIDES (Recent User Input - HIGHER PRIORITY):")
        
        if preference_override.food:
            lines.append("  Food:")
            if preference_override.food.weights:
                lines.append(f"    {_format_weights(preference_override.food.weights)}")
            if preference_override.food.budget_weights:
                lines.append(f"    Budget: {preference_override.food.budget_weights}")
        
        if preference_override.stay:
            lines.append("  Stay:")
            if preference_override.stay.weights:
                lines.append(f"    {_format_weights(preference_override.stay.weights)}")
            if preference_override.stay.budget_weights:
                lines.append(f"    Budget: {preference_override.stay.budget_weights}")
        
        if preference_override.travel:
            lines.append("  Travel:")
            if preference_override.travel.weights:
                lines.append(f"    {_format_weights(preference_override.travel.weights)}")
            if preference_override.travel.budget_weights:
                lines.append(f"    Budget: {preference_override.travel.budget_weights}")
    
    return "\n".join(lines)


def _format_weights(weights: dict, max_items: int = 10) -> str:
    """Format weights dict for display"""
    sorted_weights = sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True)
    top = sorted_weights[:max_items]
    
    formatted = []
    for key, val in top:
        if val >= 0.7:
            label = "MUST"
        elif val >= 0.3:
            label = "PREFER"
        elif val > -0.3:
            label = "OK"
        elif val > -0.7:
            label = "AVOID"
        else:
            label = "EXCLUDE"
        formatted.append(f"{key}:{val:+.1f}({label})")
    
    return ", ".join(formatted)




def evaluate_locations(
    pois: List[PointOfInterest],
    travel_style: TravelStyle,
    user_preference: Optional[UserPreference] = None,
    preference_override: Optional[PreferenceOverride] = None,
    model: str = "gemini-flash",
    batch_size: int = 10
) -> Optional[List[LocationPreferenceMatch]]:
    """
    Evaluate how well POIs match user preferences and update POI objects.
    
    Automatically separates restaurants from regular POIs and evaluates them
    separately using appropriate prompts (restaurant prompts use food preferences,
    regular POI prompts use travel/activity preferences).
    
    After evaluation, updates each PointOfInterest with:
    - travel_style: The travel style used for evaluation
    - poi_evaluation: The LocationPreferenceMatch result
    
    Args:
        pois: List of PointOfInterest to evaluate (will be updated in-place)
        travel_style: Current travel style (SOLO, FAMILY, COUPLE, etc.)
        user_preference: Long-term user profile preferences (optional)
        preference_override: Recent user input overrides (optional, higher priority)
        model: LLM model to use (default: "gemini-flash")
        batch_size: Number of POIs to evaluate per LLM call (default: 10)
    
    Returns:
        Combined list of LocationPreferenceMatch for all POIs, or None if error
    
    Examples:
        >>> matches = evaluate_locations(
        ...     pois=tokyo_pois,  # Mix of restaurants and attractions
        ...     travel_style=TravelStyle.FAMILY,
        ...     user_preference=user_profile,
        ...     preference_override=recent_override
        ... )
        >>> # POIs are now updated with travel_style and poi_evaluation
        >>> for poi in tokyo_pois:
        ...     print(f"{poi.name}: {poi.poi_evaluation.fit_score if poi.poi_evaluation else 'N/A'}")
    """
    if not pois:
        return None
    
    # Separate restaurants from regular POIs
    restaurants = []
    regular_pois = []
    
    for poi in pois:
        if is_restaurant(poi):
            restaurants.append(poi)
        else:
            regular_pois.append(poi)
    
    logger.info(
        f"Evaluating {len(pois)} total POIs for {travel_style} travel: "
        f"{len(restaurants)} restaurants, {len(regular_pois)} attractions"
    )
    
    all_matches = []
    
    # Evaluate restaurants separately (uses food preferences + restaurant prompts)
    if restaurants:
        logger.info(f"📍 Evaluating {len(restaurants)} restaurants...")
        restaurant_matches = _evaluate_poi_batch(
            pois=restaurants,
            travel_style=travel_style,
            user_preference=user_preference,
            preference_override=preference_override,
            model=model,
            batch_size=batch_size,
            is_restaurant=True
        )
        if restaurant_matches:
            all_matches.extend(restaurant_matches)
    
    # Evaluate regular POIs separately (uses travel/activity preferences + attraction prompts)
    if regular_pois:
        logger.info(f"🏛️  Evaluating {len(regular_pois)} attractions...")
        attraction_matches = _evaluate_poi_batch(
            pois=regular_pois,
            travel_style=travel_style,
            user_preference=user_preference,
            preference_override=preference_override,
            model=model,
            batch_size=batch_size,
            is_restaurant=False
        )
        if attraction_matches:
            all_matches.extend(attraction_matches)
    
    logger.info(f"✅ Total evaluations: {len(all_matches)}/{len(pois)}")
    
    # Map evaluation results back to POI objects
    if all_matches:
        _map_evaluations_to_pois(pois, all_matches, travel_style)
        logger.info(f"Updated {len(pois)} POIs with evaluation results")
    
    return all_matches if all_matches else None


def _evaluate_poi_batch(
    pois: List[PointOfInterest],
    travel_style: TravelStyle,
    user_preference: Optional[UserPreference],
    preference_override: Optional[PreferenceOverride],
    model: str,
    batch_size: int,
    is_restaurant: bool
) -> Optional[List[LocationPreferenceMatch]]:
    """
    Internal function to evaluate a batch of similar POIs (all restaurants or all attractions).
    
    Args:
        pois: List of POIs to evaluate (all same type)
        travel_style: Travel style for evaluation
        user_preference: Long-term preferences
        preference_override: Recent overrides
        model: LLM model name
        batch_size: POIs per LLM call
        is_restaurant: True if evaluating restaurants, False for attractions
    
    Returns:
        List of LocationPreferenceMatch results
    """
    if not pois:
        return None
    
    # Format preferences for LLM (shows both base and override with priority)
    preference_text = _format_preferences_as_text(
        user_preference=user_preference,
        travel_style=travel_style,
        preference_override=preference_override
    )
    
    poi_type_label = "restaurants" if is_restaurant else "attractions"
    
    # Process in batches to avoid overwhelming LLM
    all_matches = []
    num_batches = (len(pois) + batch_size - 1) // batch_size
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(pois))
        batch_pois = pois[start_idx:end_idx]
        
        logger.info(f"  Batch {batch_idx + 1}/{num_batches}: Evaluating {len(batch_pois)} {poi_type_label}")
        
        # Format POIs for prompt
        locations_text = _format_pois_for_evaluation(batch_pois)
        
        # Build prompt with travel-style-specific guidance
        prompt_template = get_evaluation_prompt(travel_style.value, is_restaurant=is_restaurant)
        prompt = prompt_template.format(
            preference_text=preference_text,
            locations_text=locations_text,
            travel_preferences=preference_text  # For FAMILY prompts compatibility
        )
        
        # Call LLM
        try:
            llm = create_vertex_ai_model(model)
            if not llm:
                logger.error(f"Failed to create LLM model: {model}")
                continue
            
            structured_llm = llm.with_structured_output(LocationPreferenceMatches)
            response = structured_llm.invoke(prompt)
            
            if response and response.matches:
                logger.info(f"  Batch {batch_idx + 1}: Got {len(response.matches)} evaluations")
                all_matches.extend(response.matches)
            else:
                logger.warning(f"  Batch {batch_idx + 1}: No matches returned")
        
        except Exception as e:
            logger.error(f"  Batch {batch_idx + 1} failed: {e}")
            continue
    
    return all_matches if all_matches else None


def _map_evaluations_to_pois(
    pois: List[PointOfInterest],
    matches: List[LocationPreferenceMatch],
    travel_style: TravelStyle
) -> None:
    """
    Map evaluation results back to POI objects.
    
    Updates each POI's travel_style and poi_evaluation fields.
    Uses name matching to find corresponding evaluations.
    
    Args:
        pois: List of POI objects to update (modified in-place)
        matches: List of evaluation results
        travel_style: Travel style used for evaluation
    """
    # Create lookup dict by name (case-insensitive)
    match_lookup = {
        match.name.lower().strip(): match 
        for match in matches
    }
    
    matched_count = 0
    for poi in pois:
        poi_name_key = poi.name.lower().strip()
        
        # Try exact match first
        match = match_lookup.get(poi_name_key)
        
        # If no exact match, try fuzzy matching (in case LLM truncated name)
        if not match:
            for match_name, match_obj in match_lookup.items():
                if poi_name_key in match_name or match_name in poi_name_key:
                    match = match_obj
                    break
        
        # Update POI with evaluation results
        if match:
            poi.travel_style = travel_style
            poi.poi_evaluation = match
            matched_count += 1
        else:
            logger.warning(f"No evaluation found for POI: {poi.name}")
    
    logger.info(f"Matched {matched_count}/{len(pois)} POIs with evaluations")


def _format_pois_for_evaluation(pois: List[PointOfInterest]) -> str:
    """
    Format POIs for LLM evaluation.
    
    Args:
        pois: List of PointOfInterest objects
    
    Returns:
        Formatted text string
    """
    lines = []
    
    for poi in pois:
        # Use restaurant view for restaurants, travel view for others
        if is_restaurant(poi):
            poi_text = poi.get_restaurant_preview_view()
        else:
            poi_text = poi.get_travel_preference_view()
        
        lines.append(f"- {poi_text}")
    
    return "\n".join(lines)

