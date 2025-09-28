"""
Google Places API Models - Using Google's Built-in Models
This module uses Google's built-in request/response models directly
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pydantic import BaseModel, Field


@dataclass
class GooglePlacesRequest:
    """Wrapper for Google Places API requests using built-in models"""
    text_query: str
    max_result_count: int = 20
    language_code: Optional[str] = None
    region_code: Optional[str] = None
    included_type: Optional[str] = None
    open_now: Optional[bool] = None
    min_rating: Optional[float] = None
    price_levels: Optional[List[str]] = None
    location_bias: Optional[Dict[str, Any]] = None
    location_restriction: Optional[Dict[str, Any]] = None

    def to_google_request(self) -> Dict[str, Any]:
        """Convert to Google's built-in TextSearchRequest format"""
        request = {
            "textQuery": self.text_query,
            "maxResultCount": min(max(self.max_result_count, 1), 20)
        }
        
        if self.language_code:
            request["languageCode"] = self.language_code
        if self.region_code:
            request["regionCode"] = self.region_code
        if self.included_type:
            request["includedType"] = self.included_type
        if self.open_now is not None:
            request["openNow"] = self.open_now
        if self.min_rating is not None:
            request["minRating"] = max(0.0, min(self.min_rating, 5.0))
        if self.price_levels:
            request["priceLevels"] = self.price_levels
        if self.location_bias:
            request["locationBias"] = self.location_bias
        if self.location_restriction:
            request["locationRestriction"] = self.location_restriction
            
        return request


