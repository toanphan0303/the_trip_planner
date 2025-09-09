"""
Base Node for LangGraph Workflows
Minimal implementation with essential components
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Dict, Optional

# Type variable for state
StateType = TypeVar('StateType')

class BaseNode(ABC, Generic[StateType]):
    """
    Minimal base class for LangGraph nodes
    
    Essential components:
    - name: Node identifier
    - description: What the node does
    - execute: Main logic function
    - transform: Data transformation function (optional)
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize the base node
        
        Args:
            name: Unique name of the node
            description: Description of what the node does
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, state: StateType, config: Optional[Any] = None) -> StateType:
        """
        Execute the main node logic
        
        Args:
            state: Input state
            config: Optional configuration (RunnableConfig or similar)
            
        Returns:
            Updated state
        """
        pass
    
    def transform(self, state: StateType, config: Optional[Any] = None) -> StateType:
        """
        Transform the state (optional override)
        
        Args:
            state: Input state
            config: Optional configuration (RunnableConfig or similar)
            
        Returns:
            Transformed state
        """
        return state
    
    def __call__(self, state: StateType, config: Optional[Any] = None) -> StateType:
        """Make the node callable"""
        # Apply transform, then execute
        transformed_state = self.transform(state, config)
        return self.execute(transformed_state, config)
    
    def __str__(self) -> str:
        return f"BaseNode(name='{self.name}', description='{self.description}')"
    
    def __repr__(self) -> str:
        return self.__str__()
