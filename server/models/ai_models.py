"""
AI Model Configuration and Initialization
This module handles the setup and configuration of AI models for the trip planner
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from enum import Enum
from logger import get_logger


load_dotenv()


logger = get_logger(__name__)
class GeminiAI(Enum):
    GEMINI_FLASH = "gemini-flash"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH_CREATIVE = "gemini-flash-creative"
    GEMINI_PRO_ANALYTICAL = "gemini-pro-analytical"

class GeminiAIModelManager:
    """Manages Gemini AI model initialization and configuration"""
    
    def __init__(self):
        self.models: Dict[GeminiAI, ChatGoogleGenerativeAI] = {}
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize multiple Gemini AI models with different configurations"""
        try:
            # Get API key from environment (always available)
            api_key = os.getenv("GOOGLE_API_KEY")
            
            # Default model configurations
            model_configs = {
                GeminiAI.GEMINI_FLASH: {
                    "model_name": "gemini-2.0-flash",
                    "temperature": 0.7,
                    "description": "Fast and efficient model for general tasks"
                },
                GeminiAI.GEMINI_PRO: {
                    "model_name": "gemini-2.0-flash",
                    "temperature": 0.7,
                    "description": "Advanced model for complex reasoning tasks"
                },
                GeminiAI.GEMINI_FLASH_CREATIVE: {
                    "model_name": "gemini-2.0-flash",
                    "temperature": 0.9,
                    "description": "Creative model with higher temperature"
                },
                GeminiAI.GEMINI_PRO_ANALYTICAL: {
                    "model_name": "gemini-2.0-flash",
                    "temperature": 0.3,
                    "description": "Analytical model with lower temperature"
                }
            }
            
            # Initialize each model (use enum as key)
            for model_enum, config in model_configs.items():
                self.models[model_enum] = ChatGoogleGenerativeAI(
                    model=config["model_name"],
                    temperature=config["temperature"],
                    google_api_key=api_key
                )
                logger.info(
                    "Gemini AI model '%s' initialized: %s",
                    model_enum.value,
                    config['description']
                )
                
        except Exception as e:
            logger.error("Failed to initialize Gemini AI models: %s", str(e))
            self.models = {}
    
    def get_model(self, model_id: GeminiAI = GeminiAI.GEMINI_FLASH) -> Optional[ChatGoogleGenerativeAI]:
        """Get a specific Gemini AI model by enum"""
        return self.models.get(model_id)
    
    def get_default_model(self) -> Optional[ChatGoogleGenerativeAI]:
        """Get the default model (GEMINI_FLASH)"""
        return self.get_model(GeminiAI.GEMINI_FLASH)
    
    def list_models(self) -> Dict[GeminiAI, Dict[str, Any]]:
        """List all available models with their configurations"""
        model_info = {}
        for model_enum, model in self.models.items():
            model_info[model_enum] = {
                "model_name": model.model_name if hasattr(model, 'model_name') else "unknown",
                "temperature": model.temperature if hasattr(model, 'temperature') else "unknown",
                "status": "available" if model else "unavailable"
            }
        return model_info
    
    def is_available(self, model_id: GeminiAI = GeminiAI.GEMINI_FLASH) -> bool:
        """Check if a specific model is available and initialized"""
        return model_id in self.models and self.models[model_id] is not None
    
    def get_model_info(self, model_id: GeminiAI = GeminiAI.GEMINI_FLASH) -> dict:
        """Get information about a specific model configuration"""
        if not self.is_available(model_id):
            return {"status": "not_available", "model_id": model_id.value}
        
        model = self.models[model_id]
        return {
            "status": "available",
            "model_id": model_id.value,
            "model_name": model.model_name if hasattr(model, 'model_name') else "unknown",
            "temperature": model.temperature if hasattr(model, 'temperature') else "unknown",
            "auth_method": "api_key"
        }

# Factory Functions
def create_vertex_ai_model(model_id: GeminiAI = GeminiAI.GEMINI_FLASH) -> Optional[ChatGoogleGenerativeAI]:
    """
    Factory function to create and return a Gemini AI model
    
    Args:
        model_id: The model identifier from GeminiAI enum (GEMINI_FLASH, GEMINI_PRO, etc.)
    
    Returns:
        ChatGoogleGenerativeAI instance or None if initialization fails
    """
    manager = get_gemini_ai_manager()
    return manager.get_model(model_id)

def get_gemini_ai_manager() -> GeminiAIModelManager:
    """
    Get a singleton instance of the Gemini AI model manager
    
    Returns:
        GeminiAIModelManager instance
    """
    if not hasattr(get_gemini_ai_manager, '_instance'):
        get_gemini_ai_manager._instance = GeminiAIModelManager()
    return get_gemini_ai_manager._instance

# Global model manager instance
gemini_ai_manager = get_gemini_ai_manager()

# Backward compatibility
model_manager = gemini_ai_manager  # Default to Gemini AI for backward compatibility
vertex_ai_manager = gemini_ai_manager  # Backward compatibility alias
