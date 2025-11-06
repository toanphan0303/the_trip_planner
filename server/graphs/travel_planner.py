"""
LangGraph Studio Entry Point
This file exposes the compiled graph for LangGraph Studio
"""

import os
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from graph_node.base_node import BaseNode
from models.ai_models import create_vertex_ai_model, GeminiAI
from state import TravelPlannerState
from enum import Enum
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from typing import Optional
from langchain_core.messages.utils import trim_messages
from constant import MESSAGE_SIZE_LIMIT
from prompt.graph_prompt import TRAVEL_PLANNER_SYSTEM_PROMPT
from logger import get_logger

logger = get_logger(__name__)
from tools.travel_planner_tools import (
    set_travel_style,
    upsert_preference_override,
    geocode_destination,
)

# Load environment variables
load_dotenv()

# Remote debugging setup (only when enabled)
if os.getenv("ENABLE_REMOTE_DEBUG", "false").lower() == "true":
    try:
        import debugpy
        debug_port = int(os.getenv("DEBUG_PORT", "5678"))
        debugpy.listen(("0.0.0.0", debug_port))
        print(f"🐛 Remote debugging enabled on port {debug_port}")
        print("Connect your debugger to this port to debug LangSmith Studio invocations")
    except ImportError:
        print("debugpy not available for remote debugging")
    except Exception as e:
        print(f"Failed to setup remote debugging: {e}")

# Function declarations for Gemini
tools = [
    set_travel_style,
    upsert_preference_override,
    geocode_destination,
]

class TravelPlannerNodeName(str, Enum):
    TRAVEL_PLANNER_ASSISTANT = "travel_planner_assistant"
    TRAVEL_PLANNER_TOOLS = "travel_planner_tools"
    PROCESS_TOOL_RESULTS = "process_tool_results"

class TravelPlannerAssistantNode(BaseNode):
    """
    Assistant node that processes user input and generates a response
    """
    def __init__(self):
        super().__init__(name="travel_planner_assistant", description="Assistant node that processes user input and generates a response")
        self.ai_model = create_vertex_ai_model(GeminiAI.GEMINI_FLASH)
    
    def execute(self, state: TravelPlannerState, config: Optional[RunnableConfig] = None) -> TravelPlannerState:
        """
        Process user input and generate a response
        """        
        message = state.get("messages", [])

        input_messages = trim_messages(
            message, 
            max_tokens=MESSAGE_SIZE_LIMIT, 
            token_counter=len,  # Count messages instead of tokens for simplicity
            strategy="last", 
            start_on="human", 
            )
        
        # Add system message to help AI understand when to use tools
        system_message = {
            "role": "system",
            "content": TRAVEL_PLANNER_SYSTEM_PROMPT
        }
        
        # Use LangChain's bind_tools approach
        llm_with_tools = self.ai_model.bind_tools(tools)
        response = llm_with_tools.invoke([system_message] + input_messages)
        return {"messages": [response]}

    def transfer(self, state: TravelPlannerState, config: Optional[RunnableConfig] = None):
        messages_key: str = "messages"
        if isinstance(state, list):
            ai_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
                ai_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return TravelPlannerNodeName.TRAVEL_PLANNER_TOOLS
        return END


def process_tool_results(state: TravelPlannerState, config: Optional[RunnableConfig] = None) -> dict:
    """
    Process tool results and extract state updates from tool return values.
    Tools return dicts which get serialized to JSON in ToolMessage.content.
    This node extracts those dicts and returns them to update state.
    """
    import json
    
    messages = state.get("messages", [])
    if not messages:
        return {}
    
    # Get the last message (should be a ToolMessage)
    last_message = messages[-1]
    
    # Check if it's a tool message
    if hasattr(last_message, "name") and hasattr(last_message, "content"):
        try:
            # Parse the tool output (dict serialized to JSON string)
            tool_output = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content
            
            # Extract state updates from tool output
            state_updates = {}
            
            # Tools return dicts with state fields to update
            # Extract only the state fields (not "message" or "error")
            for key, value in tool_output.items():
                if key not in ["message", "error"]:
                    state_updates[key] = value
                    logger.info(f"Updating state.{key} from {last_message.name}")
            
            return state_updates
            
        except Exception as e:
            logger.error(f"Error processing tool result from {last_message.name}: {e}")
    
    return {}


def create_graph_travel_planner():
    """
    Create and return the compiled LangGraph for Studio with Redis checkpointer
    
    Redis checkpointer auto-saves entire state (including preference_override)
    after every node execution.
    """
    # Create the graph
    workflow = StateGraph(TravelPlannerState)

    # Create assistant node instance
    assistant_node = TravelPlannerAssistantNode()
    
    # Create tool node - tools receive state as first parameter
    tool_node = ToolNode(tools)

    # Add the nodes
    workflow.add_node(TravelPlannerNodeName.TRAVEL_PLANNER_ASSISTANT, assistant_node.execute)
    workflow.add_node(TravelPlannerNodeName.TRAVEL_PLANNER_TOOLS, tool_node)
    workflow.add_node(TravelPlannerNodeName.PROCESS_TOOL_RESULTS, process_tool_results)

    # Set entry point
    workflow.set_entry_point(TravelPlannerNodeName.TRAVEL_PLANNER_ASSISTANT)

    # Add conditional edge from assistant to tools or end
    workflow.add_conditional_edges(TravelPlannerNodeName.TRAVEL_PLANNER_ASSISTANT, assistant_node.transfer, [TravelPlannerNodeName.TRAVEL_PLANNER_TOOLS, END])

    # Add edge from tools to processing node (extracts state updates from tool returns)
    workflow.add_edge(TravelPlannerNodeName.TRAVEL_PLANNER_TOOLS, TravelPlannerNodeName.PROCESS_TOOL_RESULTS)
    
    # Add edge from processing back to assistant
    workflow.add_edge(TravelPlannerNodeName.PROCESS_TOOL_RESULTS, TravelPlannerNodeName.TRAVEL_PLANNER_ASSISTANT)

    # Note: LangGraph Studio provides automatic persistence
    # State is auto-saved after every node execution
    return workflow.compile()


# This is the graph that LangGraph Studio will discover
graph = create_graph_travel_planner()

