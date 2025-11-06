"""
Base models for tool responses
Shared response structures used across all tools
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class WorkflowStep(BaseModel):
    """Information about the current workflow step and next actions"""
    current_step: str = Field(..., description="Name of the current step that was executed")
    next_step: Optional[str] = Field(None, description="Description of the suggested next step")

class ToolError(BaseModel):
    """Information about an error"""
    message: str = Field(..., description="Error message")

class ToolResponse(BaseModel):
    """Response from a tool"""
    success: bool = Field(..., description="Whether the tool call was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Data returned from the tool")
    error: Optional[str] = Field(None, description="Error message if the tool call failed")
    workflow: Optional[WorkflowStep] = Field(None, description="Information about the workflow")


