"""
Override Parser
Parses user messages using LLM to detect preferences
"""

from typing import Optional
from pydantic import BaseModel, Field
from .preference_override_model import PreferenceOverride, FoodOverride, StayOverride, TravelOverride
from user_profile.models import TravelStyle
from logger import get_logger
from models.ai_models import gemini_ai_manager, GeminiAI
logger = get_logger(__name__)


class OverrideParsingResult(BaseModel):
    """LLM output for detected preferences"""
    has_override: bool = Field(..., description="True if preferences found")
    confidence: float = Field(0.8, description="Confidence 0.0-1.0")
    
    food: Optional[FoodOverride] = Field(None, description="Food preferences")
    stay: Optional[StayOverride] = Field(None, description="Stay preferences")
    travel: Optional[TravelOverride] = Field(None, description="Travel preferences")
    


PARSING_PROMPT = """Analyze user message for travel preferences.

Message: "{message}"
Travel Style: {travel_style}

Extract preferences for:
- Food: "I want sushi", "vegetarian", "no spicy food"
- Activities: "love museums", "skip nightlife" 
- Stay: "need WiFi", "no hostels"
- Budget: "cheap", "luxury"

Weight scale: -1 (avoid) to +1 (must have)
Budget scale: 0 (cheap) to 1 (luxury)

Return structured preferences."""


def get_preferences_from_message(
    message: str,
    travel_style: Optional[TravelStyle] = None
) -> Optional[OverrideParsingResult]:
    """Get preferences from user message with LLM"""
    if not message or not message.strip():
        return None
    
    try:
        structured_llm = gemini_ai_manager.get_model(GeminiAI.GEMINI_FLASH).with_structured_output(OverrideParsingResult)
        prompt = PARSING_PROMPT.format(
            message=message,
            travel_style=travel_style.value if travel_style else "unknown"
        )
        
        return structured_llm.invoke(prompt)
        
        
    except Exception as e:
        logger.error("Get preferences from message failed: %s", str(e))
        return None

