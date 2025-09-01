"""
Function Calling Models for Trip Planner
This module contains the function declarations and data models for AI function calling
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# Data Models for Trip Planning

class Destination(BaseModel):
    """Model for a single destination in a trip"""
    name: str = Field(..., description="Name of the destination/city")
    country: str = Field(..., description="Country of the destination")
    duration_days: int = Field(..., description="Number of days to spend at this destination")
    activities: List[str] = Field(..., description="List of activities to do at this destination")
    accommodation_type: str = Field(..., description="Type of accommodation (hotel, hostel, resort, etc.)")
    budget_range: str = Field(..., description="Budget range for this destination")

class TripPlan(BaseModel):
    """Model for a complete trip plan"""
    destinations: List[Destination] = Field(..., description="List of destinations to visit")
    total_duration: int = Field(..., description="Total duration of the trip in days")
    total_budget_range: str = Field(..., description="Total budget range for the entire trip")
    travel_style: str = Field(..., description="Travel style (budget, luxury, adventure, etc.)")
    best_time_to_visit: str = Field(..., description="Best time of year to visit")
    transportation: List[str] = Field(..., description="List of transportation methods between destinations")

# Function Calling Models

class ParameterProperty(BaseModel):
    """Model for a parameter property in function calling"""
    type: str = Field(..., description="Type of the parameter (string, integer, array, object, etc.)")
    description: Optional[str] = Field(None, description="Description of the parameter")
    items: Optional[Dict[str, Any]] = Field(None, description="Schema for array items")
    properties: Optional[Dict[str, Any]] = Field(None, description="Properties for object type")
    required: Optional[List[str]] = Field(None, description="Required properties for object type")

class FunctionParameters(BaseModel):
    """Model for function parameters schema"""
    type: str = Field(..., description="Type of the parameters (usually 'object')")
    properties: Dict[str, ParameterProperty] = Field(..., description="Parameter properties")
    required: List[str] = Field(..., description="Required parameters")

class FunctionDeclaration(BaseModel):
    """Model for a function declaration in function calling"""
    name: str = Field(..., description="Name of the function")
    description: str = Field(..., description="Description of what the function does")
    parameters: FunctionParameters = Field(..., description="Function parameters schema")

class FunctionCallingConfig(BaseModel):
    """Model for function calling configuration"""
    function_declarations: List[FunctionDeclaration] = Field(..., description="List of function declarations")

# Trip Planning Function Declarations

def create_generate_basic_trip_function() -> FunctionDeclaration:
    """Create the generate_basic_trip function declaration"""
    return FunctionDeclaration(
        name="generate_basic_trip",
        description="Generate a basic trip plan based on user preferences",
        parameters=FunctionParameters(
            type="object",
            properties={
                "destinations": ParameterProperty(
                    type="array",
                    description="List of destinations to visit",
                    items={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "country": {"type": "string"},
                            "duration_days": {"type": "integer"},
                            "activities": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "accommodation_type": {"type": "string"},
                            "budget_range": {"type": "string"}
                        },
                        "required": ["name", "country", "duration_days", "activities", "accommodation_type", "budget_range"]
                    }
                ),
                "total_duration": ParameterProperty(
                    type="integer",
                    description="Total duration of the trip in days"
                ),
                "total_budget_range": ParameterProperty(
                    type="string",
                    description="Total budget range for the entire trip"
                ),
                "travel_style": ParameterProperty(
                    type="string",
                    description="Travel style (budget, luxury, adventure, etc.)"
                ),
                "best_time_to_visit": ParameterProperty(
                    type="string",
                    description="Best time of year to visit"
                ),
                "transportation": ParameterProperty(
                    type="array",
                    description="List of transportation methods between destinations",
                    items={"type": "string"}
                )
            },
            required=["destinations", "total_duration", "total_budget_range", "travel_style", "best_time_to_visit", "transportation"]
        )
    )

def create_recommend_destinations_function() -> FunctionDeclaration:
    """Create the recommend_destinations function declaration"""
    return FunctionDeclaration(
        name="recommend_destinations",
        description="Recommend destinations based on user preferences and constraints",
        parameters=FunctionParameters(
            type="object",
            properties={
                "interests": ParameterProperty(
                    type="array",
                    description="User interests (culture, food, adventure, etc.)",
                    items={"type": "string"}
                ),
                "budget_range": ParameterProperty(
                    type="string",
                    description="Budget range for the trip"
                ),
                "duration_days": ParameterProperty(
                    type="integer",
                    description="Duration of the trip in days"
                ),
                "travel_style": ParameterProperty(
                    type="string",
                    description="Travel style preference"
                ),
                "preferred_continents": ParameterProperty(
                    type="array",
                    description="Preferred continents or regions",
                    items={"type": "string"}
                ),
                "season": ParameterProperty(
                    type="string",
                    description="Preferred season for travel"
                )
            },
            required=["interests", "budget_range", "duration_days"]
        )
    )

def create_plan_daily_activities_function() -> FunctionDeclaration:
    """Create the plan_daily_activities function declaration"""
    return FunctionDeclaration(
        name="plan_daily_activities",
        description="Plan daily activities for a specific destination",
        parameters=FunctionParameters(
            type="object",
            properties={
                "destination": ParameterProperty(
                    type="string",
                    description="Name of the destination"
                ),
                "duration_days": ParameterProperty(
                    type="integer",
                    description="Number of days at the destination"
                ),
                "interests": ParameterProperty(
                    type="array",
                    description="User interests for activities",
                    items={"type": "string"}
                ),
                "budget_level": ParameterProperty(
                    type="string",
                    description="Budget level for activities"
                ),
                "travel_style": ParameterProperty(
                    type="string",
                    description="Travel style preference"
                ),
                "accessibility_needs": ParameterProperty(
                    type="string",
                    description="Accessibility requirements"
                ),
                "group_size": ParameterProperty(
                    type="integer",
                    description="Size of the travel group"
                )
            },
            required=["destination", "duration_days", "interests"]
        )
    )

# Function Calling Configurations

TRIP_PLANNING_FUNCTIONS = FunctionCallingConfig(
    function_declarations=[create_generate_basic_trip_function()]
)

DESTINATION_RECOMMENDATION_FUNCTIONS = FunctionCallingConfig(
    function_declarations=[create_recommend_destinations_function()]
)

ACTIVITY_PLANNING_FUNCTIONS = FunctionCallingConfig(
    function_declarations=[create_plan_daily_activities_function()]
)

# Combined Function Declarations
ALL_FUNCTION_DECLARATIONS = [
    TRIP_PLANNING_FUNCTIONS,
    DESTINATION_RECOMMENDATION_FUNCTIONS,
    ACTIVITY_PLANNING_FUNCTIONS
]

# Helper Functions

def get_function_by_name(function_name: str) -> Optional[FunctionDeclaration]:
    """Get a specific function declaration by name"""
    for function_config in ALL_FUNCTION_DECLARATIONS:
        for func_decl in function_config.function_declarations:
            if func_decl.name == function_name:
                return func_decl
    return None

def get_all_function_names() -> List[str]:
    """Get all available function names"""
    function_names = []
    for function_config in ALL_FUNCTION_DECLARATIONS:
        for func_decl in function_config.function_declarations:
            function_names.append(func_decl.name)
    return function_names

def function_declaration_to_dict(func_decl: FunctionDeclaration) -> Dict[str, Any]:
    """Convert a FunctionDeclaration to a dictionary for API compatibility"""
    return {
        "name": func_decl.name,
        "description": func_decl.description,
        "parameters": {
            "type": func_decl.parameters.type,
            "properties": {
                name: {
                    "type": prop.type,
                    **({"description": prop.description} if prop.description else {}),
                    **({"items": prop.items} if prop.items else {}),
                    **({"properties": prop.properties} if prop.properties else {}),
                    **({"required": prop.required} if prop.required else {})
                }
                for name, prop in func_decl.parameters.properties.items()
            },
            "required": func_decl.parameters.required
        }
    }

def get_function_declarations_as_dict() -> List[Dict[str, Any]]:
    """Get all function declarations as dictionaries for API compatibility"""
    result = []
    for function_config in ALL_FUNCTION_DECLARATIONS:
        result.append({
            "function_declarations": [
                function_declaration_to_dict(func_decl)
                for func_decl in function_config.function_declarations
            ]
        })
    return result

# Example usage and validation

def validate_trip_plan(trip_data: Dict[str, Any]) -> TripPlan:
    """Validate and create a TripPlan from raw data"""
    return TripPlan(**trip_data)

def create_sample_trip_plan() -> TripPlan:
    """Create a sample trip plan for testing"""
    return TripPlan(
        destinations=[
            Destination(
                name="Paris",
                country="France",
                duration_days=3,
                activities=["Visit Eiffel Tower", "Louvre Museum", "Seine River Cruise"],
                accommodation_type="hotel",
                budget_range="$200-300 per day"
            ),
            Destination(
                name="London",
                country="United Kingdom",
                duration_days=4,
                activities=["Big Ben", "British Museum", "Tower of London"],
                accommodation_type="hotel",
                budget_range="$250-350 per day"
            )
        ],
        total_duration=7,
        total_budget_range="$3000-4500",
        travel_style="cultural",
        best_time_to_visit="Spring (March-May)",
        transportation=["Eurostar train", "London Underground", "Paris Metro"]
    )
