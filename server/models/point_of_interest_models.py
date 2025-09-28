"""
Point of Interest data models for places and events
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from .yelp_model import YelpPointOfInterest
from .foursquare_model import FoursquarePlace
from .google_map_models import GooglePlace
from constant.restaurant_constants import RESTAURANT_KEYWORDS, RESTAURANT_PLACE_TYPES


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


# Backward compatibility - keep the old function but return the new model
def create_point_of_interest_from_dict(item_dict: Dict[str, Any]) -> PointOfInterest:
    """Create a PointOfInterest from a dictionary (for backward compatibility)"""
    return PointOfInterest(**item_dict)
