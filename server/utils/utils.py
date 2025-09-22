"""
Utility functions for data normalization and conversion
"""

from typing import Dict, Any, Optional, List
from models.point_of_interest_models import PointOfInterest, PointOfInterestSearchResult, Location, PriceRange, POIType, Source, PriceLevel


def normalize_places_and_events(
    places_data: Optional[Dict[str, Any]] = None,
    events_data: Optional[Dict[str, Any]] = None
) -> PointOfInterestSearchResult:
    """
    Convert nearby places and nearby events into a unified data structure.
    
    Args:
        places_data: Result from search_nearby_places_from_geocode() or similar
        events_data: Result from Ticketmaster API event search
        
    Returns:
        PointOfInterestSearchResult with normalized items
    """
    result = PointOfInterestSearchResult()
    
    # Extract search metadata from places_data
    if places_data:
        if "center" in places_data:
            center_lat, center_lng = places_data["center"]
            result.search_center = Location(latitude=center_lat, longitude=center_lng)
        
        if "radius_m" in places_data and places_data["radius_m"] is not None:
            # Convert meters to kilometers
            result.search_radius_km = places_data["radius_m"] / 1000.0
    
    # Process places data
    if places_data and places_data.get("places_results"):
        for place_type_result in places_data["places_results"]:
            if "error" in place_type_result:
                continue  # Skip failed API calls
                
            place_type = place_type_result.get("type", "unknown")
            places = place_type_result.get("places", [])
            
            for place in places:
                normalized_item = _normalize_place(place, place_type)
                if normalized_item:
                    result.add_item(normalized_item)
    
    # Process events data
    if events_data and events_data.get("_embedded", {}).get("events"):
        events = events_data["_embedded"]["events"]
        
        for event in events:
            normalized_item = _normalize_event(event)
            if normalized_item:
                result.add_item(normalized_item)
    
    return result


def _normalize_place(place: Dict[str, Any], place_type: str) -> Optional[PointOfInterest]:
    """Normalize a Google Place into unified structure"""
    try:
        # Extract basic information
        name = place.get("displayName", {}).get("text", "")
        if not name:
            return None
            
        address = place.get("formattedAddress", "")
        location = place.get("location", {})
        
        # Extract coordinates
        lat = location.get("latitude") if location else None
        lng = location.get("longitude") if location else None
        
        # Extract rating and other details
        rating = place.get("rating")
        user_rating_count = place.get("userRatingCount")
        price_level = place.get("priceLevel")
        business_status = place.get("businessStatus")
        website = place.get("websiteUri")
        
        # Extract opening hours
        opening_hours = place.get("currentOpeningHours", {})
        is_open = opening_hours.get("openNow") if opening_hours else None
        
        return PointOfInterest(
            id=place.get("id", ""),
            name=name,
            type=POIType.place,
            category=place_type,
            description=f"{place_type.replace('_', ' ').title()}",
            address=address,
            location=Location(latitude=lat, longitude=lng),
            rating=rating,
            user_rating_count=user_rating_count,
            price_level=_safe_price_level(price_level),
            business_status=business_status,
            website=website,
            is_open=is_open,
            opening_hours=opening_hours,
            tags=place.get("types", []),
            source=Source.google_places,
            enhanced_by=[],  # No enhancements by default
            raw_data=place
        )
    except Exception as e:
        print(f"Error normalizing place: {e}")
        return None


def _normalize_event(event: Dict[str, Any]) -> Optional[PointOfInterest]:
    """Normalize a Ticketmaster Event into unified structure"""
    try:
        # Extract basic information
        name = event.get("name", "")
        if not name:
            return None
            
        # Extract dates
        dates = event.get("dates", {})
        start_date = dates.get("start", {})
        event_date = start_date.get("localDate")
        event_time = start_date.get("localTime")
        
        # Extract venue information
        venues = event.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}
        venue_name = venue.get("name", "")
        venue_address = _extract_venue_address(venue)
        
        # Extract location
        location = venue.get("location", {})
        lat = location.get("latitude")
        lng = location.get("longitude")
        
        # Extract classification
        classifications = event.get("classifications", [])
        classification = classifications[0] if classifications else {}
        genre = classification.get("genre", {}).get("name", "")
        sub_genre = classification.get("subGenre", {}).get("name", "")
        
        # Extract pricing
        price_ranges = event.get("priceRanges", [])
        price_info = price_ranges[0] if price_ranges else {}
        
        # Extract images
        images = event.get("images", [])
        image_url = images[0].get("url") if images else None
        
        # Extract URLs
        url = event.get("url", "")
        
        return PointOfInterest(
            id=event.get("id", ""),
            name=name,
            type=POIType.event,
            category=genre or "Entertainment",
            description=f"{genre} event" + (f" - {sub_genre}" if sub_genre else ""),
            address=venue_address,
            location=Location(
                latitude=float(lat) if lat else None,
                longitude=float(lng) if lng else None
            ),
            rating=None,  # Events don't have ratings
            user_rating_count=None,
            price_level=_convert_price_range_to_level(price_info),
            business_status="OPERATIONAL",  # Events are typically operational
            website=url,
            is_open=None,  # Not applicable for events
            opening_hours=None,
            tags=[genre, sub_genre] if sub_genre else [genre] if genre else [],
            source=Source.ticketmaster,
            enhanced_by=[],  # No enhancements by default
            raw_data=event,
            # Event-specific fields
            event_date=event_date,
            event_time=event_time,
            venue_name=venue_name,
            price_range=PriceRange(
                min=price_info.get("min"),
                max=price_info.get("max"),
                currency=price_info.get("currency")
            ) if price_info else None,
            image_url=image_url
        )
    except Exception as e:
        print(f"Error normalizing event: {e}")
        return None


