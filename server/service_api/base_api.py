"""
Base API class for handling HTTP requests
"""

import os
import httpx
import json
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
    
    def _log_failed_request(self, method: str, url: str, status_code: int, response_text: str, 
                           params: Optional[Dict[str, Any]] = None, 
                           data: Optional[Dict[str, Any]] = None, 
                           headers: Optional[Dict[str, str]] = None):
        """Log detailed request information for failed HTTP requests"""
        print(f"\n❌ HTTP Request Failed: {method} {url}")
        print(f"   Status Code: {status_code}")
        print(f"   Response: {response_text}")
        
        if params:
            print(f"   Query Parameters: {json.dumps(params, indent=2)}")
        
        if data:
            print(f"   Request Body: {json.dumps(data, indent=2)}")
        
        if headers:
            # Mask sensitive headers like API keys
            safe_headers = {}
            for key, value in headers.items():
                if 'key' in key.lower() or 'token' in key.lower() or 'auth' in key.lower():
                    safe_headers[key] = f"{value[:10]}..." if len(value) > 10 else "***"
                else:
                    safe_headers[key] = value
            print(f"   Headers: {json.dumps(safe_headers, indent=2)}")
        
        print("=" * 80)
    
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
            
            # Log request details if status is not OK
            if not resp.is_success:
                try:
                    response_text = resp.text
                except Exception:
                    response_text = "Unable to read response text"
                
                self._log_failed_request("GET", url, resp.status_code, response_text, 
                                       params=params, headers=headers)
            
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
            
            # Log request details if status is not OK
            if not resp.is_success:
                try:
                    response_text = resp.text
                except Exception:
                    response_text = "Unable to read response text"
                
                self._log_failed_request("POST", url, resp.status_code, response_text, 
                                       data=data, headers=headers)
            
            resp.raise_for_status()
            return resp.json()
    
    async def _get_async(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make async GET request
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            
        Returns:
            JSON response as dict
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=headers)
            
            # Log request details if status is not OK
            if not resp.is_success:
                try:
                    response_text = resp.text
                except Exception:
                    response_text = "Unable to read response text"
                
                self._log_failed_request("GET", url, resp.status_code, response_text, 
                                       params=params, headers=headers)
            
            resp.raise_for_status()
            return resp.json()
    
    async def _post_async(self, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make async POST request
        
        Args:
            url: Request URL
            data: Request body data
            headers: Request headers
            
        Returns:
            JSON response as dict
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=data, headers=headers)
            
            # Log request details if status is not OK
            if not resp.is_success:
                try:
                    response_text = resp.text
                except Exception:
                    response_text = "Unable to read response text"
                
                self._log_failed_request("POST", url, resp.status_code, response_text, 
                                       data=data, headers=headers)
            
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
