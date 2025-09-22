"""
Foursquare-specific data models for Places API v3
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator
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
    
    def get_all_category_names(self) -> List[str]:
        """Get all category names"""
        return [cat.name for cat in self.categories]
    
    def get_primary_category_name(self) -> Optional[str]:
        """Get the primary category name"""
        primary = self.get_primary_category()
        return primary.name if primary else None
    
    def get_formatted_address(self) -> str:
        """Get formatted address string"""
        if self.location.formatted_address:
            return self.location.formatted_address
        
        address_parts = []
        if self.location.address:
            address_parts.append(self.location.address)
        if self.location.locality and self.location.region:
            address_parts.append(f"{self.location.locality}, {self.location.region}")
        elif self.location.locality:
            address_parts.append(self.location.locality)
        if self.location.postcode:
            address_parts.append(self.location.postcode)
        
        return ", ".join(address_parts)
    
    def get_phone_number(self) -> Optional[str]:
        """Get phone number"""
        return self.tel
    
    def get_website_url(self) -> Optional[str]:
        """Get website URL"""
        return self.website
    
    def get_price_level(self) -> Optional[int]:
        """Get price level (1-4)"""
        return self.price
    
    def get_rating_normalized(self) -> Optional[float]:
        """Get rating normalized to 0-5 scale (Foursquare uses 0-10)"""
        if self.rating is None:
            return None
        return self.rating / 2.0  # Convert from 0-10 to 0-5 scale
    
    def get_distance_km(self) -> Optional[float]:
        """Get distance in kilometers"""
        if self.distance is None:
            return None
        return self.distance / 1000.0


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
    
    def get_place_by_id(self, place_id: str) -> Optional[FoursquarePlace]:
        """Get place by ID"""
        for place in self.results:
            if place.fsq_place_id == place_id:
                return place
        return None
    
    def get_places_by_category(self, category_name: str) -> List[FoursquarePlace]:
        """Get places by category name"""
        return [
            place for place in self.results 
            if any(cat.name.lower() == category_name.lower() for cat in place.categories)
        ]
    
    def get_places_with_phone(self) -> List[FoursquarePlace]:
        """Get places that have phone numbers"""
        return [place for place in self.results if place.tel]
    
    def get_places_with_website(self) -> List[FoursquarePlace]:
        """Get places that have websites"""
        return [place for place in self.results if place.website]


# Backward compatibility aliases
FoursquareVenue = FoursquarePlace
FoursquareVenueDetailResponse = FoursquareSearchResponse