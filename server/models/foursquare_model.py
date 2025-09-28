"""
Foursquare-specific data models for Places API v3
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class FoursquareCategoryType(str, Enum):
    """Foursquare category type enumeration"""
    MAIN = "main"
    SUB = "sub"


class FoursquareCategory(BaseModel):
    """Foursquare category model for Places API v3"""
    fsq_category_id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    short_name: Optional[str] = Field(None, description="Short form of category name")
    plural_name: Optional[str] = Field(None, description="Plural form of category name")
    icon: Optional[Dict[str, str]] = Field(None, description="Icon information with prefix/suffix")


class FoursquareLocation(BaseModel):
    """Foursquare location model for Places API v3"""
    address: Optional[str] = Field(None, description="Street address")
    locality: Optional[str] = Field(None, description="City")
    region: Optional[str] = Field(None, description="State/region")
    postcode: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(None, description="Country code")
    formatted_address: Optional[str] = Field(None, description="Formatted address string")


class FoursquareExtendedLocation(BaseModel):
    """Foursquare extended location model"""
    dma: Optional[str] = Field(None, description="Designated Market Area")
    census_block_id: Optional[str] = Field(None, description="Census block ID")


class FoursquareSocialMedia(BaseModel):
    """Foursquare social media model"""
    twitter: Optional[str] = Field(None, description="Twitter handle")
    facebook: Optional[str] = Field(None, description="Facebook page")
    instagram: Optional[str] = Field(None, description="Instagram handle")


class FoursquareRelatedPlace(BaseModel):
    """Foursquare related place model"""
    fsq_place_id: str = Field(..., description="Related place ID")
    name: str = Field(..., description="Related place name")
    categories: List[FoursquareCategory] = Field(default_factory=list, description="Related place categories")


class FoursquareRelatedPlaces(BaseModel):
    """Foursquare related places container"""
    parent: Optional[FoursquareRelatedPlace] = Field(None, description="Parent place")


class FoursquarePlace(BaseModel):
    """Foursquare Place model for Places API v3"""
    
    # Core identification
    fsq_place_id: str = Field(..., description="Foursquare place ID")
    name: str = Field(..., description="Place name")
    
    # Location information
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    distance: Optional[int] = Field(None, description="Distance from search center in meters")
    
    # Address and location details
    location: FoursquareLocation = Field(default_factory=FoursquareLocation, description="Location information")
    extended_location: Optional[FoursquareExtendedLocation] = Field(None, description="Extended location data")
    
    # Categories
    categories: List[FoursquareCategory] = Field(default_factory=list, description="Place categories")
    
    # Dates
    date_created: Optional[str] = Field(None, description="Creation date")
    date_refreshed: Optional[str] = Field(None, description="Last refresh date")
    
    # Links and references
    link: Optional[str] = Field(None, description="Foursquare link path")
    placemaker_url: Optional[str] = Field(None, description="Placemaker review URL")
    
    # Contact information
    tel: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Social media
    social_media: FoursquareSocialMedia = Field(default_factory=FoursquareSocialMedia, description="Social media links")
    
    # Related places
    related_places: FoursquareRelatedPlaces = Field(default_factory=FoursquareRelatedPlaces, description="Related places")
    
    # Additional fields that might be present
    rating: Optional[float] = Field(None, description="Place rating")
    price: Optional[int] = Field(None, description="Price level (1-4)")
    hours: Optional[Dict[str, Any]] = Field(None, description="Opening hours")
    photos: Optional[List[Dict[str, Any]]] = Field(None, description="Photos")
    tips: Optional[List[Dict[str, Any]]] = Field(None, description="Tips")
    
    @field_validator('rating', mode='before')
    @classmethod
    def validate_rating(cls, v):
        """Ensure rating is within valid range"""
        if v is None:
            return None
        return max(0.0, min(float(v), 10.0))  # Foursquare uses 0-10 scale
    
    def get_primary_category(self) -> Optional[FoursquareCategory]:
        """Get the primary category"""
        return self.categories[0] if self.categories else None
    


class FoursquareGeoBounds(BaseModel):
    """Foursquare geo bounds model"""
    circle: Optional[Dict[str, Any]] = Field(None, description="Circle bounds with center and radius")


class FoursquareContext(BaseModel):
    """Foursquare context model"""
    geo_bounds: Optional[FoursquareGeoBounds] = Field(None, description="Geographic bounds")


class FoursquareSearchResponse(BaseModel):
    """Foursquare search response model for Places API v3"""
    results: List[FoursquarePlace] = Field(default_factory=list, description="List of places")
    context: Optional[FoursquareContext] = Field(None, description="Search context")
    


class FoursquareTip(BaseModel):
    """Foursquare tip model for venue tips"""
    fsq_tip_id: str = Field(..., description="Foursquare tip ID")
    created_at: str = Field(..., description="Tip creation date (ISO 8601)")
    text: str = Field(..., description="Tip text content")
    
    def get_created_date(self) -> Optional[str]:
        """Get creation date in readable format"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return self.created_at


class FoursquarePlacesMatchContext(BaseModel):
    """Foursquare places match context model"""
    latitude: float = Field(..., description="Search latitude")
    longitude: float = Field(..., description="Search longitude")