def _extract_venue_address(venue: Dict[str, Any]) -> str:
    """Extract formatted address from venue data"""
    address_lines = []
    
    # Add address line
    if venue.get("address", {}).get("line1"):
        address_lines.append(venue["address"]["line1"])
    
    # Add city, state, postal code
    city = venue.get("city", {}).get("name", "")
    state = venue.get("state", {}).get("name", "")
    postal_code = venue.get("postalCode", "")
    
    if city:
        city_state = city
        if state:
            city_state += f", {state}"
        if postal_code:
            city_state += f" {postal_code}"
        address_lines.append(city_state)
    
    # Add country
    country = venue.get("country", {}).get("name", "")
    if country:
        address_lines.append(country)
    
    return ", ".join(address_lines)


def _convert_price_range_to_level(price_info: Dict[str, Any]) -> Optional[PriceLevel]:
    """Convert Ticketmaster price range to Google Places price level format"""
    if not price_info:
        return None
    
    min_price = price_info.get("min")
    max_price = price_info.get("max")
    
    if min_price is None and max_price is None:
        return None
    
    # Use average price if both min and max are available
    if min_price is not None and max_price is not None:
        avg_price = (min_price + max_price) / 2
    elif min_price is not None:
        avg_price = min_price
    else:
        avg_price = max_price
    
    # Convert to Google Places price level format
    if avg_price <= 25:
        return PriceLevel.INEXPENSIVE
    elif avg_price <= 50:
        return PriceLevel.MODERATE
    elif avg_price <= 100:
        return PriceLevel.EXPENSIVE
    else:
        return PriceLevel.VERY_EXPENSIVE


def filter_by_distance(
    result: PointOfInterestSearchResult, 
    center_lat: float, 
    center_lng: float, 
    max_distance_km: float
) -> PointOfInterestSearchResult:
    """
    Filter items by distance from a center point.
    
    Args:
        result: PointOfInterestSearchResult to filter
        center_lat: Center latitude
        center_lng: Center longitude
        max_distance_km: Maximum distance in kilometers
        
    Returns:
        Filtered PointOfInterestSearchResult with items within the distance
    """
    from .radius import haversine_m
    
    filtered_items = []
    
    for item in result.items:
        if item.location.latitude is None or item.location.longitude is None:
            continue
            
        distance_m = haversine_m(center_lat, center_lng, item.location.latitude, item.location.longitude)
        distance_km = distance_m / 1000
        
        if distance_km <= max_distance_km:
            # Create a copy with distance set
            item_dict = item.model_dump()
            item_dict["distance_km"] = round(distance_km, 2)
            filtered_item = PointOfInterest(**item_dict)
            filtered_items.append(filtered_item)
    
    return PointOfInterestSearchResult(
        items=filtered_items,
        total_count=len(filtered_items),
        places_count=len([item for item in filtered_items if item.type == "place"]),
        events_count=len([item for item in filtered_items if item.type == "event"]),
        search_center=Location(latitude=center_lat, longitude=center_lng),
        search_radius_km=max_distance_km,
        search_date=result.search_date
    )


def sort_by_rating_and_distance(result: PointOfInterestSearchResult) -> PointOfInterestSearchResult:
    """
    Sort items by rating (descending) and then by distance (ascending).
    
    Args:
        result: PointOfInterestSearchResult to sort
        
    Returns:
        Sorted PointOfInterestSearchResult
    """
    def sort_key(item: PointOfInterest):
        rating = item.rating or 0
        distance = item.distance_km or 0
        # Higher rating is better (negative for descending), lower distance is better
        return (-rating, distance)
    
    sorted_items = sorted(result.items, key=sort_key)
    
    return PointOfInterestSearchResult(
        items=sorted_items,
        total_count=result.total_count,
        places_count=result.places_count,
        events_count=result.events_count,
        search_center=result.search_center,
        search_radius_km=result.search_radius_km,
        search_date=result.search_date
    )




