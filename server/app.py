"""
FastAPI application for Trip Planner with Authentication
Main application that integrates LangGraph workflow with Facebook authentication
"""

import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import authentication components
from auth.routes import router as auth_router
from auth.middleware import get_current_user_optional
from auth.models import UserResponse

# Import user profile components
from user_profile.routes import router as user_profile_router

# Import LangGraph components
from main_graph import create_graph
from state import MainState
from langchain_core.messages import HumanMessage, AIMessage

# Global variables for graph and auth
graph = None
auth_enabled = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global graph
    
    # Initialize LangGraph
    try:
        graph = create_graph()
        print("✅ LangGraph initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LangGraph: {e}")
        raise
    
    yield
    
    # Cleanup
    print("🛑 Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Trip Planner API",
    description="AI-powered trip planning with Facebook authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)
app.include_router(user_profile_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint - serve the main HTML page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")


@app.get("/sdk")
async def sdk_demo():
    """Facebook SDK demo page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/facebook-sdk.html")

@app.get("/preferences")
async def preferences_demo():
    """User preferences demo page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/user-preferences.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "graph_initialized": graph is not None,
        "auth_enabled": auth_enabled
    }


@app.post("/plan-trip")
async def plan_trip(
    request: dict,
    current_user: UserResponse = Depends(get_current_user_optional)
):
    """
    Plan a trip using LangGraph workflow
    """
    if not graph:
        raise HTTPException(status_code=500, detail="Trip planning service not available")
    
    # Extract message from request
    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": current_user.id if current_user else None,
            "user_name": current_user.name if current_user else "Anonymous"
        }
        
        # Run the graph
        result = graph.invoke(initial_state)
        
        # Extract the response
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                response_content = last_message.content
            else:
                response_content = str(last_message)
        else:
            response_content = "No response generated"
        
        return {
            "response": response_content,
            "user_id": current_user.id if current_user else None,
            "authenticated": current_user is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trip planning error: {str(e)}")


@app.get("/user-trips")
async def get_user_trips(current_user: UserResponse = Depends(get_current_user_optional)):
    """
    Get user's trip history (placeholder for future implementation)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Placeholder implementation
    return {
        "message": "User trip history feature coming soon",
        "user_id": current_user.id,
        "trips": []
    }


@app.post("/save-trip")
async def save_trip(
    trip_data: dict,
    current_user: UserResponse = Depends(get_current_user_optional)
):
    """
    Save a trip plan for the user (placeholder for future implementation)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Placeholder implementation
    return {
        "message": "Trip saved successfully",
        "user_id": current_user.id,
        "trip_id": "placeholder_id"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting Trip Planner API on {host}:{port}")
    print(f"🔐 Authentication: {'Enabled' if auth_enabled else 'Disabled'}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
