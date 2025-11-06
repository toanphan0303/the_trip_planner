"""
Point of Interest data models for places and events
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from enum import Enum
from user_profile.models import TravelStyle

from .yelp_model import YelpPointOfInterest
from .foursquare_model import FoursquarePlace
from .google_map_models import GooglePlace
from constant.restaurant_constants import RESTAURANT_KEYWORDS, RESTAURANT_PLACE_TYPES

if TYPE_CHECKING:
    from models.location_preference_model import LocationPreferenceMatch

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
    """Point of Interest model that wraps data from multiple sources"""

    # Core identification
    name: str = Field(..., description="Display name")
    type_POI: POIType = Field(..., description="Type of point of interest")
    types: List[str] = Field(
        default_factory=list, description="List of categories or types"
    )

    # Location information
    address: str = Field("", description="Formatted address")
    location: Location = Field(
        default_factory=Location, description="Geographic coordinates"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="List of tags/categories")

    # Source-specific data wrappers
    google_data: Optional[GooglePlace] = Field(None, description="Google Places data")
    yelp_data: Optional[YelpPointOfInterest] = Field(None, description="Yelp data")
    foursquare_data: Optional[FoursquarePlace] = Field(
        None, description="Foursquare data"
    )
    travel_style: Optional[TravelStyle] = Field(None, description="Travel style")
    poi_evaluation: Optional[Any] = Field(None, description="POI evaluation (LocationPreferenceMatch)")

    def is_worth_visiting(
        self,
        min_rating: float = 3.5,
        min_review_count: int = 10,
        min_score: float = 0.6,
    ) -> bool:
        """
        Determine if this location is worth visiting based on rating, user rating count, and visitability score.

        Args:
            min_rating: Minimum rating threshold (default: 3.5)
            min_review_count: Minimum number of reviews required (default: 10)
            min_score: Minimum visitability score threshold (default: 0.6)

        Returns:
            True if the location meets the criteria for being worth visiting
        """
        # Get the best rating data from available sources
        best_rating, best_review_count = self._get_best_rating_data()

        # If no rating data, consider it not worth visiting
        if best_rating is None or best_review_count is None:
            return False

        # Check if rating meets minimum threshold
        if best_rating < min_rating:
            return False

        # Check if review count meets minimum threshold
        if best_review_count < min_review_count:
            return False

        # Calculate and check visitability score
        visitability_score = self._calculate_visitability_score()
        if visitability_score < min_score:
            return False

        return True

    def _get_best_rating_data(self) -> tuple[Optional[float], Optional[int]]:
        """
        Get the best rating data from Google data.

        Returns:
            Tuple of (rating, review_count) from Google data
        """
        if self.google_data and self.google_data.rating is not None:
            return self.google_data.rating, self.google_data.user_rating_count
        else:
            return None, None

    def _calculate_visitability_score(self) -> float:
        """
        Calculate a visitability score (0-1) based on rating and review count.
        Higher scores indicate more worth visiting.

        Returns:
            Float between 0 and 1 representing visitability score
        """
        # Get the best rating data from available sources
        best_rating, best_review_count = self._get_best_rating_data()

        # If no rating data, return 0
        if best_rating is None or best_review_count is None:
            return 0.0

        # Normalize rating to 0-1 scale (assuming 5-star max)
        rating_score = best_rating / 5.0

        # Normalize review count to 0-1 scale (using log scale for diminishing returns)
        # More reviews = higher confidence, but with diminishing returns
        import math

        review_score = min(
            1.0, math.log10(max(1, best_review_count)) / 3.0
        )  # log10(1000) ≈ 3

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

    def get_travel_preference_view(self) -> str:
        """
        Get a concise, essential view of this POI for travel preference evaluation.
        Only includes data that exists and is relevant for matching travel preferences.
        
        Returns:
            Formatted string with essential POI information for LLM evaluation
        """
        view_parts = []
        
        # Name (always present)
        view_parts.append(f"**{self.name}**")
        
        # Types/Categories
        if self.types:
            primary_types = [t for t in self.types if t not in ['point_of_interest', 'establishment', 'food']]
            if primary_types:
                view_parts.append(f"Type: {', '.join(primary_types[:3])}")
        
        # Rating and reviews (quality indicator)
        rating, review_count = self._get_best_rating_data()
        if rating and review_count:
            view_parts.append(f"Rating: {rating:.1f}/5 ({review_count:,} reviews)")
        elif rating:
            view_parts.append(f"Rating: {rating:.1f}/5")
        
        # Editorial summary (what makes it special)
        if self.google_data and self.google_data.editorial_summary_text:
            summary = self.google_data.editorial_summary_text
            # Truncate if too long
            if len(summary) > 150:
                summary = summary[:147] + "..."
            view_parts.append(f"Description: {summary}")
        
        # Reviews (real user experiences)
        if self.google_data and self.google_data.reviews:
            reviews = self.google_data.reviews
            # Get the most helpful reviews (typically the first ones from Google)
            review_snippets = []
            for review in reviews[:2]:  # Take top 2 reviews
                if review.text and hasattr(review.text, 'text'):
                    review_text = review.text.text
                    # Truncate long reviews
                    if len(review_text) > 100:
                        review_text = review_text[:97] + "..."
                    # Add rating as text (clearer for LLMs than symbols)
                    rating_text = f"{review.rating}-star" if review.rating else "unrated"
                    review_snippets.append(f"({rating_text}) {review_text}")
            
            if review_snippets:
                reviews_text = "; ".join(review_snippets)
                view_parts.append(f"Reviews: {reviews_text}")
        
        # Price level
        if self.google_data and self.google_data.price_level:
            price_map = {
                'PRICE_LEVEL_FREE': 'Free',
                'PRICE_LEVEL_INEXPENSIVE': 'Inexpensive',
                'PRICE_LEVEL_MODERATE': 'Moderate',
                'PRICE_LEVEL_EXPENSIVE': 'Expensive',
                'PRICE_LEVEL_VERY_EXPENSIVE': 'Very Expensive'
            }
            price = price_map.get(self.google_data.price_level, self.google_data.price_level)
            view_parts.append(f"Price: {price}")
        
        # Key amenities (relevant for family/group travel)
        amenities = []
        if self.google_data:
            if self.google_data.good_for_children:
                amenities.append("good for children")
            if self.google_data.good_for_groups:
                amenities.append("good for groups")
            if self.google_data.outdoor_seating:
                amenities.append("outdoor seating")
            if self.google_data.accessibility_options:
                amenities.append("wheelchair accessible")
        
        if amenities:
            view_parts.append(f"Amenities: {', '.join(amenities)}")
        
        # Opening status
        if self.google_data and self.google_data.business_status:
            if self.google_data.business_status != 'OPERATIONAL':
                view_parts.append(f"Status: {self.google_data.business_status}")
        
        return " | ".join(view_parts)

    def get_restaurant_preview_view(self) -> str:
        """
        Get a restaurant-focused view for preference evaluation.
        Prioritizes Yelp data over Google data as Yelp has richer restaurant information.
        Only includes data that exists and is essential for restaurant preference matching.
        
        Returns:
            Formatted string with essential restaurant information for LLM evaluation
        """
        view_parts = []
        
        # Name (always present)
        view_parts.append(f"**{self.name}**")
        
        # Determine data source priority: Yelp > Google
        use_yelp = self.yelp_data is not None
        
        # Cuisine/Categories
        if use_yelp and self.yelp_data.categories:
            # Yelp categories are more specific for restaurants
            cuisine_types = [cat.title for cat in self.yelp_data.categories[:3]]
            view_parts.append(f"Cuisine: {', '.join(cuisine_types)}")
        elif self.types:
            # Fallback to Google types
            cuisine_types = [t for t in self.types if t not in ['restaurant', 'food', 'establishment', 'point_of_interest']]
            if cuisine_types:
                view_parts.append(f"Cuisine: {', '.join(cuisine_types[:3])}")
        
        # Rating and reviews (prefer Yelp for restaurants)
        if use_yelp and self.yelp_data.rating:
            rating = float(self.yelp_data.rating) if isinstance(self.yelp_data.rating, str) else self.yelp_data.rating
            review_count = self.yelp_data.review_count
            view_parts.append(f"Rating: {rating:.1f}/5 ({review_count:,} Yelp reviews)")
        else:
            # Fallback to Google rating
            rating, review_count = self._get_best_rating_data()
            if rating and review_count:
                view_parts.append(f"Rating: {rating:.1f}/5 ({review_count:,} reviews)")
            elif rating:
                view_parts.append(f"Rating: {rating:.1f}/5")
        
        # Price level (prefer Yelp's $ system for restaurants)
        if use_yelp and self.yelp_data.price:
            price_map = {
                '$': 'Inexpensive',
                '$$': 'Moderate',
                '$$$': 'Expensive',
                '$$$$': 'Very Expensive'
            }
            price = price_map.get(self.yelp_data.price, self.yelp_data.price)
            view_parts.append(f"Price: {price}")
        elif self.google_data and self.google_data.price_level:
            price_map = {
                'PRICE_LEVEL_FREE': 'Free',
                'PRICE_LEVEL_INEXPENSIVE': 'Inexpensive',
                'PRICE_LEVEL_MODERATE': 'Moderate',
                'PRICE_LEVEL_EXPENSIVE': 'Expensive',
                'PRICE_LEVEL_VERY_EXPENSIVE': 'Very Expensive'
            }
            price = price_map.get(self.google_data.price_level, self.google_data.price_level)
            view_parts.append(f"Price: {price}")
        
        # Dining options (from Google data)
        dining_options = []
        if self.google_data:
            if self.google_data.dine_in:
                dining_options.append("dine-in")
            if self.google_data.takeout:
                dining_options.append("takeout")
            if self.google_data.delivery:
                dining_options.append("delivery")
            if self.google_data.reservable:
                dining_options.append("reservations")
        
        if dining_options:
            view_parts.append(f"Options: {', '.join(dining_options)}")
        
        # Food service info (what meals they serve)
        meal_service = []
        if self.google_data:
            if self.google_data.serves_breakfast:
                meal_service.append("breakfast")
            if self.google_data.serves_lunch:
                meal_service.append("lunch")
            if self.google_data.serves_dinner:
                meal_service.append("dinner")
            if self.google_data.serves_brunch:
                meal_service.append("brunch")
        
        if meal_service:
            view_parts.append(f"Serves: {', '.join(meal_service)}")
        
        # Key amenities for restaurant preference
        amenities = []
        if self.google_data:
            if self.google_data.good_for_children:
                amenities.append("kid-friendly")
            if self.google_data.good_for_groups:
                amenities.append("group-friendly")
            if self.google_data.outdoor_seating:
                amenities.append("outdoor seating")
            if self.google_data.serves_vegetarian_food:
                amenities.append("vegetarian options")
        
        if amenities:
            view_parts.append(f"Features: {', '.join(amenities)}")
        
        # Reviews (use Google reviews since Yelp doesn't provide review text in Business Search API)
        # Note: Yelp Reviews API would need separate calls - using Google reviews for now
        if self.google_data and self.google_data.reviews:
            reviews = self.google_data.reviews
            review_snippets = []
            for review in reviews[:2]:  # Take top 2 reviews
                if review.text and hasattr(review.text, 'text'):
                    review_text = review.text.text
                    # Truncate long reviews
                    if len(review_text) > 100:
                        review_text = review_text[:97] + "..."
                    # Add rating as text
                    rating_text = f"{review.rating}-star" if review.rating else "unrated"
                    review_snippets.append(f"({rating_text}) {review_text}")
            
            if review_snippets:
                reviews_text = "; ".join(review_snippets)
                # Indicate source if we're using Google reviews but have Yelp data
                source_label = "Google reviews" if use_yelp else "Reviews"
                view_parts.append(f"{source_label}: {reviews_text}")
        
        # Business status (only if problematic)
        if self.google_data and self.google_data.business_status:
            if self.google_data.business_status != 'OPERATIONAL':
                view_parts.append(f"Status: {self.google_data.business_status}")
        
        if use_yelp and self.yelp_data.is_closed:
            view_parts.append("Status: CLOSED")
        
        return " | ".join(view_parts)

    def get_enhancement_summary(self) -> str:
        """
        Get a human-readable summary of data enhancements.

        Returns:
            String describing the enhancement sources
        """
        sources = []
        if self.google_data:
            sources.append("Google")
        if self.yelp_data:
            sources.append("Yelp")
        if self.foursquare_data:
            sources.append("Foursquare")

        if not sources:
            return "No data sources available"
        elif len(sources) == 1:
            return f"Data from {sources[0]}"
        else:
            return f"Data from {', '.join(sources)}"

    def get_all_types(self) -> List[str]:
        """Get all types from Google data"""
        types = set()

        # Add types
        types.update(self.types)

        # Add tags
        types.update(self.tags)

        # Add Google categories
        if self.google_data and self.google_data.types:
            types.update(self.google_data.types)

        return list(types)

    def is_restaurant(self) -> bool:
        """Check if this is a restaurant based on categories from all sources"""
        categories = self.get_all_types()

        # Check if any category matches restaurant keywords or place types
        for category in categories:
            category_lower = category.lower()
            if (
                category_lower in RESTAURANT_KEYWORDS
                or category_lower in RESTAURANT_PLACE_TYPES
            ):
                return True

        return False

    def get_available_fields(self) -> Dict[str, Any]:
        """Get all available fields with non-empty values"""
        fields = {}
        
        # Core fields
        if self.name:
            fields['name'] = self.name
        if self.type_POI:
            fields['type_POI'] = self.type_POI
        if self.types:
            fields['types'] = self.types
        if self.address:
            fields['address'] = self.address
        if self.location and (self.location.latitude is not None or self.location.longitude is not None):
            fields['location'] = self.location
        if self.tags:
            fields['tags'] = self.tags
        
        # Source-specific data
        if self.google_data:
            google_fields = self.google_data.get_available_fields()
            if google_fields:
                fields['google_data'] = google_fields
        
        if self.yelp_data:
            yelp_fields = self.yelp_data.get_available_fields()
            if yelp_fields:
                fields['yelp_data'] = yelp_fields
        
        if self.foursquare_data:
            foursquare_fields = self.foursquare_data.get_available_fields()
            if foursquare_fields:
                fields['foursquare_data'] = foursquare_fields
        
        return fields


# Backward compatibility - keep the old function but return the new model
def create_point_of_interest_from_dict(item_dict: Dict[str, Any]) -> PointOfInterest:
    """Create a PointOfInterest from a dictionary (for backward compatibility)"""
    return PointOfInterest(**item_dict)
