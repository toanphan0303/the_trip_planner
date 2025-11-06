"""
Google Places API Models - Matching Google's Actual API Structure
This module uses Pydantic models that match Google's nested structure exactly
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pydantic import BaseModel, Field


# ============================================================================
# Nested Object Models (matching Google's structure)
# ============================================================================

class LocalizedText(BaseModel):
    """Localized text with language code"""
    text: str
    language_code: Optional[str] = Field(None, alias="languageCode")
    
    model_config = {"populate_by_name": True}


class LatLng(BaseModel):
    """Geographic coordinates"""
    latitude: float
    longitude: float


class AuthorAttribution(BaseModel):
    """Review author information"""
    display_name: Optional[str] = Field(None, alias="displayName")
    uri: Optional[str] = None
    photo_uri: Optional[str] = Field(None, alias="photoUri")
    
    model_config = {"populate_by_name": True}


class Review(BaseModel):
    """User review"""
    name: Optional[str] = None
    relative_publish_time_description: Optional[str] = Field(None, alias="relativePublishTimeDescription")
    rating: Optional[int] = None
    text: Optional[LocalizedText] = None
    original_text: Optional[LocalizedText] = Field(None, alias="originalText")
    author_attribution: Optional[AuthorAttribution] = Field(None, alias="authorAttribution")
    publish_time: Optional[str] = Field(None, alias="publishTime")
    
    model_config = {"populate_by_name": True}


class OpeningHoursPeriod(BaseModel):
    """Opening hours period"""
    open: Optional[Dict[str, Any]] = None
    close: Optional[Dict[str, Any]] = None


class OpeningHours(BaseModel):
    """Opening hours information"""
    open_now: Optional[bool] = Field(None, alias="openNow")
    periods: Optional[List[OpeningHoursPeriod]] = None
    weekday_descriptions: Optional[List[str]] = Field(None, alias="weekdayDescriptions")
    
    model_config = {"populate_by_name": True}


class Photo(BaseModel):
    """Photo reference"""
    name: Optional[str] = None
    width_px: Optional[int] = Field(None, alias="widthPx")
    height_px: Optional[int] = Field(None, alias="heightPx")
    author_attributions: Optional[List[AuthorAttribution]] = Field(None, alias="authorAttributions")
    
    model_config = {"populate_by_name": True}


class PriceRange(BaseModel):
    """Price range information"""
    start_price: Optional[Dict[str, Any]] = Field(None, alias="startPrice")
    end_price: Optional[Dict[str, Any]] = Field(None, alias="endPrice")
    
    model_config = {"populate_by_name": True}


class AccessibilityOptions(BaseModel):
    """Accessibility information"""
    wheelchair_accessible_parking: Optional[bool] = Field(None, alias="wheelchairAccessibleParking")
    wheelchair_accessible_entrance: Optional[bool] = Field(None, alias="wheelchairAccessibleEntrance")
    wheelchair_accessible_restroom: Optional[bool] = Field(None, alias="wheelchairAccessibleRestroom")
    wheelchair_accessible_seating: Optional[bool] = Field(None, alias="wheelchairAccessibleSeating")
    
    model_config = {"populate_by_name": True}


# ============================================================================
# Main GooglePlace Model (matching Google's exact structure)
# ============================================================================

class GooglePlace(BaseModel):
    """
    Google Place model matching the actual Google Places API structure.
    This allows direct use of model_validate() without manual transformation.
    """
    
    # Core identification
    name: Optional[str] = Field(None, description="Resource name format: places/{place_id}")
    id: str = Field(..., description="Unique stable identifier")
    display_name: Optional[LocalizedText] = Field(None, alias="displayName")
    
    # Location
    location: Optional[LatLng] = None
    viewport: Optional[Dict[str, Any]] = None
    
    # Address information
    formatted_address: Optional[str] = Field(None, alias="formattedAddress")
    short_formatted_address: Optional[str] = Field(None, alias="shortFormattedAddress")
    adr_format_address: Optional[str] = Field(None, alias="adrFormatAddress")
    
    # Place types
    types: Optional[List[str]] = None
    primary_type: Optional[str] = Field(None, alias="primaryType")
    primary_type_display_name: Optional[LocalizedText] = Field(None, alias="primaryTypeDisplayName")
    
    # Ratings and reviews
    rating: Optional[float] = None
    user_rating_count: Optional[int] = Field(None, alias="userRatingCount")
    reviews: Optional[List[Review]] = None
    
    # Contact information
    national_phone_number: Optional[str] = Field(None, alias="nationalPhoneNumber")
    international_phone_number: Optional[str] = Field(None, alias="internationalPhoneNumber")
    website_uri: Optional[str] = Field(None, alias="websiteUri")
    google_maps_uri: Optional[str] = Field(None, alias="googleMapsUri")
    
    # Business information
    business_status: Optional[str] = Field(None, alias="businessStatus")
    price_level: Optional[str] = Field(None, alias="priceLevel")
    price_range: Optional[PriceRange] = Field(None, alias="priceRange")
    
    # Opening hours
    current_opening_hours: Optional[OpeningHours] = Field(None, alias="currentOpeningHours")
    regular_opening_hours: Optional[OpeningHours] = Field(None, alias="regularOpeningHours")
    current_secondary_opening_hours: Optional[List[OpeningHours]] = Field(None, alias="currentSecondaryOpeningHours")
    regular_secondary_opening_hours: Optional[List[OpeningHours]] = Field(None, alias="regularSecondaryOpeningHours")
    
    # Editorial content
    editorial_summary: Optional[LocalizedText] = Field(None, alias="editorialSummary")
    
    # Photos
    photos: Optional[List[Photo]] = None
    
    # Restaurant/Dining attributes
    takeout: Optional[bool] = None
    delivery: Optional[bool] = None
    dine_in: Optional[bool] = Field(None, alias="dineIn")
    curbside_pickup: Optional[bool] = Field(None, alias="curbsidePickup")
    reservable: Optional[bool] = None
    
    serves_breakfast: Optional[bool] = Field(None, alias="servesBreakfast")
    serves_lunch: Optional[bool] = Field(None, alias="servesLunch")
    serves_dinner: Optional[bool] = Field(None, alias="servesDinner")
    serves_brunch: Optional[bool] = Field(None, alias="servesBrunch")
    serves_beer: Optional[bool] = Field(None, alias="servesBeer")
    serves_wine: Optional[bool] = Field(None, alias="servesWine")
    serves_cocktails: Optional[bool] = Field(None, alias="servesCocktails")
    serves_coffee: Optional[bool] = Field(None, alias="servesCoffee")
    serves_dessert: Optional[bool] = Field(None, alias="servesDessert")
    serves_vegetarian_food: Optional[bool] = Field(None, alias="servesVegetarianFood")
    menu_for_children: Optional[bool] = Field(None, alias="menuForChildren")
    
    # Amenities
    outdoor_seating: Optional[bool] = Field(None, alias="outdoorSeating")
    live_music: Optional[bool] = Field(None, alias="liveMusic")
    restroom: Optional[bool] = None
    good_for_children: Optional[bool] = Field(None, alias="goodForChildren")
    good_for_groups: Optional[bool] = Field(None, alias="goodForGroups")
    good_for_watching_sports: Optional[bool] = Field(None, alias="goodForWatchingSports")
    allows_dogs: Optional[bool] = Field(None, alias="allowsDogs")
    
    # Accessibility
    accessibility_options: Optional[AccessibilityOptions] = Field(None, alias="accessibilityOptions")
    
    # Additional metadata
    utc_offset_minutes: Optional[int] = Field(None, alias="utcOffsetMinutes")
    icon_mask_base_uri: Optional[str] = Field(None, alias="iconMaskBaseUri")
    icon_background_color: Optional[str] = Field(None, alias="iconBackgroundColor")
    
    model_config = {
        "populate_by_name": True,  # Allow both camelCase and snake_case
        "arbitrary_types_allowed": True
    }
    
    # ========================================================================
    # Helper Methods for Backward Compatibility
    # ========================================================================
    
    @property
    def latitude(self) -> Optional[float]:
        """Helper to get latitude from nested location object"""
        return self.location.latitude if self.location else None
    
    @property
    def longitude(self) -> Optional[float]:
        """Helper to get longitude from nested location object"""
        return self.location.longitude if self.location else None
    
    @property
    def display_name_text(self) -> Optional[str]:
        """Helper to get display name text"""
        return self.display_name.text if self.display_name else None
    
    @property
    def editorial_summary_text(self) -> Optional[str]:
        """Helper to get editorial summary text"""
        return self.editorial_summary.text if self.editorial_summary else None
    
    @property
    def is_open(self) -> Optional[bool]:
        """Helper to check if currently open"""
        if self.current_opening_hours:
            return self.current_opening_hours.open_now
        return None
    
    def get_available_fields(self) -> Dict[str, Any]:
        """
        Extract all available fields that have actual values.
        Excludes None values, empty strings, empty lists, and empty dicts.
        
        Returns:
            Dict containing only fields with meaningful values
        """
        available = {}
        
        for field_name, field_value in self.model_dump(exclude_none=True, by_alias=False).items():
            if field_value is not None:
                # Skip empty collections
                if isinstance(field_value, (list, dict)) and len(field_value) == 0:
                    continue
                available[field_name] = field_value
        
        return available


# ============================================================================
# Legacy Models for Backward Compatibility
# ============================================================================

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


@dataclass
class GooglePlacesResponse:
    """Wrapper for Google Places API responses using GooglePlace models"""
    places: List[GooglePlace]
    next_page_token: Optional[str] = None
    
    @classmethod
    def from_google_response(cls, response_data: Dict[str, Any]) -> 'GooglePlacesResponse':
        """Create from Google's built-in TextSearchResponse format"""
        places_data = response_data.get("places", [])
        places = [GooglePlace.model_validate(place_data) for place_data in places_data]
        
        return cls(
            places=places,
            next_page_token=response_data.get("nextPageToken")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB serialization"""
        return {
            "places": [place.model_dump(by_alias=True) for place in self.places],
            "next_page_token": self.next_page_token
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GooglePlacesResponse':
        """Create from dictionary (for MongoDB deserialization)"""
        places = [GooglePlace.model_validate(place_data) for place_data in data.get("places", [])]
        return cls(
            places=places,
            next_page_token=data.get("next_page_token")
        )
    
    def handle_multiple_places(self) -> None:
        """Handle multiple places by raising UserClarificationError with options"""
        if len(self.places) > 1:
            from error.trip_planner_errors import UserClarificationError
            
            option_places = "\n".join(
                [place.display_name_text or place.name for place in self.places]
            )
            raise UserClarificationError(
                clarification_questions=[
                    "Please provide more information about the destination ",
                    option_places,
                ]
            )


# Field masks for different use cases
class GooglePlacesFieldMasks:
    """
    Field masks for Google Places API endpoints organized by pricing tiers
    
    Google's Pricing Tiers:
    - ESSENTIAL: Basic fields (lowest cost) - id, name, address, location, types
    - PRO: Contact & atmosphere (medium cost) - adds rating, hours, price, website  
    - ENTERPRISE: Premium content (highest cost) - adds photos, reviews, editorial
    
    Reference: https://developers.google.com/maps/documentation/places/web-service/choose-fields
    """
    
    # ============================================================================
    # TEXT SEARCH API - Field Masks (uses "places." prefix)
    # ============================================================================
    
    TEXT_SEARCH_ESSENTIAL = (
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.shortFormattedAddress,"
        "places.location,"
        "places.types,"
        "places.viewport,"
        "places.addressComponents,"
        "places.adrFormatAddress,"
        "places.plusCode"
    )
    
    TEXT_SEARCH_PRO = (
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.shortFormattedAddress,"
        "places.location,"
        "places.types,"
        "places.viewport,"
        "places.addressComponents,"
        "places.rating,"
        "places.userRatingCount,"
        "places.priceLevel,"
        "places.businessStatus,"
        "places.websiteUri,"
        "places.googleMapsUri,"
        "places.currentOpeningHours"
    )
    
    TEXT_SEARCH_ENTERPRISE = (
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.location,"
        "places.types,"
        "places.rating,"
        "places.userRatingCount,"
        "places.priceLevel,"
        "places.businessStatus,"
        "places.websiteUri,"
        "places.currentOpeningHours,"
        "places.regularOpeningHours,"
        "places.photos,"
        "places.reviews,"
        "places.editorialSummary"
    )
    
    # ============================================================================
    # NEARBY SEARCH API - Field Masks (uses "places." prefix)
    # ============================================================================
    

    
    NEARBY_SEARCH_PRO = (
        "places.accessibilityOptions,"
        "places.addressComponents,"
        "places.adrFormatAddress,"
        "places.attributions,"
        "places.businessStatus,"
        "places.containingPlaces,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.googleMapsLinks,"
        "places.googleMapsUri,"
        "places.iconBackgroundColor,"
        "places.iconMaskBaseUri,"
        "places.id,"
        "places.location,"
        "places.movedPlace,"    
        "places.movedPlaceId,"
        "places.photos,"
        "places.plusCode,"
        "places.postalAddress,"
        "places.primaryType,"
        "places.primaryTypeDisplayName,"
        "places.pureServiceAreaBusiness,"
        "places.shortFormattedAddress,"
        "places.subDestinations,"
        "places.types,"
        "places.utcOffsetMinutes,"
        "places.viewport"
    )
    
    
    # ============================================================================
    # PLACE DETAILS API - Field Masks (NO "places." prefix)
    # ============================================================================
    
    PLACE_DETAILS_ESSENTIAL = (
        "id,"
        "displayName,"
        "formattedAddress,"
        "shortFormattedAddress,"
        "location,"
        "types,"
        "viewport,"
        "addressComponents,"
        "adrFormatAddress,"
        "plusCode"
    )
    
