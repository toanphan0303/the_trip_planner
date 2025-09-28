from models.ai_models import create_vertex_ai_model
from prompt.location import HIGHLIGHT_LOCATION_PROMPT
from models.location_highlight_model import LocationHighlights

def llm_call(prompt: str, system_context: str, model: str = "gemini-flash"):
    model = create_vertex_ai_model(model)
    response = model.with_structured_output(LocationHighlights, [system_context, prompt])
    return response

def get_highlight_location(location_data: dict, model: str = "gemini-flash"):
    system_context = HIGHLIGHT_LOCATION_PROMPT.format(location_data=location_data)
    return llm_call(system_context, model)
    
