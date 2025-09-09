"""
AI Model Configuration and Initialization
This module handles the setup and configuration of AI models for the trip planner
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AI_AVAILABLE = True
except ImportError:
    GEMINI_AI_AVAILABLE = False
    # Create dummy class for when Gemini AI is not available
    class ChatGoogleGenerativeAI:
        def __init__(self, *args, **kwargs): 
            pass

class GeminiAIModelManager:
    """Manages Gemini AI model initialization and configuration"""
    
    def __init__(self):
        self.models: Dict[str, ChatGoogleGenerativeAI] = {}
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize multiple Gemini AI models with different configurations"""
        if not GEMINI_AI_AVAILABLE:
            print("Warning: langchain-google-genai not available")
            return
        
        try:
            # Get API key from environment (always available)
            api_key = os.getenv("GOOGLE_API_KEY")
            
            # Default model configurations
            model_configs = {
                "gemini-flash": {
                    "model_name": "gemini-1.5-flash",
                    "temperature": 0.7,
                    "description": "Fast and efficient model for general tasks"
                },
                "gemini-pro": {
                    "model_name": "gemini-1.5-pro",
                    "temperature": 0.7,
                    "description": "Advanced model for complex reasoning tasks"
                },
                "gemini-flash-creative": {
                    "model_name": "gemini-1.5-flash",
                    "temperature": 0.9,
                    "description": "Creative model with higher temperature"
                },
                "gemini-pro-analytical": {
                    "model_name": "gemini-1.5-pro",
                    "temperature": 0.3,
                    "description": "Analytical model with lower temperature"
                }
            }
            
            # Initialize each model
            for model_id, config in model_configs.items():
                self.models[model_id] = ChatGoogleGenerativeAI(
                    model=config["model_name"],
                    temperature=config["temperature"],
                    google_api_key=api_key
                )
                print(f"Gemini AI model '{model_id}' initialized: {config['description']}")
                
        except Exception as e:
            print(f"Failed to initialize Gemini AI models: {str(e)}")
            self.models = {}
    
    def get_model(self, model_id: str = "gemini-flash") -> Optional[ChatGoogleGenerativeAI]:
        """Get a specific Gemini AI model by ID"""
        return self.models.get(model_id)
    
    def get_default_model(self) -> Optional[ChatGoogleGenerativeAI]:
        """Get the default model (gemini-flash)"""
        return self.get_model("gemini-flash")
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models with their configurations"""
        model_info = {}
        for model_id, model in self.models.items():
            model_info[model_id] = {
                "model_name": model.model_name if hasattr(model, 'model_name') else "unknown",
                "temperature": model.temperature if hasattr(model, 'temperature') else "unknown",
                "status": "available" if model else "unavailable"
            }
        return model_info
    
    def is_available(self, model_id: str = "gemini-flash") -> bool:
        """Check if a specific model is available and initialized"""
        return model_id in self.models and self.models[model_id] is not None
    
    def get_model_info(self, model_id: str = "gemini-flash") -> dict:
        """Get information about a specific model configuration"""
        if not self.is_available(model_id):
            return {"status": "not_available", "model_id": model_id}
        
        model = self.models[model_id]
        return {
            "status": "available",
            "model_id": model_id,
            "model_name": model.model_name if hasattr(model, 'model_name') else "unknown",
            "temperature": model.temperature if hasattr(model, 'temperature') else "unknown",
            "auth_method": "api_key"
        }

# Factory Functions
def create_vertex_ai_model(model_id: str = "gemini-flash") -> Optional[ChatGoogleGenerativeAI]:
    """
    Factory function to create and return a Gemini AI model
    
    Args:
        model_id: The model identifier (gemini-flash, gemini-pro, etc.)
    
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
