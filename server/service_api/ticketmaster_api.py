"""
Ticketmaster API client using base API infrastructure
"""

from typing import Optional, Dict, Any, List
from .base_api import BaseAPI
from cache.mongo_cache_decorator import mongo_cached


class TicketmasterAPI(BaseAPI):
    """Ticketmaster API client for event discovery services"""
    
    def __init__(self):
        super().__init__("TICKETMASTER_API_KEY")
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Any:
        """Parse response based on API type - implemented by specific methods"""
        return response_data
    
    @mongo_cached("ticketmaster_events_search")
    def search_events(
        self,
        keyword: Optional[str] = None,
        city: Optional[List[str]] = None,
        state_code: Optional[str] = None,
        country_code: Optional[str] = None,
        classification_name: Optional[str] = None,
        classification_id: Optional[str] = None,
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        size: int = 20,
        page: int = 0,
        sort: Optional[str] = None,
        radius: Optional[int] = None,
        unit: Optional[str] = None,
        latlong: Optional[str] = None,
        include_test: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for events using Ticketmaster Discovery API.
        
        Args:
            keyword: Keyword to search for in event names, descriptions, etc.
            city: City name to search in
            state_code: State code (e.g., 'CA', 'NY')
            country_code: Country code (e.g., 'US', 'CA')
            classification_name: Event classification (e.g., 'Music', 'Sports', 'Arts & Theatre')
            classification_id: Specific classification ID
            start_date_time: Start date/time filter (ISO 8601 format)
            end_date_time: End date/time filter (ISO 8601 format)
            size: Number of results per page (max 200)
            page: Page number (0-based)
            sort: Sort order ('date,asc', 'date,desc', 'name,asc', 'name,desc', 'relevance,desc')
            radius: Search radius in miles or kilometers
            unit: Unit for radius ('miles' or 'km')
            latlong: Latitude and longitude (format: "lat,long")
            
        Returns:
            Dict with Ticketmaster's event discovery data
        """
        endpoint = "https://app.ticketmaster.com/discovery/v2/events.json"
        
        params = {
            "apikey": self.api_key,
            "size": min(max(size, 1), 200),  # Limit between 1-200
            "page": max(page, 0)
        }
        
        # Add optional parameters
        if keyword:
            params["keyword"] = keyword
        if city:
            # Handle city as array - join multiple cities with comma
            if isinstance(city, list):
                params["city"] = ",".join(city)
            else:
                params["city"] = city
        if state_code:
            params["stateCode"] = state_code
        if country_code:
            params["countryCode"] = country_code
        if classification_name:
            params["classificationName"] = classification_name
        if classification_id:
            params["classificationId"] = classification_id
        if start_date_time:
            params["startDateTime"] = start_date_time
        if end_date_time:
            params["endDateTime"] = end_date_time
        if sort:
            params["sort"] = sort
        if radius:
            params["radius"] = radius
        if unit:
            params["unit"] = unit
        if latlong:
            params["latlong"] = latlong
        if include_test:
            params["includeTest"] = include_test
        
        response_data = self._get(endpoint, params=params)
        
        return response_data
    
    def get_event_details(self, event_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific event.
        
        Args:
            event_id: The Ticketmaster event ID
            
        Returns:
            Dict with detailed event information
        """
        endpoint = f"https://app.ticketmaster.com/discovery/v2/events/{event_id}.json"
        
        params = {
            "apikey": self.api_key
        }
        
        response_data = self._get(endpoint, params=params)
        
        return response_data
    
    def search_attractions(
        self,
        keyword: Optional[str] = None,
        classification_name: Optional[str] = None,
        classification_id: Optional[str] = None,
        size: int = 20,
        page: int = 0,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for attractions (artists, venues, etc.) using Ticketmaster Discovery API.
        
        Args:
            keyword: Keyword to search for in attraction names
            classification_name: Attraction classification
            classification_id: Specific classification ID
            size: Number of results per page (max 200)
            page: Page number (0-based)
            sort: Sort order
            
        Returns:
            Dict with Ticketmaster's attraction discovery data
        """
        endpoint = "https://app.ticketmaster.com/discovery/v2/attractions.json"
        
        params = {
            "apikey": self.api_key,
            "size": min(max(size, 1), 200),
            "page": max(page, 0)
        }
        
        if keyword:
            params["keyword"] = keyword
        if classification_name:
            params["classificationName"] = classification_name
        if classification_id:
            params["classificationId"] = classification_id
        if sort:
            params["sort"] = sort
        
        response_data = self._get(endpoint, params=params)
        
        return response_data
    
    def search_venues(
        self,
        keyword: Optional[str] = None,
        city: Optional[str] = None,
        state_code: Optional[str] = None,
        country_code: Optional[str] = None,
        size: int = 20,
        page: int = 0,
        sort: Optional[str] = None,
        radius: Optional[int] = None,
        unit: Optional[str] = None,
        latlong: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for venues using Ticketmaster Discovery API.
        
        Args:
            keyword: Keyword to search for in venue names
            city: City name to search in
            state_code: State code (e.g., 'CA', 'NY')
            country_code: Country code (e.g., 'US', 'CA')
            size: Number of results per page (max 200)
            page: Page number (0-based)
            sort: Sort order
            radius: Search radius in miles or kilometers
            unit: Unit for radius ('miles' or 'km')
            latlong: Latitude and longitude (format: "lat,long")
            
        Returns:
            Dict with Ticketmaster's venue discovery data
        """
        endpoint = "https://app.ticketmaster.com/discovery/v2/venues.json"
        
        params = {
            "apikey": self.api_key,
            "size": min(max(size, 1), 200),
            "page": max(page, 0)
        }
        
        if keyword:
            params["keyword"] = keyword
        if city:
            params["city"] = city
        if state_code:
            params["stateCode"] = state_code
        if country_code:
            params["countryCode"] = country_code
        if sort:
            params["sort"] = sort
        if radius:
            params["radius"] = radius
        if unit:
            params["unit"] = unit
        if latlong:
            params["latlong"] = latlong
        
        response_data = self._get(endpoint, params=params)
        
        return response_data


# Convenience functions for backward compatibility
_ticketmaster_api = TicketmasterAPI()

def ticketmaster_search_events(
    keyword: Optional[str] = None,
    city: Optional[List[str]] = None,
    state_code: Optional[str] = None,
    country_code: Optional[str] = None,
    classification_name: Optional[str] = None,
    size: int = 20,
    include_test: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for event search"""
    return _ticketmaster_api.search_events(
        keyword=keyword,
        city=city,
        state_code=state_code,
        country_code=country_code,
        classification_name=classification_name,
        size=size,
        include_test=include_test,
        **kwargs
    )

def ticketmaster_get_event_details(event_id: str) -> Dict[str, Any]:
    """Convenience function for getting event details"""
    return _ticketmaster_api.get_event_details(event_id)

def ticketmaster_search_attractions(
    keyword: Optional[str] = None,
    classification_name: Optional[str] = None,
    size: int = 20,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for attraction search"""
    return _ticketmaster_api.search_attractions(
        keyword=keyword,
        classification_name=classification_name,
        size=size,
        **kwargs
    )

def ticketmaster_search_venues(
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    state_code: Optional[str] = None,
    country_code: Optional[str] = None,
    size: int = 20,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for venue search"""
    return _ticketmaster_api.search_venues(
        keyword=keyword,
        city=city,
        state_code=state_code,
        country_code=country_code,
        size=size,
        **kwargs
    )