class GooglePlace(BaseModel):
    """Clean model for Google Places based on actual API structure"""
    
    # Core identification
    id: str = Field(..., description="Google Place ID")
    name: str = Field(..., description="Place name")
    display_name: Optional[str] = Field(None, description="Display name from LocalizedText")
    formatted_address: str = Field("", description="Formatted address")
    short_formatted_address: Optional[str] = Field(None, description="Short formatted address")
    
    # Location
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    
    # Place classification
    types: List[str] = Field(default_factory=list, description="Place types")
    primary_type: Optional[str] = Field(None, description="Primary place type")
    primary_type_display_name: Optional[str] = Field(None, description="Primary type display name")
    
    # Business info
    rating: Optional[float] = Field(None, ge=0, le=5, description="Place rating (0-5)")
    user_rating_count: Optional[int] = Field(None, ge=0, description="Number of user ratings")
    price_level: Optional[str] = Field(None, description="Price level enum")
    business_status: Optional[str] = Field(None, description="Business status")
    
    # Contact info
    national_phone: Optional[str] = Field(None, description="National phone number")
    international_phone: Optional[str] = Field(None, description="International phone number")
    website: Optional[str] = Field(None, description="Website URI")
    google_maps_uri: Optional[str] = Field(None, description="Google Maps URI")
    
    # Hours
    is_open: Optional[bool] = Field(None, description="Whether currently open")
    
    # Restaurant-specific attributes
    takeout: Optional[bool] = Field(None, description="Offers takeout")
    delivery: Optional[bool] = Field(None, description="Offers delivery")
    dine_in: Optional[bool] = Field(None, description="Offers dine-in")
    curbside_pickup: Optional[bool] = Field(None, description="Offers curbside pickup")
    reservable: Optional[bool] = Field(None, description="Accepts reservations")
    
    # Dining attributes
    serves_breakfast: Optional[bool] = Field(None, description="Serves breakfast")
    serves_lunch: Optional[bool] = Field(None, description="Serves lunch")
    serves_dinner: Optional[bool] = Field(None, description="Serves dinner")
    serves_beer: Optional[bool] = Field(None, description="Serves beer")
    serves_wine: Optional[bool] = Field(None, description="Serves wine")
    serves_coffee: Optional[bool] = Field(None, description="Serves coffee")
    
    # Amenities
    outdoor_seating: Optional[bool] = Field(None, description="Has outdoor seating")
    good_for_children: Optional[bool] = Field(None, description="Good for children")
    good_for_groups: Optional[bool] = Field(None, description="Good for groups")
    allows_dogs: Optional[bool] = Field(None, description="Allows dogs")
    restroom: Optional[bool] = Field(None, description="Has restroom")
    
    @classmethod
    def from_google_place(cls, place_data: Dict[str, Any]) -> 'GooglePlace':
        """Create GooglePlace from Google's place data"""
        location = place_data.get("location", {})
        display_name_obj = place_data.get("displayName", {})
        primary_type_display_obj = place_data.get("primaryTypeDisplayName", {})
        current_hours = place_data.get("currentOpeningHours", {})
        
        return cls(
            id=place_data.get("id", ""),
            name=place_data.get("name", ""),
            display_name=display_name_obj.get("text") if display_name_obj else None,
            formatted_address=place_data.get("formattedAddress", ""),
            short_formatted_address=place_data.get("shortFormattedAddress"),
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
            types=place_data.get("types", []),
            primary_type=place_data.get("primaryType"),
            primary_type_display_name=primary_type_display_obj.get("text") if primary_type_display_obj else None,
            rating=place_data.get("rating"),
            user_rating_count=place_data.get("userRatingCount"),
            price_level=place_data.get("priceLevel"),
            business_status=place_data.get("businessStatus"),
            national_phone=place_data.get("nationalPhoneNumber"),
            international_phone=place_data.get("internationalPhoneNumber"),
            website=place_data.get("websiteUri"),
            google_maps_uri=place_data.get("googleMapsUri"),
            is_open=current_hours.get("openNow") if current_hours else None,
            takeout=place_data.get("takeout"),
            delivery=place_data.get("delivery"),
            dine_in=place_data.get("dineIn"),
            curbside_pickup=place_data.get("curbsidePickup"),
            reservable=place_data.get("reservable"),
            serves_breakfast=place_data.get("servesBreakfast"),
            serves_lunch=place_data.get("servesLunch"),
            serves_dinner=place_data.get("servesDinner"),
            serves_beer=place_data.get("servesBeer"),
            serves_wine=place_data.get("servesWine"),
            serves_coffee=place_data.get("servesCoffee"),
            outdoor_seating=place_data.get("outdoorSeating"),
            good_for_children=place_data.get("goodForChildren"),
            good_for_groups=place_data.get("goodForGroups"),
            allows_dogs=place_data.get("allowsDogs"),
            restroom=place_data.get("restroom")
        )
    
    def get_available_fields(self) -> Dict[str, Any]:
        """
        Extract all available fields that have actual values.
        Excludes None values, empty strings, empty lists, and empty dicts.
        
        Returns:
            Dict containing only fields with meaningful values
        """
        available_fields = {}
        
        # Core identification
        if self.id:
            available_fields["id"] = self.id
        if self.name:
            available_fields["name"] = self.name
        if self.display_name:
            available_fields["display_name"] = self.display_name
        if self.formatted_address:
            available_fields["formatted_address"] = self.formatted_address
        if self.short_formatted_address:
            available_fields["short_formatted_address"] = self.short_formatted_address
        
        # Location
        if self.latitude is not None:
            available_fields["latitude"] = self.latitude
        if self.longitude is not None:
            available_fields["longitude"] = self.longitude
        
        # Place classification
        if self.types:
            available_fields["types"] = self.types
        if self.primary_type:
            available_fields["primary_type"] = self.primary_type
        if self.primary_type_display_name:
            available_fields["primary_type_display_name"] = self.primary_type_display_name
        
        # Business info
        if self.rating is not None:
            available_fields["rating"] = self.rating
        if self.user_rating_count is not None:
            available_fields["user_rating_count"] = self.user_rating_count
        if self.price_level:
            available_fields["price_level"] = self.price_level
        if self.business_status:
            available_fields["business_status"] = self.business_status
        
        # Contact info
        if self.national_phone:
            available_fields["national_phone"] = self.national_phone
        if self.international_phone:
            available_fields["international_phone"] = self.international_phone
        if self.website:
            available_fields["website"] = self.website
        if self.google_maps_uri:
            available_fields["google_maps_uri"] = self.google_maps_uri
        
        # Hours
        if self.is_open is not None:
            available_fields["is_open"] = self.is_open
        
        # Restaurant-specific attributes
        if self.takeout is not None:
            available_fields["takeout"] = self.takeout
        if self.delivery is not None:
            available_fields["delivery"] = self.delivery
        if self.dine_in is not None:
            available_fields["dine_in"] = self.dine_in
        if self.curbside_pickup is not None:
            available_fields["curbside_pickup"] = self.curbside_pickup
        if self.reservable is not None:
            available_fields["reservable"] = self.reservable
        
        # Dining attributes
        if self.serves_breakfast is not None:
            available_fields["serves_breakfast"] = self.serves_breakfast
        if self.serves_lunch is not None:
            available_fields["serves_lunch"] = self.serves_lunch
        if self.serves_dinner is not None:
            available_fields["serves_dinner"] = self.serves_dinner
        if self.serves_beer is not None:
            available_fields["serves_beer"] = self.serves_beer
        if self.serves_wine is not None:
            available_fields["serves_wine"] = self.serves_wine
        if self.serves_coffee is not None:
            available_fields["serves_coffee"] = self.serves_coffee
        
        # Amenities
        if self.outdoor_seating is not None:
            available_fields["outdoor_seating"] = self.outdoor_seating
        if self.good_for_children is not None:
            available_fields["good_for_children"] = self.good_for_children
        if self.good_for_groups is not None:
            available_fields["good_for_groups"] = self.good_for_groups
        if self.allows_dogs is not None:
            available_fields["allows_dogs"] = self.allows_dogs
        if self.restroom is not None:
            available_fields["restroom"] = self.restroom
        
        return available_fields


