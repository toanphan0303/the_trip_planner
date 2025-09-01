#!/usr/bin/env python3
"""
Test script for Function Calling Models
Demonstrates how to use the Pydantic models for function calling
"""

import json
from models.function_calling import (
    FunctionDeclaration,
    FunctionParameters,
    ParameterProperty,
    get_function_by_name,
    get_all_function_names,
    function_declaration_to_dict,
    get_function_declarations_as_dict,
    create_generate_basic_trip_function,
    create_sample_trip_plan
)

def test_function_declaration_creation():
    """Test creating a function declaration using Pydantic models"""
    print("🧪 Testing Function Declaration Creation")
    print("=" * 50)
    
    # Create a simple function declaration
    func_decl = FunctionDeclaration(
        name="test_function",
        description="A test function for demonstration",
        parameters=FunctionParameters(
            type="object",
            properties={
                "input": ParameterProperty(
                    type="string",
                    description="Input parameter"
                ),
                "count": ParameterProperty(
                    type="integer",
                    description="Count parameter"
                )
            },
            required=["input"]
        )
    )
    
    print(f"✅ Created function declaration: {func_decl.name}")
    print(f"   Description: {func_decl.description}")
    print(f"   Parameters: {len(func_decl.parameters.properties)} properties")
    print(f"   Required: {func_decl.parameters.required}")
    
    # Convert to dictionary
    func_dict = function_declaration_to_dict(func_decl)
    print(f"✅ Converted to dictionary: {json.dumps(func_dict, indent=2)}")
    
    return func_decl

def test_predefined_functions():
    """Test the predefined function declarations"""
    print("\n🧪 Testing Predefined Functions")
    print("=" * 50)
    
    # Get all function names
    function_names = get_all_function_names()
    print(f"✅ Available functions: {function_names}")
    
    # Test getting a specific function
    trip_function = get_function_by_name("generate_basic_trip")
    if trip_function:
        print(f"✅ Found function: {trip_function.name}")
        print(f"   Description: {trip_function.description}")
        print(f"   Parameters: {len(trip_function.parameters.properties)} properties")
    else:
        print("❌ Function not found")
    
    # Test creating the trip function
    created_trip_function = create_generate_basic_trip_function()
    print(f"✅ Created trip function: {created_trip_function.name}")
    
    return trip_function

def test_trip_plan_validation():
    """Test trip plan validation"""
    print("\n🧪 Testing Trip Plan Validation")
    print("=" * 50)
    
    # Create a sample trip plan
    sample_plan = create_sample_trip_plan()
    print(f"✅ Created sample trip plan with {len(sample_plan.destinations)} destinations")
    print(f"   Total duration: {sample_plan.total_duration} days")
    print(f"   Budget range: {sample_plan.total_budget_range}")
    print(f"   Travel style: {sample_plan.travel_style}")
    
    # Validate the trip plan
    try:
        validated_plan = sample_plan.model_validate(sample_plan.model_dump())
        print("✅ Trip plan validation successful")
    except Exception as e:
        print(f"❌ Trip plan validation failed: {e}")
    
    return sample_plan

def test_function_declarations_as_dict():
    """Test converting all function declarations to dictionaries"""
    print("\n🧪 Testing Function Declarations as Dictionary")
    print("=" * 50)
    
    # Get all function declarations as dictionaries
    function_dicts = get_function_declarations_as_dict()
    print(f"✅ Converted {len(function_dicts)} function configurations to dictionaries")
    
    # Print the first function declaration
    if function_dicts:
        first_config = function_dicts[0]
        first_function = first_config["function_declarations"][0]
        print(f"   First function: {first_function['name']}")
        print(f"   Description: {first_function['description']}")
    
    return function_dicts

def main():
    """Main test function"""
    print("🚀 Function Calling Models Test")
    print("=" * 60)
    
    try:
        # Run all tests
        test_function_declaration_creation()
        test_predefined_functions()
        test_trip_plan_validation()
        test_function_declarations_as_dict()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
