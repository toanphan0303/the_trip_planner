"""
Specific error classes for the trip planner application
"""

from typing import Optional, Dict, Any, List
from .base_error import BaseTripPlannerError


class UserClarificationError(BaseTripPlannerError):
    """
    Error raised when user input requires clarification.
    
    This error is used when the AI needs to ask the user for additional
    information to provide better recommendations or complete a request.
    """
    
    def __init__(
        self,
        clarification_questions: List[str],
        message: str = "User input requires clarification",
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Initialize user clarification error.
        
        Args:
            clarification_questions: List of questions to ask the user
            message: Technical error message
            context: Additional context information
            user_message: User-friendly message explaining why clarification is needed
        """
        self.clarification_questions = clarification_questions
        self.error_code = "USER_CLARIFICATION_REQUIRED"
        
        # Create user-friendly message if not provided
        if not user_message:
            if len(clarification_questions) == 1:
                user_message = f"To provide better recommendations, {clarification_questions[0].lower()}"
            else:
                user_message = "To provide better recommendations, I need some additional information:"
        
        super().__init__(
            message=message,
            error_code=self.error_code,
            context=context,
            user_message=user_message
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary with clarification questions."""
        error_dict = super().to_dict()
        error_dict['clarification_questions'] = self.clarification_questions
        return error_dict

class ToolExecutionError(BaseTripPlannerError):
    """
    Error raised when a tool execution fails.
    
    This error is used when a tool cannot complete its task due to
    missing preconditions, invalid state, or execution failures.
    """
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize tool execution error.
        
        Args:
            message: Error message
            tool_name: Name of the tool that failed
            context: Additional context information
        """
        self.tool_name = tool_name
        
        super().__init__(
            message=message,
            error_code="TOOL_EXECUTION_ERROR",
            context=context,
            user_message=message
        )


class ValidationError(BaseTripPlannerError):
    """
    Error raised when input validation fails.
    
    This error is used for parameter validation, data format validation,
    and other input validation scenarios.
    """
    
    def __init__(
        self,
        field: str,
        value: Any,
        validation_message: str,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            field: Name of the field that failed validation
            value: The value that failed validation
            validation_message: Specific validation error message
            message: Technical error message
            context: Additional context information
        """
        self.field = field
        self.value = value
        self.validation_message = validation_message
        
        if not message:
            message = f"Validation failed for field '{field}': {validation_message}"
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context=context,
            user_message=f"Invalid input for {field}: {validation_message}"
        )

