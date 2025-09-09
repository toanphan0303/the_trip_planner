"""
Base error class for the trip planner application
"""

from typing import Optional, Dict, Any
from abc import ABC


class BaseTripPlannerError(Exception, ABC):
    """
    Base exception class for all trip planner errors.
    
    This class provides a common interface for all custom errors in the application,
    including error codes, context information, and user-friendly messages.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Initialize the base error.
        
        Args:
            message: Technical error message for logging/debugging
            error_code: Unique error code for programmatic handling
            context: Additional context information (e.g., request data, parameters)
            user_message: User-friendly error message to display
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.user_message = user_message or message
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary representation.
        
        Returns:
            Dictionary containing error information
        """
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'user_message': self.user_message,
            'context': self.context
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"{self.__class__.__name__}: {self.message}"
    
    def __repr__(self) -> str:
        """Detailed string representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"error_code='{self.error_code}', "
            f"context={self.context})"
        )
