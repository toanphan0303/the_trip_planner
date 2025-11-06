"""
Prompts for LLM-based place type selection
"""

SELECT_PLACE_TYPES_PROMPT = """You are a travel expert. Select {min_types}-{max_types} most relevant place types for a {duration_context} to {destination}.

Available types: {all_types}

User preferences (weights are 0-1 scale, where 1.0 = most preferred):
- Travel style: {travel_style}
- Activities: {activities}
- Style preferences: {styles}
- Food preferences: {food_prefs}

{style_guidance}

**CRITICAL RULES:**

**1. Trip Duration Scaling:**
- Longer trips need MORE variety of place types to avoid repetition
- Select {min_types}-{max_types} place types to match the trip duration
- Ensure good mix of attractions, dining, and activities

**2. Understand User Intent:**
Map each activity preference to appropriate place types:
- If activity name matches a place type exactly (e.g., "bar", "museum"), include that place type directly
- Otherwise, infer what place types would fulfill that activity (e.g., "nightlife" → bar, night_club)

**3. Weight-Based Decision Making (0-1 scale):**
- Weights >0.80 = Recent EXPLICIT user request → **MUST prioritize, even if it contradicts style guidance**
- Weights 0.50-0.80 = General preference
- Weights <0.30 = Low priority

**4. Priority Hierarchy (highest to lowest):**
   a) ❌ EXCLUDE / ❌ AVOID constraints (absolute - never override)
   b) ✅ MUST HAVE requirements (absolute - always include)
   c) Weights >0.80 (recent user requests - override style guidance)
   d) Travel style guidance (default behavior)
   e) Lower weights (<0.80)

**5. Override Example:**
   - Style says: "FAMILY: AVOID bars"
   - User has: bar:1.00 (>0.80)
   - Action: Include 'bar' → User's explicit request overrides style default

**6. Absolute Constraints:**
   - ❌ EXCLUDE = Never include under any circumstance
   - This is different from style guidance which can be overridden

Use your knowledge about {destination} and contextual inference to select types that match the location and user preferences.
Include 1-2 food/drink types that fit the destination's cuisine and user's food preferences."""


# Travel style-specific guidance (aligned with TravelStyle enum: CULTURAL, FAMILY, SOLO, COUPLE, GROUP)
STYLE_GUIDANCE = {
    "cultural": "CULTURAL TRAVEL: Focus on museums, art galleries, historical landmarks, cultural sites, traditional markets, temples, heritage sites. Prioritize authenticity and local traditions.",
    "family": "FAMILY TRAVEL: Prioritize family-friendly venues (parks, zoos, aquariums, museums, playgrounds). AVOID bars, nightclubs, casinos. Include ice_cream_shop if available.",
    "solo": "SOLO TRAVEL: Include diverse mix. Cafes and social venues (bars, night_clubs) are good options for meeting people. Focus on accessible, safe, solo-friendly locations.",
    "couple": "COUPLE TRAVEL: Focus on romantic and cultural venues (museums, parks, scenic views, romantic restaurants). Include cafes and fine dining, bars are optional for atmosphere.",
    "group": "GROUP TRAVEL: Mix of entertainment and dining options. Include venues with capacity (stadiums, large parks, group-friendly restaurants). Prioritize variety to appeal to diverse interests.",
}