@dataclass
class GooglePlacesResponse:
    """Wrapper for Google Places API responses using GooglePlace models"""
    places: List[GooglePlace]
    next_page_token: Optional[str] = None
    
    @classmethod
    def from_google_response(cls, response_data: Dict[str, Any]) -> 'GooglePlacesResponse':
        """Create from Google's built-in TextSearchResponse format"""
        places_data = response_data.get("places", [])
        places = [GooglePlace.from_google_place(place_data) for place_data in places_data]
        
        return cls(
            places=places,
            next_page_token=response_data.get("nextPageToken")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB serialization"""
        return {
            "places": [place.dict() for place in self.places],
            "next_page_token": self.next_page_token
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GooglePlacesResponse':
        """Create from dictionary (for MongoDB deserialization)"""
        places = [GooglePlace(**place_data) for place_data in data.get("places", [])]
        return cls(
            places=places,
            next_page_token=data.get("next_page_token")
        )
    
    def handle_multiple_places(self) -> None:
        """Handle multiple places by raising UserClarificationError with options"""
        if len(self.places) > 1:
            from error.trip_planner_errors import UserClarificationError
            
            option_places = "\n".join(
                [place.display_name or place.name for place in self.places]
            )
            raise UserClarificationError(
                clarification_questions=[
                    "Please provide more information about the destination ",
                    option_places,
                ]
            )


# Field masks for different use cases
class GooglePlacesFieldMasks:
    """Predefined field masks for Google Places API requests"""
    
    BASIC = "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.types"
    
    DETAILED = (
        "places.id,places.displayName,places.formattedAddress,places.location,"
        "places.rating,places.types,places.priceLevel,places.businessStatus,"
        "places.currentOpeningHours,places.websiteUri"
    )
    
    COMPREHENSIVE = (
        "places.id,places.displayName,places.formattedAddress,places.location,"
        "places.rating,places.types,places.priceLevel,places.businessStatus,"
        "places.currentOpeningHours,places.websiteUri,places.userRatingCount,"
        "places.reviews,places.photos"
    )


# Backward compatibility aliases (for existing code)
PlacesSearchResponse = GooglePlacesResponse
PlacesNearbyResponse = GooglePlacesResponse