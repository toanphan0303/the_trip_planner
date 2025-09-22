"""
Point of Interest data models for places and events
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from .yelp_model import YelpPointOfInterest, PriceLevel
from .foursquare_model import FoursquarePlace


class POIType(str, Enum):
    """Point of Interest type enumeration"""
    place = "place"
    event = "event"


class Source(str, Enum):
    """Data source enumeration"""
    google_places = "google_places"
    ticketmaster = "ticketmaster"
    yelp = "yelp"
    foursquare = "foursquare"


class Location(BaseModel):
    """Location coordinates"""
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")


class PriceRange(BaseModel):
    """Price range information for events"""
    min: Optional[float] = Field(None, description="Minimum price")
    max: Optional[float] = Field(None, description="Maximum price")
    currency: Optional[str] = Field(None, description="Currency code (e.g., USD)")


class PointOfInterest(BaseModel):
    """Point of Interest model for places and events"""
    
    # Core identification
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Display name")
    type: POIType = Field(..., description="Type of point of interest")
    category: str = Field(..., description="Category or type (e.g., 'restaurant', 'Music')")
    description: str = Field(..., description="Human-readable description")
    
    # Location information
    address: str = Field("", description="Formatted address")
    location: Location = Field(default_factory=Location, description="Geographic coordinates")
    
    # Rating and pricing
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating (0-5)")
    user_rating_count: Optional[int] = Field(None, ge=0, description="Number of user ratings")
    price_level: Optional[PriceLevel] = Field(None, description="Price level")
    
    # Business information
    business_status: Optional[str] = Field(None, description="Business operational status")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Place-specific fields
    is_open: Optional[bool] = Field(None, description="Whether the place is currently open")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="Opening hours information")
    
    # Event-specific fields
    event_date: Optional[str] = Field(None, description="Event date (YYYY-MM-DD)")
    event_time: Optional[str] = Field(None, description="Event time (HH:MM)")
    venue_name: Optional[str] = Field(None, description="Venue name for events")
    price_range: Optional[PriceRange] = Field(None, description="Price range for events")
    image_url: Optional[str] = Field(None, description="Image URL for events")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="List of tags/categories")
    source: Source = Field(..., description="Data source")
    enhanced_by: List[Source] = Field(default_factory=list, description="List of services that enhanced this data")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Original API response data")
    
    # Source-specific data
    yelp_data: Optional[YelpPointOfInterest] = Field(None, description="Yelp-specific data when source is yelp")
    foursquare_data: Optional[FoursquarePlace] = Field(None, description="Foursquare-specific data when source is foursquare")
    
    # Computed fields
    distance_km: Optional[float] = Field(None, ge=0, description="Distance from center point in kilometers")
    
    def is_worth_visiting(self, min_rating: float = 3.5, min_review_count: int = 10, min_score: float = 0.6) -> bool:
        """
        Determine if this location is worth visiting based on rating, user rating count, and visitability score.
        
        Args:
            min_rating: Minimum rating threshold (default: 3.5)
            min_review_count: Minimum number of reviews required (default: 10)
            min_score: Minimum visitability score threshold (default: 0.6)
            
        Returns:
            True if the location meets the criteria for being worth visiting
        """
        # If no rating data, consider it not worth visiting
        if self.rating is None or self.user_rating_count is None:
            return False
        
        # Check if rating meets minimum threshold
        if self.rating < min_rating:
            return False
        
        # Check if review count meets minimum threshold
        if self.user_rating_count < min_review_count:
            return False
        
        # Calculate and check visitability score
        visitability_score = self._calculate_visitability_score()
        if visitability_score < min_score:
            return False
        
        return True
    
    def _calculate_visitability_score(self) -> float:
        """
        Calculate a visitability score (0-1) based on rating and review count.
        Higher scores indicate more worth visiting.
        
        Returns:
            Float between 0 and 1 representing visitability score
        """
        # If no rating data, return 0
        if self.rating is None or self.user_rating_count is None:
            return 0.0
        
        # Normalize rating to 0-1 scale (assuming 5-star max)
        rating_score = self.rating / 5.0
        
        # Normalize review count to 0-1 scale (using log scale for diminishing returns)
        # More reviews = higher confidence, but with diminishing returns
        import math
        review_score = min(1.0, math.log10(max(1, self.user_rating_count)) / 3.0)  # log10(1000) ≈ 3
        
        # Weighted combination: 70% rating, 30% review confidence
        visitability_score = (0.7 * rating_score) + (0.3 * review_score)
        
        return min(1.0, max(0.0, visitability_score))
    
    def get_visitability_score(self) -> float:
        """
        Get the visitability score for this location.
        
        Returns:
            Float between 0 and 1 representing visitability score
        """
        return self._calculate_visitability_score()
    
    def is_enhanced_by(self, source: Source) -> bool:
        """
        Check if this POI has been enhanced by a specific source.
        
        Args:
            source: Source to check for enhancement
            
        Returns:
            True if enhanced by the specified source
        """
        return source in self.enhanced_by
    
    def get_enhancement_summary(self) -> str:
        """
        Get a human-readable summary of data enhancements.
        
        Returns:
            String describing the enhancement sources
        """
        if not self.enhanced_by:
            return f"Primary data from {self.source.value}"
        
        enhanced_sources = [source.value for source in self.enhanced_by]
        return f"Primary data from {self.source.value}, enhanced by {', '.join(enhanced_sources)}"
    
    def get_yelp_rating(self) -> Optional[float]:
        """Get rating from Yelp data if available"""
        if self.yelp_data and self.yelp_data.rating is not None:
            return self.yelp_data.rating
        return self.rating
    
    def get_yelp_review_count(self) -> Optional[int]:
        """Get review count from Yelp data if available"""
        if self.yelp_data:
            return self.yelp_data.review_count
        return self.user_rating_count
    
    def get_yelp_categories(self) -> List[str]:
        """Get categories from Yelp data if available"""
        if self.yelp_data:
            return self.yelp_data.get_all_categories()
        return self.tags
    
    def get_yelp_phone(self) -> Optional[str]:
        """Get phone number from Yelp data if available"""
        if self.yelp_data:
            return self.yelp_data.display_phone or self.yelp_data.phone
        return None
    
    def get_yelp_website(self) -> Optional[str]:
        """Get website URL from Yelp data if available"""
        if self.yelp_data and self.yelp_data.url:
            return self.yelp_data.url
        return self.website
    
    def is_yelp_business_open(self) -> Optional[bool]:
        """Check if Yelp business is currently open"""
        if self.yelp_data:
            return self.yelp_data.is_currently_open()
        return self.is_open
    
    def get_yelp_price_level(self) -> Optional[PriceLevel]:
        """Get price level from Yelp data if available"""
        if self.yelp_data:
            return self.yelp_data.get_price_level()
        return self.price_level
    
    def get_foursquare_rating(self) -> Optional[float]:
        """Get rating from Foursquare data if available (normalized to 0-5 scale)"""
        if self.foursquare_data:
            return self.foursquare_data.get_rating_normalized()
        return self.rating
    
    def get_foursquare_checkin_count(self) -> Optional[int]:
        """Get check-in count from Foursquare data if available"""
        if self.foursquare_data:
            return self.foursquare_data.get_checkin_count()
        return None
    
    def get_foursquare_tip_count(self) -> Optional[int]:
        """Get tip count from Foursquare data if available"""
        if self.foursquare_data:
            return self.foursquare_data.get_tip_count()
        return None
    
    def get_foursquare_categories(self) -> List[str]:
        """Get categories from Foursquare data if available"""
        if self.foursquare_data:
            return self.foursquare_data.get_all_category_names()
        return self.tags
    
    def get_foursquare_phone(self) -> Optional[str]:
        """Get phone number from Foursquare data if available"""
        if self.foursquare_data:
            return self.foursquare_data.get_phone_number()
        return None
    
    def get_foursquare_website(self) -> Optional[str]:
        """Get website URL from Foursquare data if available"""
        if self.foursquare_data:
            return self.foursquare_data.get_website_url()
        return self.website
    
    def is_foursquare_venue_open(self) -> Optional[bool]:
        """Check if Foursquare venue is currently open"""
        if self.foursquare_data:
            return self.foursquare_data.is_currently_open()
        return self.is_open
    
    def get_foursquare_price_level(self) -> Optional[int]:
        """Get price level from Foursquare data if available (1-4 scale)"""
        if self.foursquare_data:
            return self.foursquare_data.get_price_level()
        return None
    
    def get_foursquare_photo_url(self, size: str = "300x300") -> Optional[str]:
        """Get photo URL from Foursquare data if available"""
        if self.foursquare_data:
            return self.foursquare_data.get_photo_url(size)
        return self.image_url
    
    def get_foursquare_primary_category(self) -> Optional[str]:
        """Get primary category from Foursquare data if available"""
        if self.foursquare_data:
            return self.foursquare_data.get_primary_category_name()
        return self.category


class PointOfInterestSearchResult(BaseModel):
    """Container for Point of Interest search results"""
    
    items: List[PointOfInterest] = Field(default_factory=list, description="List of points of interest")
    total_count: int = Field(0, ge=0, description="Total number of items found")
    places_count: int = Field(0, ge=0, description="Number of places found")
    events_count: int = Field(0, ge=0, description="Number of events found")
    
    # Search metadata
    search_center: Optional[Location] = Field(None, description="Center point of search")
    search_radius_km: Optional[float] = Field(None, ge=0, description="Search radius in kilometers")
    search_date: datetime = Field(default_factory=datetime.now, description="When the search was performed")
    
    def add_item(self, item: PointOfInterest) -> None:
        """Add an item to the results and update counters"""
        self.items.append(item)
        self.total_count += 1
        
        if item.type == "place":
            self.places_count += 1
        elif item.type == "event":
            self.events_count += 1
    
    def filter_by_distance(self, max_distance_km: float) -> 'PointOfInterestSearchResult':
        """Filter results by distance and return new result object"""
        filtered_items = [
            item for item in self.items 
            if item.distance_km is None or item.distance_km <= max_distance_km
        ]
        
        return PointOfInterestSearchResult(
            items=filtered_items,
            total_count=len(filtered_items),
            places_count=len([item for item in filtered_items if item.type == "place"]),
            events_count=len([item for item in filtered_items if item.type == "event"]),
            search_center=self.search_center,
            search_radius_km=max_distance_km,
            search_date=self.search_date
        )
    
    def sort_by_rating_and_distance(self) -> 'PointOfInterestSearchResult':
        """Sort items by rating (descending) then distance (ascending)"""
        def sort_key(item: PointOfInterest) -> tuple:
            rating = item.rating or 0
            distance = item.distance_km or 0
            return (-rating, distance)  # Negative rating for descending order
        
        sorted_items = sorted(self.items, key=sort_key)
        
        return PointOfInterestSearchResult(
            items=sorted_items,
            total_count=self.total_count,
            places_count=self.places_count,
            events_count=self.events_count,
            search_center=self.search_center,
            search_radius_km=self.search_radius_km,
            search_date=self.search_date
        )
    
    def get_places_only(self) -> List[PointOfInterest]:
        """Get only place items"""
        return [item for item in self.items if item.type == "place"]
    
    def get_events_only(self) -> List[PointOfInterest]:
        """Get only event items"""
        return [item for item in self.items if item.type == "event"]
    
    def get_by_category(self, category: str) -> List[PointOfInterest]:
        """Get items by category"""
        return [item for item in self.items if item.category.lower() == category.lower()]
    
    def get_top_rated(self, limit: int = 10) -> List[PointOfInterest]:
        """Get top-rated items"""
        rated_items = [item for item in self.items if item.rating is not None]
        return sorted(rated_items, key=lambda x: x.rating or 0, reverse=True)[:limit]
    
    def filter_worth_visiting(self, min_rating: float = 3.5, min_review_count: int = 10, min_score: float = 0.6) -> 'PointOfInterestSearchResult':
        """Filter results to only include locations worth visiting"""
        worth_visiting_items = [
            item for item in self.items 
            if item.is_worth_visiting(min_rating=min_rating, min_review_count=min_review_count, min_score=min_score)
        ]
        
        return PointOfInterestSearchResult(
            items=worth_visiting_items,
            total_count=len(worth_visiting_items),
            places_count=len([item for item in worth_visiting_items if item.type == "place"]),
            events_count=len([item for item in worth_visiting_items if item.type == "event"]),
            search_center=self.search_center,
            search_radius_km=self.search_radius_km,
            search_date=self.search_date
        )
    
    def sort_by_visitability(self) -> 'PointOfInterestSearchResult':
        """Sort items by visitability score (descending)"""
        sorted_items = sorted(self.items, key=lambda x: x.get_visitability_score(), reverse=True)
        
        return PointOfInterestSearchResult(
            items=sorted_items,
            total_count=self.total_count,
            places_count=self.places_count,
            events_count=self.events_count,
            search_center=self.search_center,
            search_radius_km=self.search_radius_km,
            search_date=self.search_date
        )


# Backward compatibility - keep the old function but return the new model
def create_point_of_interest_from_dict(item_dict: Dict[str, Any]) -> PointOfInterest:
    """Create a PointOfInterest from a dictionary (for backward compatibility)"""
    return PointOfInterest(**item_dict)


def create_point_of_interest_search_result_from_items(items: List[Dict[str, Any]]) -> PointOfInterestSearchResult:
    """Create a PointOfInterestSearchResult from a list of item dictionaries"""
    poi_items = [create_point_of_interest_from_dict(item) for item in items]
    
    return PointOfInterestSearchResult(
        items=poi_items,
        total_count=len(poi_items),
        places_count=len([item for item in poi_items if item.type == "place"]),
        events_count=len([item for item in poi_items if item.type == "event"])
    )


