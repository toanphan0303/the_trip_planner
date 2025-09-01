"""
Models package for Trip Planner
"""

from .function_calling import (
    # Data Models
    Destination,
    TripPlan,
    
    # Function Calling Models
    ParameterProperty,
    FunctionParameters,
    FunctionDeclaration,
    FunctionCallingConfig,
    
    # Function Configurations
    TRIP_PLANNING_FUNCTIONS,
    DESTINATION_RECOMMENDATION_FUNCTIONS,
    ACTIVITY_PLANNING_FUNCTIONS,
    ALL_FUNCTION_DECLARATIONS,
    
    # Helper Functions
    get_function_by_name,
    get_all_function_names,
    function_declaration_to_dict,
    get_function_declarations_as_dict,
    validate_trip_plan,
    create_sample_trip_plan,
    
    # Function Creation Functions
    create_generate_basic_trip_function,
    create_recommend_destinations_function,
    create_plan_daily_activities_function
)

__all__ = [
    # Data Models
    "Destination",
    "TripPlan",
    
    # Function Calling Models
    "ParameterProperty",
    "FunctionParameters", 
    "FunctionDeclaration",
    "FunctionCallingConfig",
    
    # Function Configurations
    "TRIP_PLANNING_FUNCTIONS",
    "DESTINATION_RECOMMENDATION_FUNCTIONS",
    "ACTIVITY_PLANNING_FUNCTIONS",
    "ALL_FUNCTION_DECLARATIONS",
    
    # Helper Functions
    "get_function_by_name",
    "get_all_function_names",
    "function_declaration_to_dict",
    "get_function_declarations_as_dict",
    "validate_trip_plan",
    "create_sample_trip_plan",
    
    # Function Creation Functions
    "create_generate_basic_trip_function",
    "create_recommend_destinations_function",
    "create_plan_daily_activities_function"
]
