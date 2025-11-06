"""
Utility functions for data normalization and conversion
"""

from typing import Dict, Optional, List
from models.point_of_interest_models import PointOfInterest, Location, POIType, Source
from models.google_map_models import GooglePlace


def normalize_places_and_events(
    places_data: Optional[List[GooglePlace]] = None,
) -> List[PointOfInterest]:
    """
    Convert GooglePlace objects into a unified data structure.

    Args:
        places_data: List of GooglePlace objects from search_nearby_places_from_geocode()

    Returns:
        List of PointOfInterest objects
    """
    result = []

    # Process GooglePlace objects
    if places_data:
        for place in places_data:
            # Determine place type from the place's types
            place_type = "unknown"
            if hasattr(place, "types") and place.types:
                # Use the first type as the category
                place_type = place.types[0] if place.types else "unknown"

            normalized_item = _normalize_place(place, place_type)
            if normalized_item:
                result.append(normalized_item)

    return result


def _normalize_place(place: GooglePlace, place_type: str) -> Optional[PointOfInterest]:
    """Normalize a GooglePlace object into unified structure"""
    try:
        # Extract name from LocalizedText object or use resource name as fallback
        name = place.display_name_text or place.name
        if not name:
            return None

        return PointOfInterest(
            name=name,
            type_POI=POIType.place,
            types=[place_type] if place_type != "unknown" else (place.types or []),
            address=place.formatted_address or "",
            location=Location(latitude=place.latitude, longitude=place.longitude),
            tags=place.types or [],
            # Source-specific data wrappers
            google_data=place,
            yelp_data=None,
            foursquare_data=None,
        )
    except Exception as e:
        print(f"Error normalizing place: {e}")
        return None


def enhance_clusters_with_yelp_data(
    clusters: Dict[int, List[PointOfInterest]],
    search_radius_m: int = 500,
    name_similarity_threshold: float = 0.6,
    enable_linking: bool = True,
) -> Dict[int, List[PointOfInterest]]:
    """
    Enhance restaurants with Yelp data for clustered POIs.
    This is more efficient than enhancing before clustering since it only processes
    restaurants that made it through the clustering and filtering process.

    Args:
        clusters: List of cluster dictionaries containing POI data
        search_radius_m: Search radius in meters for finding Yelp matches
        name_similarity_threshold: Minimum name similarity score (0-1)
        enable_linking: Whether to enable Yelp linking (can be disabled for testing)

    Returns:
        Enhanced clusters with Yelp data for restaurants
    """
    if not enable_linking:
        return clusters

    try:
        from .restaurant_linker import link_restaurants_batch

        # Collect all Google restaurants from all clusters
        all_google_restaurants = []
        cluster_restaurant_mapping = {}  # Maps restaurant ID to cluster index

        from .restaurant_utils import is_restaurant

        for cluster_id, cluster_items in clusters.items():
            for item in cluster_items:
                # Check if this is a Google restaurant that needs enhancement
                if (
                    hasattr(item, "source")
                    and item.source == Source.google_places
                    and is_restaurant(item)
                ):
                    all_google_restaurants.append(item)
                    cluster_restaurant_mapping[item.id] = cluster_id

        if not all_google_restaurants:
            print("🍽️  No Google restaurants found in clusters to enhance")
            return clusters

        print(
            f"🍽️  Enhancing {len(all_google_restaurants)} Google restaurants with Yelp data..."
        )

        # Restaurants are already POI objects from clustering
        poi_restaurants = all_google_restaurants

        # Link restaurants with Yelp
        linked_results = link_restaurants_batch(
            poi_restaurants,
            search_radius_m=search_radius_m,
            name_similarity_threshold=name_similarity_threshold,
        )

        # Count successful links
        successful_links = sum(
            1 for _, yelp_place in linked_results if yelp_place is not None
        )
        print(
            f"✅ Successfully linked {successful_links}/{len(poi_restaurants)} restaurants with Yelp"
        )

        # Show enhancement details for linked restaurants
        for google_place, yelp_place in linked_results:
            if yelp_place:
                print(
                    f"   🔗 {google_place.name} → {yelp_place.name} (Enhanced by: {yelp_place.get_enhancement_summary()})"
                )

        # Create a mapping of enhanced restaurants
        enhanced_restaurants = {}
        for google_place, yelp_place in linked_results:
            if yelp_place:
                enhanced_restaurants[google_place.id] = yelp_place

        # Update clusters with enhanced restaurant data
        enhanced_clusters = {}
        for cluster_id, cluster_items in clusters.items():
            enhanced_items = []
            for item in cluster_items:
                # Check if this restaurant was enhanced
                if (
                    hasattr(item, "id")
                    and item.id in enhanced_restaurants
                    and hasattr(item, "source")
                    and item.source == Source.google_places
                    and is_restaurant(item)
                ):
                    # Replace with enhanced Yelp data
                    enhanced_items.append(enhanced_restaurants[item.id])
                    print(
                        f"   ✅ Enhanced restaurant in cluster {cluster_id}: {item.name}"
                    )
                else:
                    # Keep original item
                    enhanced_items.append(item)

            enhanced_clusters[cluster_id] = enhanced_items

        return enhanced_clusters

    except ImportError as e:
        print(f"⚠️  Yelp linking not available: {e}")
        return clusters
    except Exception as e:
        print(f"❌ Error enhancing clusters with Yelp data: {e}")
        return clusters
