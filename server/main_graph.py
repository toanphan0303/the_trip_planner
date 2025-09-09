"""
LangGraph Studio Entry Point
This file exposes the compiled graph for LangGraph Studio
"""

import os
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from graph_node.base_node import BaseNode
from models.ai_models import create_vertex_ai_model
from state import MainState
from enum import Enum
from langgraph.prebuilt import ToolNode
from tools.main_graph_tools import plan_trip_for_destinations
from langchain_core.runnables import RunnableConfig
from typing import Optional
from langchain_core.messages.utils import trim_messages
from constant import MESSAGE_SIZE_LIMIT
from prompt.graph_prompt import MAIN_GRAPH_SYSTEM_PROMPT

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
tools = [plan_trip_for_destinations]

class MainNodeName(str, Enum):
    MAIN_ASSISTANT = "main_assistant"
    MAIN_TOOLS = "main_tools"

class MainAssistantNode(BaseNode):
    """
    Assistant node that processes user input and generates a response
    """
    def __init__(self):
        super().__init__(name="main_assistant", description="Assistant node that processes user input and generates a response")
        self.ai_model = create_vertex_ai_model("gemini-flash")
    
    def execute(self, state: MainState, config: Optional[RunnableConfig] = None) -> MainState:
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
            "content": MAIN_GRAPH_SYSTEM_PROMPT
        }
        
        # Use LangChain's bind_tools approach
        llm_with_tools = self.ai_model.bind_tools(tools)
        response = llm_with_tools.invoke([system_message] + input_messages)
        return {"messages": [response]}

    def transform(self, state: MainState, config: Optional[RunnableConfig] = None):
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
            return MainNodeName.MAIN_TOOLS
        return END


def create_graph():
    """
    Create and return the compiled LangGraph for Studio
    """
    # Create the graph
    workflow = StateGraph(MainState)

    # Create assistant node instance
    assistant_node = MainAssistantNode()
    
    # Create tool node for function calling
    tool_node = ToolNode(tools)

    # Add the nodes
    workflow.add_node(MainNodeName.MAIN_ASSISTANT, assistant_node.execute)
    workflow.add_node(MainNodeName.MAIN_TOOLS, tool_node)

    # Set entry point
    workflow.set_entry_point(MainNodeName.MAIN_ASSISTANT)

    # Add conditional edge from assistant to tools or end
    workflow.add_conditional_edges(MainNodeName.MAIN_ASSISTANT, assistant_node.transform, [MainNodeName.MAIN_TOOLS, END])

    # Add edge from tools back to assistant
    workflow.add_edge(MainNodeName.MAIN_TOOLS, MainNodeName.MAIN_ASSISTANT)

    # Compile the graph
    return workflow.compile()


# This is the graph that LangGraph Studio will discover
graph = create_graph()

