"""
Yelp-specific data models for business information
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PriceLevel(str, Enum):
    """Price level enumeration"""
    INEXPENSIVE = "PRICE_LEVEL_INEXPENSIVE"
    MODERATE = "PRICE_LEVEL_MODERATE"
    EXPENSIVE = "PRICE_LEVEL_EXPENSIVE"
    VERY_EXPENSIVE = "PRICE_LEVEL_VERY_EXPENSIVE"


class YelpCategory(BaseModel):
    """Yelp category model"""
    alias: str = Field(..., description="Category alias")
    title: str = Field(..., description="Category title")


class YelpLocation(BaseModel):
    """Yelp location model"""
    address1: Optional[str] = Field(None, description="Primary address")
    address2: Optional[str] = Field(None, description="Secondary address")
    address3: Optional[str] = Field(None, description="Tertiary address")
    city: Optional[str] = Field(None, description="City")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    country: Optional[str] = Field(None, description="Country code")
    state: Optional[str] = Field(None, description="State code")
    display_address: List[str] = Field(default_factory=list, description="Formatted display address")
    cross_streets: Optional[str] = Field(None, description="Cross streets")


class YelpCoordinates(BaseModel):
    """Yelp coordinates model"""
    latitude: Union[str, float, None] = Field(None, description="Latitude")
    longitude: Union[str, float, None] = Field(None, description="Longitude")
    
    @field_validator('latitude', 'longitude', mode='before')
    @classmethod
    def convert_to_float(cls, v):
        """Convert string coordinates to float"""
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class YelpHoursOpen(BaseModel):
    """Yelp hours open model"""
    is_overnight: bool = Field(False, description="Whether hours extend overnight")
    start: str = Field(..., description="Opening time (HHMM format)")
    end: str = Field(..., description="Closing time (HHMM format)")
    day: int = Field(..., description="Day of week (0=Monday, 6=Sunday)")


class YelpHours(BaseModel):
    """Yelp hours model"""
    open: List[YelpHoursOpen] = Field(default_factory=list, description="Opening hours")
    hour_type: Optional[str] = Field(None, description="Type of hours (e.g., REGULAR)")
    is_open_now: bool = Field(False, description="Whether currently open")


class YelpSpecialHours(BaseModel):
    """Yelp special hours model"""
    date: str = Field(..., description="Special date (YYYY-MM-DD)")
    is_closed: bool = Field(False, description="Whether closed on this date")
    start: Optional[str] = Field(None, description="Special opening time")
    end: Optional[str] = Field(None, description="Special closing time")
    is_overnight: Optional[bool] = Field(None, description="Whether special hours extend overnight")


class YelpMessaging(BaseModel):
    """Yelp messaging model"""
    url: str = Field(..., description="Messaging URL")
    use_case_text: str = Field(..., description="Use case text for messaging")
    response_rate: Optional[str] = Field(None, description="Response rate (0-1)")
    response_time: Optional[int] = Field(None, description="Estimated response time in seconds")
    is_enabled: Optional[bool] = Field(None, description="Whether messaging is enabled")


class YelpPhotoDetails(BaseModel):
    """Yelp photo details model (Premium tier)"""
    photo_id: str = Field(..., description="Unique photo identifier")
    url: str = Field(..., description="Photo URL")
    caption: Optional[str] = Field(None, description="Photo caption")
    width: Optional[int] = Field(None, description="Photo width")
    height: Optional[int] = Field(None, description="Photo height")
    is_user_submitted: Optional[bool] = Field(None, description="Whether photo is user submitted")
    user_id: Optional[str] = Field(None, description="User ID who submitted photo")
    label: Optional[str] = Field(None, description="Photo label")


class YelpPopularityScore(BaseModel):
    """Yelp popularity score model (Premium tier)"""
    primary_category: str = Field(..., description="Primary category")
    score: str = Field(..., description="Popularity score")


class YelpRAPC(BaseModel):
    """Request a Phone Call model (Premium tier)"""
    is_enabled: bool = Field(False, description="Whether RAPC is enabled")
    is_eligible: bool = Field(False, description="Whether business is eligible for RAPC")


class YelpPointOfInterest(BaseModel):
    """Yelp-specific point of interest model - Complete business details response"""
    
    # Core Yelp fields (required)
    id: str = Field(..., description="Yelp Encrypted Business ID")
    alias: str = Field(..., description="Unique Yelp alias of this business")
    name: str = Field(..., description="Name of this business")
    is_claimed: bool = Field(False, description="Whether business has been claimed by a business owner")
    is_closed: bool = Field(False, description="Whether business has been (permanently) closed")
    url: Optional[str] = Field(None, description="URL for business page on Yelp")
    phone: str = Field("", description="Phone number of the business")
    display_phone: str = Field("", description="Phone number formatted nicely for display")
    review_count: int = Field(0, description="Number of reviews for this business")
    categories: List[YelpCategory] = Field(default_factory=list, description="List of category title and alias pairs")
    rating: Union[str, float, None] = Field(None, description="Rating for this business (1, 1.5, ... 4.5, 5)")
    coordinates: YelpCoordinates = Field(default_factory=YelpCoordinates, description="Coordinates of this business")
    location: YelpLocation = Field(default_factory=YelpLocation, description="Location of this business")
    photos: List[str] = Field(default_factory=list, description="URLs of up to three photos of the business")
    hours: List[YelpHours] = Field(default_factory=list, description="Regular business hours")
    
    # Optional fields
    image_url: Optional[str] = Field(None, description="URL of photo for this business")
    transactions: List[str] = Field(default_factory=list, description="List of Yelp transactions (pickup, delivery, restaurant_reservation)")
    price: Optional[str] = Field(None, description="Price level ($, $$, $$$, $$$$)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Various features or facilities provided by the business")
    special_hours: List[YelpSpecialHours] = Field(default_factory=list, description="Out of the ordinary hours for the business")
    messaging: Optional[YelpMessaging] = Field(None, description="Information and action links for messaging with this business")
    
    # Premium tier fields (optional)
    date_opened: Optional[str] = Field(None, description="Business opening date")
    date_closed: Optional[str] = Field(None, description="Business closing date")
    photo_count: Optional[int] = Field(None, description="Total number of photos (Premium tier)")
    photo_details: List[YelpPhotoDetails] = Field(default_factory=list, description="List of photo details (Premium tier)")
    yelp_menu_url: Optional[str] = Field(None, description="Business menu URL (Premium tier)")
    cbsa: Optional[str] = Field(None, description="Core based statistical area (Premium tier)")
    popularity_score: Optional[YelpPopularityScore] = Field(None, description="Popularity score (Premium tier)")
    rapc: Optional[YelpRAPC] = Field(None, description="Request a Phone Call information (Premium tier)")
    
    # Distance field (for search results)
    distance: Optional[str] = Field(None, description="Distance in meters from search location")
    
    @field_validator('price', mode='before')
    @classmethod
    def validate_price(cls, v):
        """Ensure price is always a string"""
        if v is None:
            return None
        return str(v)
    
    @field_validator('rating', mode='before')
    @classmethod
    def validate_rating(cls, v):
        """Convert rating to float if it's a string"""
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
    
    def get_primary_category(self) -> Optional[str]:
        """Get the primary category title"""
        if self.categories:
            return self.categories[0].title
        return None
    
    def get_all_categories(self) -> List[str]:
        """Get all category titles"""
        return [cat.title for cat in self.categories]
    
    def is_currently_open(self) -> bool:
        """Check if business is currently open"""
        if not self.hours:
            return False
        return any(hour.is_open_now for hour in self.hours)
    
    def get_price_level(self) -> Optional[PriceLevel]:
        """Convert Yelp price to PriceLevel enum"""
        if not self.price:
            return None
        
        price_mapping = {
            "$": PriceLevel.INEXPENSIVE,
            "$$": PriceLevel.MODERATE,
            "$$$": PriceLevel.EXPENSIVE,
            "$$$$": PriceLevel.VERY_EXPENSIVE
        }
        return price_mapping.get(self.price)
    
    def get_distance_meters(self) -> Optional[float]:
        """Get distance in meters as float"""
        if not self.distance:
            return None
        try:
            return float(self.distance)
        except (ValueError, TypeError):
            return None
    
    def has_transaction(self, transaction_type: str) -> bool:
        """Check if business supports a specific transaction type"""
        return transaction_type in self.transactions
    
    def get_photo_urls(self) -> List[str]:
        """Get all photo URLs (main image + photos list)"""
        urls = []
        if self.image_url:
            urls.append(self.image_url)
        urls.extend(self.photos)
        return urls
    
    def get_full_address(self) -> str:
        """Get formatted full address"""
        if self.location.display_address:
            return ", ".join(self.location.display_address)
        
        parts = []
        if self.location.address1:
            parts.append(self.location.address1)
        if self.location.city:
            parts.append(self.location.city)
        if self.location.state:
            parts.append(self.location.state)
        if self.location.zip_code:
            parts.append(self.location.zip_code)
        if self.location.country:
            parts.append(self.location.country)
        
        return ", ".join(parts)
    
    def is_premium_tier_available(self) -> bool:
        """Check if premium tier data is available"""
        return any([
            self.photo_count is not None,
            self.photo_details,
            self.yelp_menu_url,
            self.cbsa,
            self.popularity_score,
            self.rapc
        ])
