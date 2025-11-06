"""
Foursquare enhancement utilities for integrating Foursquare API with Google Places data.
"""

from typing import Optional, Dict, List
from models.point_of_interest_models import PointOfInterest, Source
from models.foursquare_model import (
    FoursquarePlacesMatchRequest,
    FoursquareVenueTipsRequest,
    FoursquarePlacesMatchResponse,
    FoursquareVenueTipsResponse,
    FoursquareSortOrder,
)
from service_api.fourquare_api import (
    foursquare_places_match_with_request,
    foursquare_venue_tips_with_request,
)


class FoursquareEnhancer:
    """
    Foursquare enhancement class for integrating Foursquare API with Google Places data.
    """

    def __init__(self):
        self.foursquare_api = None
        # Initialize Foursquare API if available
        try:
            from service_api.fourquare_api import _foursquare_api

            self.foursquare_api = _foursquare_api
        except Exception:
            pass

    def enhance_google_place_with_foursquare(
        self,
        google_place: PointOfInterest,
        search_radius_m: int = 500,
        name_similarity_threshold: float = 0.6,
    ) -> Optional[Dict[str, any]]:
        """
        Try to find a matching Foursquare venue using places match API and get tips.
        Returns a dictionary containing Foursquare match data and tips, or None if no match.

        Args:
            google_place: Google Places PointOfInterest object
            search_radius_m: Search radius in meters (not used in places match API)
            name_similarity_threshold: Minimum match confidence threshold (0.0-1.0)

        Returns:
            Dictionary with Foursquare data or None if no match found
        """
        if not self.foursquare_api:
            print("⚠️  Foursquare API not available")
            return None

        try:
            # Create Foursquare places match request with full address and coordinates
            # Truncate address if it's too long (Foursquare limit is 64 characters)
            address = google_place.address or ""
            if len(address) > 64:
                address = address[:64]

            match_request = FoursquarePlacesMatchRequest(
                name=google_place.name,
                address=address,
                ll=f"{google_place.location.latitude},{google_place.location.longitude}",
            )

            # Call Foursquare places match API
            match_result = foursquare_places_match_with_request(match_request)

            # Parse the response using Pydantic model
            match_response = FoursquarePlacesMatchResponse(**match_result)

            # Check if match confidence is acceptable
            if not match_response.is_high_confidence_match(
                threshold=name_similarity_threshold
            ):
                print(
                    f"Low confidence match for {google_place.name}: {match_response.get_match_percentage()}%"
                )
                return None

            # Get venue tips
            tips_request = FoursquareVenueTipsRequest(
                venue_id=match_response.place.fsq_place_id,
                limit=10,
                sort=FoursquareSortOrder.POPULAR,
            )

            tips_result = foursquare_venue_tips_with_request(tips_request)
            tips_response = FoursquareVenueTipsResponse(tips=tips_result)

            # Return combined Foursquare data
            return {
                "match": match_response,
                "tips": tips_response,
                "place": match_response.place,
                "match_score": match_response.match_score,
                "match_percentage": match_response.get_match_percentage(),
                "tips_count": tips_response.get_tips_count(),
                "venue_id": match_response.place.fsq_place_id,
            }

        except Exception as e:
            print(f"Error enhancing Google Place with Foursquare: {e}")
            return None


# Convenience functions
_foursquare_enhancer = FoursquareEnhancer()


def enhance_clusters_with_foursquare_data(
    clusters: Dict[int, List[PointOfInterest]],
    search_radius_m: int = 500,
    name_similarity_threshold: float = 0.6,
    enable_linking: bool = True,
) -> Dict[int, List[PointOfInterest]]:
    """
    Enhance Google places (not just restaurants) with Foursquare data for clustered POIs.
    This runs after clustering to reduce API calls by focusing on survived items.

    Args:
        clusters: Dictionary of clusters with POI objects
        search_radius_m: Search radius in meters for finding Foursquare matches
        name_similarity_threshold: Minimum name similarity score (0-1)
        enable_linking: Whether to enable Foursquare linking (can be disabled for testing)

    Returns:
        Enhanced clusters with Foursquare data
    """
    if not enable_linking:
        return clusters

    try:
        # Collect all Google places from all clusters
        all_google_places = []
        cluster_place_mapping = {}  # Maps place ID to cluster index

        # no restaurant check needed for Foursquare enhancement of places

        for cluster_id, cluster_items in clusters.items():
            for item in cluster_items:
                # Enhance all Google places (not just restaurants)
                if hasattr(item, "source") and item.source == Source.google_places:
                    all_google_places.append(item)
                    cluster_place_mapping[item.id] = cluster_id

        if not all_google_places:
            print("ℹ️  No Google places found in clusters to enhance with Foursquare")
            return clusters

        print(
            f"🔎 Enhancing {len(all_google_places)} Google places with Foursquare data..."
        )

        # Enhance places with Foursquare data
        enhanced_places = {}
        successful_enhancements = 0

        for place in all_google_places:
            try:
                foursquare_data = (
                    _foursquare_enhancer.enhance_google_place_with_foursquare(
                        place,
                        search_radius_m=search_radius_m,
                        name_similarity_threshold=name_similarity_threshold,
                    )
                )

                # Check if enhancement was successful (has Foursquare data)
                if foursquare_data is not None:
                    # Add Foursquare data to the place object
                    place.foursquare_data = foursquare_data
                    enhanced_places[place.id] = place
                    successful_enhancements += 1
                    print(f"   🔗 {place.name} → Enhanced with Foursquare data")
                else:
                    # Keep original if no Foursquare match found
                    enhanced_places[place.id] = place

            except Exception as e:
                print(f"   ⚠️  Failed to enhance {place.name} with Foursquare: {e}")
                enhanced_places[place.id] = place

        print(
            f"✅ Successfully enhanced {successful_enhancements}/{len(all_google_places)} places with Foursquare"
        )

        # Update clusters with enhanced place data
        enhanced_clusters = {}
        for cluster_id, cluster_items in clusters.items():
            enhanced_items = []
            for item in cluster_items:
                # Check if this place was enhanced
                if (
                    hasattr(item, "id")
                    and item.id in enhanced_places
                    and hasattr(item, "source")
                    and item.source == Source.google_places
                ):
                    # Replace with enhanced Foursquare data
                    enhanced_items.append(enhanced_places[item.id])
                    if (
                        hasattr(enhanced_places[item.id], "foursquare_data")
                        and enhanced_places[item.id].foursquare_data is not None
                    ):
                        print(
                            f"   ✅ Enhanced place in cluster {cluster_id}: {item.name}"
                        )
                else:
                    # Keep original item
                    enhanced_items.append(item)

            enhanced_clusters[cluster_id] = enhanced_items

        return enhanced_clusters

    except ImportError as e:
        print(f"⚠️  Foursquare linking not available: {e}")
        return clusters
    except Exception as e:
        print(f"❌ Error enhancing clusters with Foursquare data: {e}")
        return clusters
