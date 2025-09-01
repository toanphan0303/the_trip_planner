"""
LangGraph Studio Entry Point
This file exposes the compiled graph for LangGraph Studio
"""

import os
from typing import Dict, Any, List, TypedDict, Annotated
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Load environment variables
load_dotenv()

class ChatState(TypedDict):
    """State for the chat workflow"""
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    user_input: Annotated[str, "The current user input"]
    response: Annotated[str, "The AI response"]

def chat_node(state: ChatState) -> ChatState:
    """
    Chat node that processes user input and generates a response
    """
    # Get the current user input
    user_input = state["user_input"]
    
    # Create a simple response (you can replace this with your actual AI logic)
    if "hello" in user_input.lower():
        response = "Hello! I'm your trip planning assistant. How can I help you plan your next adventure?"
    elif "trip" in user_input.lower() or "travel" in user_input.lower():
        response = "Great! I'd love to help you plan a trip. What's your destination and how many days are you thinking?"
    elif "budget" in user_input.lower():
        response = "Budget is important! What's your budget range for this trip?"
    else:
        response = "I'm here to help with trip planning! You can ask me about destinations, budgets, itineraries, and more."
    
    # Add the user message to the conversation
    messages = state["messages"] + [HumanMessage(content=user_input)]
    
    # Add the AI response to the conversation
    messages.append(AIMessage(content=response))
    
    return {
        "messages": messages,
        "user_input": user_input,
        "response": response
    }

def create_graph():
    """
    Create and return the compiled LangGraph for Studio
    """
    # Create the graph
    workflow = StateGraph(ChatState)
    
    # Add the chat node
    workflow.add_node("chat", chat_node)
    
    # Set entry point
    workflow.set_entry_point("chat")
    
    # Add edge to end
    workflow.add_edge("chat", END)
    
    # Compile and return the graph
    return workflow.compile()

# This is the graph that LangGraph Studio will discover
graph = create_graph()
