# 🌍 Trip Travel Planner - Basic LangGraph Structure

A basic LangGraph workflow structure for trip planning, ready for development and testing using LangGraph Studio.

## 🚀 Features

- **Basic LangGraph Structure**: Clean, minimal workflow foundation
- **LangSmith Integration**: Ready for data collection and monitoring
- **LangGraph Studio**: Workflow visualization and debugging capabilities
- **Google Cloud Integration**: Vertex AI model support
- **Clean Architecture**: Minimal dependencies and code

## 🏗️ Architecture

```
the_trip_planner/
├── server/
│   ├── app.py                    # Basic workflow components
│   ├── langgraph_trip_planner.py # Basic LangGraph structure
│   ├── studio_graph.py           # LangGraph Studio entry point
│   ├── models.py                 # Essential data models
│   ├── requirements.txt          # Minimal dependencies
│   ├── env_template.txt          # Environment configuration
│   └── langgraph.json           # LangGraph Studio configuration
└── README.md                    # This file
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd the_trip_planner
   ```

2. **Navigate to server directory**:
   ```bash
   cd server
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the server directory:
   ```bash
   cp env_template.txt .env
   # Edit .env with your actual values
   ```

5. **Enable required APIs**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

6. **Set up LangSmith** (optional but recommended):
   - Sign up at https://smith.langchain.com/
   - Get your API key
   - Add it to your `.env` file

## 🚀 Running the Service

### Option 1: Using the startup script (Recommended)
```bash
python start.py
```

### Option 2: Direct LangGraph Studio run
```bash
cd server
pip install langgraph-cli
langgraph up
```

### Option 3: Test basic structure
```bash
cd server
python langgraph_trip_planner.py
```

## 🌐 Access Points

Once running, you can access:

- **LangGraph Studio**: http://localhost:8123
- **LangGraph Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123

## 📚 Workflow Components

### Basic Structure

The LangGraph workflow has a minimal structure ready for development:

1. **Placeholder Node**: Basic node that can be replaced with your logic
2. **TripState**: Simple state management class
3. **LangGraphTripPlanner**: Main planner class with basic structure

### Core Functions

| Function | Description |
|----------|-------------|
| `plan_trip_with_langgraph()` | Basic function for LangGraph Studio testing |
| `langgraph_planner` | Basic LangGraph workflow instance |
| `placeholder_node()` | Placeholder node ready for replacement |

### Workflow Flow

```
User Input → Placeholder Node → Basic Response
```

The placeholder node currently just returns the state unchanged, ready for you to implement your own logic.

## 🧹 Clean Structure

This project has been cleaned to include only essential components:

- ✅ **Minimal dependencies**: Only required packages
- ✅ **Clean code**: No unused functions or imports
- ✅ **Basic models**: Only essential data structures
- ✅ **Simple workflow**: Ready for your implementation
- ✅ **No complex logic**: Clean slate for development

## 💡 Next Steps

1. **Add your nodes**: Replace the placeholder node with your logic
2. **Implement tools**: Add function calling capabilities
3. **Enhance workflow**: Build your multi-step process
4. **Test in Studio**: Use LangGraph Studio for development