class FoursquarePlacesMatchResponse(BaseModel):
    """Foursquare places match response model"""
    place: FoursquarePlace = Field(..., description="Matched place information")
    match_score: float = Field(..., description="Match confidence score (0-1)")
    context: FoursquarePlacesMatchContext = Field(..., description="Search context")
    
    def get_match_percentage(self) -> float:
        """Get match score as percentage"""
        return round(self.match_score * 100, 2)
    
    def is_high_confidence_match(self, threshold: float = 0.7) -> bool:
        """Check if this is a high confidence match"""
        return self.match_score >= threshold


class FoursquareVenueTipsResponse(BaseModel):
    """Foursquare venue tips response model"""
    tips: List[FoursquareTip] = Field(default_factory=list, description="List of venue tips")
    
    def get_tips_count(self) -> int:
        """Get number of tips"""
        return len(self.tips)
    


# Request Models for API Parameters

class FoursquareSortOrder(str, Enum):
    """Foursquare sort order enumeration"""
    DISTANCE = "DISTANCE"
    POPULARITY = "POPULARITY"
    RATING = "RATING"
    NEWEST = "NEWEST"
    POPULAR = "POPULAR"


class FoursquareVenueSearchRequest(BaseModel):
    """Request model for Foursquare venue search"""
    query: str = Field(..., description="Search query (e.g., 'coffee', 'restaurants')")
    ll: Optional[str] = Field(None, description="Latitude and longitude (e.g., '37.7749,-122.4194')")
    near: Optional[str] = Field(None, description="Location to search near (e.g., 'San Francisco, CA')")
    radius: Optional[int] = Field(None, ge=1, le=100000, description="Search radius in meters (max 100000)")
    categories: Optional[List[str]] = Field(None, description="List of category IDs to filter by")
    price: Optional[List[int]] = Field(None, description="List of price levels to filter by (1-4)")
    open_now: Optional[bool] = Field(None, description="Filter for venues currently open")
    sort: Optional[FoursquareSortOrder] = Field(None, description="Sort results by")
    limit: int = Field(50, ge=1, le=50, description="Number of results to return (max 50)")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    
    @model_validator(mode='after')
    def validate_location(self):
        """Validate that either ll or near is provided"""
        if not self.ll and not self.near:
            raise ValueError("Either 'll' (latitude,longitude) or 'near' location must be provided")
        return self
    
    def to_params(self) -> Dict[str, Any]:
        """Convert to API parameters"""
        params = {
            "query": self.query,
            "limit": self.limit,
        }
        
        if self.ll:
            params["ll"] = self.ll
        if self.near:
            params["near"] = self.near
        if self.radius:
            params["radius"] = min(self.radius, 100000)
        if self.categories:
            params["categories"] = ",".join(self.categories)
        if self.price:
            params["price"] = ",".join(map(str, self.price))
        if self.open_now:
            params["open_now"] = "true"
        if self.sort:
            params["sort"] = self.sort.value
        if self.offset:
            params["offset"] = self.offset
            
        return params


class FoursquareVenueDetailsRequest(BaseModel):
    """Request model for Foursquare venue details"""
    venue_id: str = Field(..., description="Foursquare venue ID")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to return")
    
    def to_params(self) -> Dict[str, Any]:
        """Convert to API parameters"""
        params = {}
        if self.fields:
            params["fields"] = self.fields
        return params


class FoursquareVenueTipsRequest(BaseModel):
    """Request model for Foursquare venue tips"""
    venue_id: str = Field(..., description="Foursquare venue ID")
    limit: int = Field(10, ge=1, le=50, description="Number of tips to return (max 50)")
    sort: FoursquareSortOrder = Field(FoursquareSortOrder.POPULAR, description="Sort order for tips")
    
    def to_params(self) -> Dict[str, Any]:
        """Convert to API parameters"""
        return {
            "limit": self.limit,
            "sort": self.sort.value,
        }


class FoursquarePlacesMatchRequest(BaseModel):
    """Request model for Foursquare places match"""
    name: str = Field(..., max_length=64, description="Name of the place to match")
    address: Optional[str] = Field(None, max_length=64, description="Street address of the place")
    city: Optional[str] = Field(None, max_length=64, description="City where the place is located")
    state: Optional[str] = Field(None, max_length=64, description="State or region name")
    postal_code: Optional[str] = Field(None, max_length=12, description="Postal code")
    cc: Optional[str] = Field(None, min_length=2, max_length=2, description="Country code (ISO 3166-1 alpha-2)")
    ll: Optional[str] = Field(None, description="Latitude,longitude coordinates")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to return")
    
    @model_validator(mode='after')
    def validate_location(self):
        """Validate that either ll or (address, city, cc) is provided"""
        has_coordinates = bool(self.ll)
        has_address_info = bool(self.address and self.city and self.cc)
        
        if not has_coordinates and not has_address_info:
            raise ValueError("Either 'll' (coordinates) or ('address', 'city', 'cc') must be provided")
        
        return self
    
    def to_params(self) -> Dict[str, Any]:
        """Convert to API parameters"""
        params = {"name": self.name}
        
        if self.address is not None:
            params["address"] = self.address
        if self.city is not None:
            params["city"] = self.city
        if self.state is not None:
            params["state"] = self.state
        if self.postal_code is not None:
            params["postal_code"] = self.postal_code
        if self.cc is not None:
            params["cc"] = self.cc
        if self.ll is not None:
            params["ll"] = self.ll
        if self.fields is not None:
            params["fields"] = self.fields
            
        return params


# Backward compatibility aliases
FoursquareVenue = FoursquarePlace
FoursquareVenueDetailResponse = FoursquareSearchResponse