def enhance_clusters_with_yelp_data(
    clusters: Dict[int, List[Any]],
    search_radius_m: int = 500,
    name_similarity_threshold: float = 0.6,
    enable_linking: bool = True
) -> Dict[int, List[Any]]:
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
                if (hasattr(item, 'source') and item.source == Source.google_places and 
                    is_restaurant(item)):
                    all_google_restaurants.append(item)
                    cluster_restaurant_mapping[item.id] = cluster_id
        
        if not all_google_restaurants:
            print("🍽️  No Google restaurants found in clusters to enhance")
            return clusters
        
        print(f"🍽️  Enhancing {len(all_google_restaurants)} Google restaurants with Yelp data...")
        
        # Restaurants are already POI objects from clustering
        poi_restaurants = all_google_restaurants
        
        # Link restaurants with Yelp
        linked_results = link_restaurants_batch(
            poi_restaurants,
            search_radius_m=search_radius_m,
            name_similarity_threshold=name_similarity_threshold
        )
        
        # Count successful links
        successful_links = sum(1 for _, yelp_place in linked_results if yelp_place is not None)
        print(f"✅ Successfully linked {successful_links}/{len(poi_restaurants)} restaurants with Yelp")
        
        # Show enhancement details for linked restaurants
        for google_place, yelp_place in linked_results:
            if yelp_place:
                print(f"   🔗 {google_place.name} → {yelp_place.name} (Enhanced by: {yelp_place.get_enhancement_summary()})")
        
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
                if (hasattr(item, 'id') and item.id in enhanced_restaurants and 
                    hasattr(item, 'source') and item.source == Source.google_places and 
                    is_restaurant(item)):
                    # Replace with enhanced Yelp data
                    enhanced_items.append(enhanced_restaurants[item.id])
                    print(f"   ✅ Enhanced restaurant in cluster {cluster_id}: {item.name}")
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


def enhance_clusters_with_foursquare_data(
    clusters: Dict[int, List[Any]],
    search_radius_m: int = 500,
    name_similarity_threshold: float = 0.6,
    enable_linking: bool = True
) -> Dict[int, List[Any]]:
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
        from .restaurant_linker import enhance_google_place_with_foursquare
        
        # Collect all Google places from all clusters
        all_google_places = []
        cluster_place_mapping = {}  # Maps place ID to cluster index
        
        # no restaurant check needed for Foursquare enhancement of places
        
        for cluster_id, cluster_items in clusters.items():
            for item in cluster_items:
                # Enhance all Google places (not just restaurants)
                if hasattr(item, 'source') and item.source == Source.google_places:
                    all_google_places.append(item)
                    cluster_place_mapping[item.id] = cluster_id
        
        if not all_google_places:
            print("ℹ️  No Google places found in clusters to enhance with Foursquare")
            return clusters
        
        print(f"🔎 Enhancing {len(all_google_places)} Google places with Foursquare data...")
        
        # Enhance places with Foursquare data
        enhanced_places = {}
        successful_enhancements = 0
        
        for place in all_google_places:
            try:
                enhanced_place = enhance_google_place_with_foursquare(
                    place,
                    search_radius_m=search_radius_m,
                    name_similarity_threshold=name_similarity_threshold
                )
                
                # Check if enhancement was successful (has Foursquare data)
                if (hasattr(enhanced_place, 'foursquare_data') and 
                    enhanced_place.foursquare_data is not None):
                    enhanced_places[place.id] = enhanced_place
                    successful_enhancements += 1
                    print(f"   🔗 {place.name} → Enhanced with Foursquare data")
                else:
                    # Keep original if no Foursquare match found
                    enhanced_places[place.id] = place
                    
            except Exception as e:
                print(f"   ⚠️  Failed to enhance {place.name} with Foursquare: {e}")
                enhanced_places[place.id] = place
        
        print(f"✅ Successfully enhanced {successful_enhancements}/{len(all_google_places)} places with Foursquare")
        
        # Update clusters with enhanced place data
        enhanced_clusters = {}
        for cluster_id, cluster_items in clusters.items():
            enhanced_items = []
            for item in cluster_items:
                # Check if this place was enhanced
                if (hasattr(item, 'id') and item.id in enhanced_places and 
                    hasattr(item, 'source') and item.source == Source.google_places):
                    # Replace with enhanced Foursquare data
                    enhanced_items.append(enhanced_places[item.id])
                    if (hasattr(enhanced_places[item.id], 'foursquare_data') and 
                        enhanced_places[item.id].foursquare_data is not None):
                        print(f"   ✅ Enhanced place in cluster {cluster_id}: {item.name}")
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


def _safe_price_level(price_level: Optional[str]) -> Optional[PriceLevel]:
    """Safely convert price level string to PriceLevel enum"""
    if not price_level:
        return None
    
    try:
        # Check if the price level is a valid enum value
        valid_values = [e.value for e in PriceLevel]
        if price_level in valid_values:
            return PriceLevel(price_level)
    except (ValueError, TypeError):
        pass
    
    return None


