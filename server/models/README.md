# Function Calling Models

This directory contains Pydantic models for AI function calling in the Trip Planner application.

## 📁 Structure

```
models/
├── __init__.py              # Package exports
├── function_calling.py      # Main function calling models
└── README.md               # This file
```

## 🏗️ Model Classes

### Core Function Calling Models

- **`FunctionDeclaration`** - Represents a function that can be called by the AI
- **`FunctionParameters`** - Schema for function parameters
- **`ParameterProperty`** - Individual parameter definition
- **`FunctionCallingConfig`** - Collection of function declarations

### Data Models

- **`Destination`** - Single destination in a trip
- **`TripPlan`** - Complete trip plan with multiple destinations

## 🚀 Usage Examples

### Creating a Function Declaration

```python
from models.function_calling import FunctionDeclaration, FunctionParameters, ParameterProperty

# Create a simple function declaration
func_decl = FunctionDeclaration(
    name="my_function",
    description="A function that does something",
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
```

### Using Predefined Functions

```python
from models.function_calling import (
    get_function_by_name,
    get_all_function_names,
    create_generate_basic_trip_function
)

# Get all available function names
function_names = get_all_function_names()
print(function_names)  # ['generate_basic_trip', 'recommend_destinations', 'plan_daily_activities']

# Get a specific function
trip_function = get_function_by_name("generate_basic_trip")
print(trip_function.name)  # generate_basic_trip

# Create a function programmatically
new_trip_function = create_generate_basic_trip_function()
```

### Converting to Dictionary Format

```python
from models.function_calling import function_declaration_to_dict, get_function_declarations_as_dict

# Convert single function to dictionary
func_dict = function_declaration_to_dict(trip_function)

# Convert all functions to dictionary format (for API compatibility)
all_functions = get_function_declarations_as_dict()
```

### Trip Plan Validation

```python
from models.function_calling import TripPlan, Destination, create_sample_trip_plan

# Create a sample trip plan
sample_plan = create_sample_trip_plan()

# Validate trip plan data
trip_data = {
    "destinations": [...],
    "total_duration": 7,
    "total_budget_range": "$3000-4500",
    # ... other fields
}
validated_plan = TripPlan(**trip_data)
```

## 📋 Available Functions

### 1. `generate_basic_trip`
Generates a basic trip plan based on user preferences.

**Parameters:**
- `destinations` (array) - List of destinations to visit
- `total_duration` (integer) - Total duration in days
- `total_budget_range` (string) - Budget range
- `travel_style` (string) - Travel style preference
- `best_time_to_visit` (string) - Best time to visit
- `transportation` (array) - Transportation methods

### 2. `recommend_destinations`
Recommends destinations based on user preferences.

**Parameters:**
- `interests` (array) - User interests
- `budget_range` (string) - Budget range
- `duration_days` (integer) - Trip duration
- `travel_style` (string) - Travel style
- `preferred_continents` (array) - Preferred regions
- `season` (string) - Preferred season

### 3. `plan_daily_activities`
Plans daily activities for a specific destination.

**Parameters:**
- `destination` (string) - Destination name
- `duration_days` (integer) - Days at destination
- `interests` (array) - Activity interests
- `budget_level` (string) - Budget level
- `travel_style` (string) - Travel style
- `accessibility_needs` (string) - Accessibility requirements
- `group_size` (integer) - Group size

## 🧪 Testing

Run the test script to verify everything works:

```bash
cd server
python test_function_models.py
```

## 🔧 Integration with LangGraph

These models can be easily integrated with LangGraph for function calling:

```python
from models.function_calling import get_function_declarations_as_dict

# Get function declarations for LangGraph
function_declarations = get_function_declarations_as_dict()

# Use with your AI model
model = ChatVertexAI(
    model_name="gemini-1.5-flash",
    tools=function_declarations  # Pass to your model
)
```

## 📝 Benefits

1. **Type Safety** - Pydantic validation ensures data integrity
2. **Reusability** - Models can be used across different parts of the application
3. **Maintainability** - Centralized function definitions
4. **API Compatibility** - Easy conversion to dictionary format for APIs
5. **Documentation** - Self-documenting with field descriptions
