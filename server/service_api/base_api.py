"""
Base API class for handling HTTP requests
"""

import os
import httpx
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseAPI(ABC):
    """Base class for API clients with common HTTP functionality"""
    
    def __init__(self, api_key_env_var: str, base_timeout: float = 15.0):
        """
        Initialize base API client
        
        Args:
            api_key_env_var: Environment variable name for API key
            base_timeout: Default timeout for requests
        """
        self.api_key = os.getenv(api_key_env_var)
        if not self.api_key:
            raise ValueError(f"{api_key_env_var} is not set in environment")
        self.timeout = base_timeout
    
    def _get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make GET request
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            
        Returns:
            JSON response as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
    
    def _post(self, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make POST request
        
        Args:
            url: Request URL
            data: Request body data
            headers: Request headers
            
        Returns:
            JSON response as dict
        """
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=data, headers=headers)
            resp.raise_for_status()
            return resp.json()
    
    @abstractmethod
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """
        Parse API response into Python object
        
        Args:
            response_data: Raw JSON response
            
        Returns:
            Parsed Python object
        """
        pass
