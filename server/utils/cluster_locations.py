"""
Cluster anchor POIs using H3 hexagons and DBSCAN clustering
"""

import numpy as np
from typing import List, Dict, Tuple
from sklearn.cluster import DBSCAN
import math

from models.point_of_interest_models import PointOfInterest
from service_api.google_api import google_place_details
from constant.place_types import PlaceTypes


def is_restaurant(poi: PointOfInterest) -> bool:
    """
    Check if a PointOfInterest is a restaurant based on its category.
    Uses the official place types from PlaceTypes constants.
    
    Args:
        poi: PointOfInterest object to check
        
    Returns:
        True if the POI is a restaurant, False otherwise
    """
    if not poi.category:
        return False
    
    # Get all food and drink related place types from the constants
    food_types = PlaceTypes.get_food_types()
    
    return poi.category.lower() in food_types


def _filter_clusters_by_restaurant_constraint(
    clusters: Dict[int, List[PointOfInterest]], 
    min_restaurants_per_cluster: int = 2
) -> Dict[int, List[PointOfInterest]]:
    """
    Filter clusters to ensure each cluster has at least the minimum number of restaurants.
    Clusters that don't meet this requirement are removed.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of POIs
        min_restaurants_per_cluster: Minimum number of restaurants required per cluster (default: 2)
        
    Returns:
        Filtered clusters dictionary with only clusters that meet the restaurant constraint
    """
    filtered_clusters = {}
    
    for cluster_id, cluster_pois in clusters.items():
        # Count restaurants in this cluster
        restaurant_count = sum(1 for poi in cluster_pois if is_restaurant(poi))
        
        # Only keep clusters that meet the minimum restaurant requirement
        if restaurant_count >= min_restaurants_per_cluster:
            filtered_clusters[cluster_id] = cluster_pois
        else:
            print(f"Removing cluster {cluster_id}: only {restaurant_count} restaurants (need {min_restaurants_per_cluster})")
    
    return filtered_clusters


def _limit_restaurants_per_cluster(
    clusters: Dict[int, List[PointOfInterest]], 
    max_restaurants_per_cluster: int
) -> Dict[int, List[PointOfInterest]]:
    """
    Limit the number of restaurants in each cluster while preserving other POIs.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of POIs
        max_restaurants_per_cluster: Maximum number of restaurants allowed per cluster
        
    Returns:
        Clusters with limited restaurants per cluster
    """
    limited_clusters = {}
    
    for cluster_id, cluster_pois in clusters.items():
        # Separate restaurants from other POIs
        restaurants = [poi for poi in cluster_pois if is_restaurant(poi)]
        other_pois = [poi for poi in cluster_pois if not is_restaurant(poi)]
        
        # Limit restaurants if there are too many (and limit is > 0)
        if max_restaurants_per_cluster > 0 and len(restaurants) > max_restaurants_per_cluster:
            # Sort restaurants by visitability score (highest first) and take top max_restaurants_per_cluster
            sorted_restaurants = sorted(
                restaurants, 
                key=lambda poi: poi.get_visitability_score(), 
                reverse=True
            )
            limited_restaurants = sorted_restaurants[:max_restaurants_per_cluster]
            print(f"Limited cluster {cluster_id}: {len(restaurants)} restaurants -> {len(limited_restaurants)} restaurants")
        else:
            limited_restaurants = restaurants
        
        # Combine limited restaurants with other POIs
        limited_clusters[cluster_id] = limited_restaurants + other_pois
    
    return limited_clusters


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
        
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r


def get_h3_resolution_for_radius(radius_km: float) -> int:
    """
    Determine appropriate H3 resolution based on search radius.
    
    Args:
        radius_km: Search radius in kilometers
        
    Returns:
        H3 resolution level (0-15, where higher numbers = smaller hexagons)
    """
    if radius_km <= 1:
        return 10  # ~0.5km hexagons
    elif radius_km <= 5:
        return 9   # ~1km hexagons
    elif radius_km <= 10:
        return 8   # ~2km hexagons
    elif radius_km <= 25:
        return 7   # ~4km hexagons
    elif radius_km <= 50:
        return 6   # ~8km hexagons
    elif radius_km <= 100:
        return 5   # ~16km hexagons
    else:
        return 4   # ~32km hexagons


def cluster_pois_with_h3_and_dbscan(
    pois: List[PointOfInterest],
    search_radius_km: float,
    min_samples: int = 3,
    eps_km: float = None
) -> Dict[int, List[PointOfInterest]]:
    """
    Cluster PointOfInterest objects using H3 hexagons for initial grouping
    and DBSCAN for fine-grained clustering within hexagons.
    
    Args:
        pois: List of PointOfInterest objects to cluster
        search_radius_km: Search radius in kilometers (used to determine H3 resolution)
        min_samples: Minimum number of samples in a DBSCAN cluster
        eps_km: DBSCAN epsilon parameter in kilometers (auto-calculated if None)
        
    Returns:
        Dictionary mapping cluster_id to list of POIs in that cluster
    """
    if not pois:
        return {}
    
    # Filter POIs with valid coordinates
    valid_pois = [
        poi for poi in pois 
        if poi.location.latitude is not None and poi.location.longitude is not None
    ]
    
    if not valid_pois:
        return {}
    
    # Determine H3 resolution based on search radius
    h3_resolution = get_h3_resolution_for_radius(search_radius_km)
    
    # Group POIs by H3 hexagons
    h3_groups = {}
    
    try:
        import h3
        
        for poi in valid_pois:
            # Get H3 hexagon for this POI
            hex_id = h3.latlng_to_cell(poi.location.latitude, poi.location.longitude, h3_resolution)
            
            if hex_id not in h3_groups:
                h3_groups[hex_id] = []
            h3_groups[hex_id].append(poi)
            
    except ImportError:
        # Fallback: if H3 is not available, use simple grid-based clustering
        print("Warning: H3 library not available, using grid-based clustering")
        return cluster_pois_with_dbscan_only(valid_pois, min_samples, eps_km)
    
    # Cluster within each H3 hexagon using DBSCAN
    clusters = {}
    cluster_id = 0
    
    for hex_id, hex_pois in h3_groups.items():
        if len(hex_pois) < 2:
            # Single POI - assign to its own cluster
            clusters[cluster_id] = hex_pois
            cluster_id += 1
            continue
        
        # Convert POIs to coordinate matrix for DBSCAN
        coords = np.array([
            [poi.location.latitude, poi.location.longitude] 
            for poi in hex_pois
        ])
        
        # Calculate eps in coordinate units (approximate conversion)
        if eps_km is None:
            # Auto-calculate eps based on hexagon size
            eps_km = 0.5  # Default to 500m clusters
        
        # Convert km to approximate coordinate degrees (rough approximation)
        eps_degrees = eps_km / 111.0  # 1 degree ≈ 111 km
        
        # Apply DBSCAN
        dbscan = DBSCAN(eps=eps_degrees, min_samples=min_samples, metric='euclidean')
        labels = dbscan.fit_predict(coords)
        
        # Group POIs by cluster labels
        for label in set(labels):
            if label == -1:  # Noise points
                # Assign noise points to individual clusters
                for i, poi in enumerate(hex_pois):
                    if labels[i] == -1:
                        clusters[cluster_id] = [poi]
                        cluster_id += 1
            else:
                # Regular cluster
                cluster_pois = [hex_pois[i] for i in range(len(hex_pois)) if labels[i] == label]
                clusters[cluster_id] = cluster_pois
                cluster_id += 1
    
    return clusters


def cluster_pois_with_dbscan_only(
    pois: List[PointOfInterest],
    min_samples: int = 3,
    eps_km: float = 0.5
) -> Dict[int, List[PointOfInterest]]:
    """
    Fallback clustering method using only DBSCAN without H3 preprocessing.
    
    Args:
        pois: List of PointOfInterest objects to cluster
        min_samples: Minimum number of samples in a DBSCAN cluster
        eps_km: DBSCAN epsilon parameter in kilometers
        
    Returns:
        Dictionary mapping cluster_id to list of POIs in that cluster
    """
    if len(pois) < 2:
        return {0: pois} if pois else {}
    
    # Convert POIs to coordinate matrix
    coords = np.array([
        [poi.location.latitude, poi.location.longitude] 
        for poi in pois
    ])
    
    # Convert km to approximate coordinate degrees
    eps_degrees = eps_km / 111.0
    
    # Apply DBSCAN
    dbscan = DBSCAN(eps=eps_degrees, min_samples=min_samples, metric='euclidean')
    labels = dbscan.fit_predict(coords)
    
    # Group POIs by cluster labels
    clusters = {}
    cluster_id = 0
    
    for label in set(labels):
        if label == -1:  # Noise points
            # Assign each noise point to its own cluster
            for i, poi in enumerate(pois):
                if labels[i] == -1:
                    clusters[cluster_id] = [poi]
                    cluster_id += 1
        else:
            # Regular cluster
            cluster_pois = [pois[i] for i in range(len(pois)) if labels[i] == label]
            clusters[cluster_id] = cluster_pois
            cluster_id += 1
    
    return clusters


def find_cluster_anchors(
    clusters: Dict[int, List[PointOfInterest]],
    method: str = "centroid"
) -> Dict[int, PointOfInterest]:
    """
    Find anchor POIs for each cluster using different methods.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of POIs
        method: Method to select anchor ("centroid", "highest_rated", "most_popular")
        
    Returns:
        Dictionary mapping cluster_id to anchor POI
    """
    anchors = {}
    
    for cluster_id, cluster_pois in clusters.items():
        if not cluster_pois:
            continue
        
        if method == "centroid":
            # Find POI closest to cluster centroid
            avg_lat = sum(poi.location.latitude for poi in cluster_pois) / len(cluster_pois)
            avg_lon = sum(poi.location.longitude for poi in cluster_pois) / len(cluster_pois)
            
            min_distance = float('inf')
            anchor = cluster_pois[0]
            
            for poi in cluster_pois:
                distance = haversine_distance(
                    avg_lat, avg_lon,
                    poi.location.latitude, poi.location.longitude
                )
                if distance < min_distance:
                    min_distance = distance
                    anchor = poi
            
            anchors[cluster_id] = anchor
            
        elif method == "highest_rated":
            # Find POI with highest rating
            anchor = max(cluster_pois, key=lambda poi: poi.rating or 0)
            anchors[cluster_id] = anchor
            
        elif method == "most_popular":
            # Find POI with most user ratings
            anchor = max(cluster_pois, key=lambda poi: poi.user_rating_count or 0)
            anchors[cluster_id] = anchor
            
        else:
            # Default to first POI
            anchors[cluster_id] = cluster_pois[0]
    
    return anchors


def calculate_smart_clustering_params(pois: List[PointOfInterest], target_clusters: int = None) -> Tuple[int, float]:
    """
    Calculate smart clustering parameters based on dataset characteristics.
    
    Args:
        pois: List of PointOfInterest objects to cluster
        target_clusters: Target number of clusters (e.g., trip duration in days)
        
    Returns:
        Tuple of (min_samples, eps_km) optimized for the dataset
    """
    if not pois or len(pois) < 2:
        return 2, 2.0  # Default fallback
    
    # Calculate dataset characteristics
    num_pois = len(pois)
    
    # Calculate average distance between all POI pairs
    distances = []
    for i in range(len(pois)):
        for j in range(i + 1, len(pois)):
            if (pois[i].location.latitude and pois[i].location.longitude and 
                pois[j].location.latitude and pois[j].location.longitude):
                distance = haversine_distance(
                    pois[i].location.latitude, pois[i].location.longitude,
                    pois[j].location.latitude, pois[j].location.longitude
                )
                distances.append(distance)
    
    if not distances:
        return 2, 2.0  # Fallback if no valid coordinates
    
    # Calculate statistics
    avg_distance = sum(distances) / len(distances)
    min_distance = min(distances)
    
    # Smart min_samples calculation
    # If target_clusters is specified (e.g., trip duration), adjust accordingly
    if target_clusters and target_clusters > 0:
        # Calculate optimal min_samples to achieve target number of clusters
        # Formula: min_samples should be high enough to prevent too many clusters
        # but low enough to allow the target number of clusters
        expected_pois_per_cluster = num_pois / target_clusters
        if expected_pois_per_cluster < 2:
            min_samples = 2  # Minimum for meaningful clusters
        elif expected_pois_per_cluster < 3:
            min_samples = 2
        elif expected_pois_per_cluster < 5:
            min_samples = 3
        else:
            min_samples = min(5, max(3, int(expected_pois_per_cluster * 0.6)))
    else:
        # Original algorithm for automatic clustering
        if num_pois <= 5:
            min_samples = 2
        elif num_pois <= 15:
            # For small datasets, use 2-3 to allow meaningful clusters
            min_samples = max(2, min(3, num_pois // 5))
        elif num_pois <= 50:
            # For medium datasets, use 3-5
            min_samples = max(3, min(5, num_pois // 10))
        else:
            # For large datasets, use 5-8
            min_samples = max(5, min(8, num_pois // 15))
    
    # Smart eps_km calculation
    # If target_clusters is specified, adjust eps_km to help achieve target
    if target_clusters and target_clusters > 0:
        # Calculate eps_km based on desired cluster size and target clusters
        expected_pois_per_cluster = num_pois / target_clusters
        
        # Start with base eps_km from density
        if avg_distance < 1.0:
            base_eps = max(0.5, min_distance * 3)
        elif avg_distance < 3.0:
            base_eps = max(1.0, avg_distance * 0.8)
        elif avg_distance < 10.0:
            base_eps = max(2.0, avg_distance * 0.6)
        else:
            base_eps = max(5.0, avg_distance * 0.4)
        
        # Adjust eps_km based on target clusters
        # If we want fewer clusters, increase eps_km
        # If we want more clusters, decrease eps_km
        if target_clusters < num_pois / 3:  # Want fewer clusters
            eps_km = base_eps * 1.5
        elif target_clusters > num_pois / 2:  # Want more clusters
            eps_km = base_eps * 0.7
        else:
            eps_km = base_eps
    else:
        # Original algorithm for automatic clustering
        if avg_distance < 1.0:
            # Very dense dataset (like city center)
            eps_km = max(0.5, min_distance * 3)
        elif avg_distance < 3.0:
            # Moderately dense dataset (like city districts)
            eps_km = max(1.0, avg_distance * 0.8)
        elif avg_distance < 10.0:
            # Spread out dataset (like metropolitan area)
            eps_km = max(2.0, avg_distance * 0.6)
        else:
            # Very spread out dataset (like region/country)
            eps_km = max(5.0, avg_distance * 0.4)
    
    # Apply constraints
    eps_km = max(0.5, min(eps_km, 15.0))  # Keep between 0.5-15 km
    
    return min_samples, eps_km


def calculate_smart_max_results(days: int, destination_name: str = None, geocode_result: Dict = None) -> int:
    """
    Calculate smart max_results based on trip duration and destination characteristics.
    
    Args:
        days: Trip duration in days
        destination_name: Name of the destination
        geocode_result: Geocoding result with bounds information
        
    Returns:
        Optimal max_results value for the search
    """
    if not days or days <= 0:
        return 10  # Default fallback
    
    # Base calculation: more days = more places needed
    # Target: ~3-5 POIs per day for good coverage
    base_pois_per_day = 4
    target_total_pois = days * base_pois_per_day
    
    # Adjust based on destination characteristics
    destination_factor = _get_destination_diversity_factor(destination_name, geocode_result)
    
    # Calculate max_results_per_type using destination-specific search types
    from constant.destination_config import SearchConfiguration
    num_search_types = SearchConfiguration.get_num_search_types(destination_name)
    base_max_results = target_total_pois // num_search_types
    
    # Apply destination factor
    adjusted_max_results = int(base_max_results * destination_factor)
    
    # Apply constraints and bounds
    min_results = max(5, days)  # At least 5, or 1 per day
    max_results = min(50, adjusted_max_results)  # Cap at 50 per type
    
    # Ensure we have enough results
    final_max_results = max(min_results, max_results)
    
    return final_max_results


def _get_destination_diversity_factor(destination_name: str = None, geocode_result: Dict = None) -> float:
    """
    Calculate a factor that adjusts max_results based on destination diversity.
    
    Args:
        destination_name: Name of the destination
        geocode_result: Geocoding result with bounds information
        
    Returns:
        Multiplier factor (1.0 = default, >1.0 = more diverse, <1.0 = less diverse)
    """
    if not destination_name:
        return 1.0
    
    # Use the new destination classification system
    from constant.destination_config import DestinationClassification
    
    # Get base diversity factor from classification
    base_factor = DestinationClassification.get_diversity_factor(destination_name)
    
    # Use geocode bounds if available for additional adjustment
    if geocode_result and "geometry" in geocode_result:
        bounds = geocode_result["geometry"].get("bounds") or geocode_result["geometry"].get("viewport")
        if bounds:
            try:
                ne = bounds.get("northeast", {})
                sw = bounds.get("southwest", {})
                
                if ne and sw:
                    # Calculate approximate area
                    lat_diff = ne.get("lat", 0) - sw.get("lat", 0)
                    lng_diff = ne.get("lng", 0) - sw.get("lng", 0)
                    area_approx = abs(lat_diff * lng_diff) * 111 * 111  # Convert to km²
                    
                    # Adjust based on area size (additional to classification factor)
                    if area_approx > 5000:  # Very large metropolitan area
                        area_factor = 1.2
                    elif area_approx > 2000:  # Large city
                        area_factor = 1.1
                    elif area_approx > 500:   # Medium city
                        area_factor = 1.05
                    elif area_approx < 100:   # Small/compact area
                        area_factor = 0.9
                    else:
                        area_factor = 1.0
                    
                    # Combine classification and area factors
                    return base_factor * area_factor
            except Exception:
                pass  # Fall through to base factor
    
    # Return base factor from classification
    return base_factor


def _merge_clusters_to_target(clusters: Dict[int, List[PointOfInterest]], target_clusters: int) -> Dict[int, List[PointOfInterest]]:
    """
    Merge clusters to achieve the target number by combining the smallest clusters.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of POIs
        target_clusters: Target number of clusters
        
    Returns:
        Dictionary with merged clusters
    """
    if len(clusters) <= target_clusters:
        return clusters
    
    # Convert to list of (cluster_id, cluster_pois) sorted by size (smallest first)
    cluster_items = [(cluster_id, cluster_pois) for cluster_id, cluster_pois in clusters.items()]
    cluster_items.sort(key=lambda x: len(x[1]))
    
    # Merge smallest clusters until we reach target
    merged_clusters = {}
    next_cluster_id = 0
    
    # Keep the largest clusters as-is
    clusters_to_keep = cluster_items[-(target_clusters-1):] if target_clusters > 1 else []
    for cluster_id, cluster_pois in clusters_to_keep:
        merged_clusters[next_cluster_id] = cluster_pois
        next_cluster_id += 1
    
    # Merge all remaining small clusters into one
    if target_clusters > 0:
        remaining_pois = []
        for cluster_id, cluster_pois in cluster_items[:-(target_clusters-1)] if target_clusters > 1 else cluster_items:
            remaining_pois.extend(cluster_pois)
        
        if remaining_pois:
            merged_clusters[next_cluster_id] = remaining_pois
    
    return merged_clusters


def _filter_clusters_by_worth_visiting(
    clusters: Dict[int, List[PointOfInterest]], 
    min_cluster_size: int = 5,
    max_clusters: int = None,
    max_pois_per_cluster: int = 5
) -> Dict[int, List[PointOfInterest]]:
    """
    Filter clusters to remove places not worth visiting, but keep all places
    if the cluster has fewer than min_cluster_size places. Then sort by 
    visitability score and limit to max_clusters clusters. Also limit
    the number of POIs within each cluster to max_pois_per_cluster.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of POIs
        min_cluster_size: Minimum cluster size to apply filtering (default: 5)
        max_clusters: Maximum number of clusters to return (None = no limit)
        max_pois_per_cluster: Maximum number of POIs to keep in each cluster (default: 5)
        
    Returns:
        Filtered and sorted clusters dictionary
    """
    filtered_clusters = {}
    
    # First pass: filter clusters by worth visiting criteria
    for cluster_id, cluster_pois in clusters.items():
        if len(cluster_pois) < min_cluster_size:
            # Keep all places if cluster is small
            filtered_clusters[cluster_id] = cluster_pois
        else:
            # Filter out places not worth visiting for larger clusters
            worth_visiting_pois = [
                poi for poi in cluster_pois 
                if poi.is_worth_visiting()
            ]
            # Only keep the cluster if it still has places after filtering
            if worth_visiting_pois:
                filtered_clusters[cluster_id] = worth_visiting_pois
    
    # Second pass: limit non-restaurant POIs within each cluster to max_pois_per_cluster
    for cluster_id, cluster_pois in filtered_clusters.items():
        # Separate restaurants from other POIs
        restaurants = [poi for poi in cluster_pois if is_restaurant(poi)]
        other_pois = [poi for poi in cluster_pois if not is_restaurant(poi)]
        
        # Limit only non-restaurant POIs
        if len(other_pois) > max_pois_per_cluster:
            # Sort non-restaurant POIs by visitability score (highest first) and take top max_pois_per_cluster
            sorted_other_pois = sorted(
                other_pois, 
                key=lambda poi: poi.get_visitability_score(), 
                reverse=True
            )
            limited_other_pois = sorted_other_pois[:max_pois_per_cluster]
            filtered_clusters[cluster_id] = restaurants + limited_other_pois
        else:
            # Keep all POIs if under the limit
            filtered_clusters[cluster_id] = restaurants + other_pois
    
    # Third pass: sort by visitability score and limit to max_clusters
    if max_clusters is None or len(filtered_clusters) <= max_clusters:
        return filtered_clusters
    
    # Calculate the best visitability score for each cluster
    cluster_scores = []
    for cluster_id, cluster_pois in filtered_clusters.items():
        # Find the POI with the highest visitability score in this cluster
        best_score = max(
            (poi.get_visitability_score() for poi in cluster_pois),
            default=0.0
        )
        cluster_scores.append((cluster_id, best_score, cluster_pois))
    
    # Sort by visitability score (descending - highest scores first)
    cluster_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Take only the top max_clusters clusters
    top_clusters = cluster_scores[:max_clusters]
    
    # Convert back to dictionary format
    result_clusters = {}
    for i, (original_cluster_id, score, cluster_pois) in enumerate(top_clusters):
        result_clusters[i] = cluster_pois
    
    return result_clusters


def _enhance_pois_with_google_details(
    clusters: Dict[int, List[PointOfInterest]], 
    language_code: str = None,
    region_code: str = None
) -> Dict[int, List[PointOfInterest]]:
    """
    Enhance PointOfInterest objects with detailed information from Google Places API.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of POIs
        language_code: Optional language code for Google API calls
        region_code: Optional region code for Google API calls
        
    Returns:
        Enhanced clusters dictionary with updated POI information
    """
    enhanced_clusters = {}
    
    for cluster_id, cluster_pois in clusters.items():
        enhanced_pois = []
        
        for poi in cluster_pois:
            try:
                # Only enhance POIs that have a place_id (from Google Places)
                if hasattr(poi, 'raw_data') and poi.raw_data.get('id'):
                    place_id = poi.raw_data['id']
                    
                    # Call Google Places Details API
                    details_response = google_place_details(
                        place_id=place_id,
                        language_code=language_code,
                        region_code=region_code
                    )
                    
                    # Extract place details from response (API returns data directly, not wrapped in 'place')
                    place_details = details_response
                    
                    # Create enhanced POI with updated information
                    enhanced_poi = _update_poi_with_details(poi, place_details)
                    enhanced_pois.append(enhanced_poi)
                    
                else:
                    # Keep original POI if no place_id available
                    enhanced_pois.append(poi)
                    
            except Exception as e:
                print(f"Warning: Failed to enhance POI {poi.name}: {str(e)}")
                print(f"Place ID: {poi.raw_data.get('id', 'N/A') if hasattr(poi, 'raw_data') else 'N/A'}")
                # Keep original POI if enhancement fails
                enhanced_pois.append(poi)
        
        enhanced_clusters[cluster_id] = enhanced_pois
    
    return enhanced_clusters


def _update_poi_with_details(poi: PointOfInterest, place_details: Dict) -> PointOfInterest:
    """
    Update a PointOfInterest object with enhanced details from Google Places API.
    
    Args:
        poi: Original PointOfInterest object
        place_details: Place details from Google Places API
        
    Returns:
        Enhanced PointOfInterest object
    """
    # Create a copy of the original POI data
    poi_data = poi.dict()
    
    # Update with enhanced information from Google Places Details
    if place_details.get('rating') is not None:
        poi_data['rating'] = place_details['rating']
    
    if place_details.get('userRatingCount') is not None:
        poi_data['user_rating_count'] = place_details['userRatingCount']
    
    if place_details.get('websiteUri'):
        poi_data['website'] = place_details['websiteUri']
    
    if place_details.get('businessStatus'):
        poi_data['business_status'] = place_details['businessStatus']
    
    if place_details.get('priceLevel'):
        poi_data['price_level'] = place_details['priceLevel']
    
    if place_details.get('editorialSummary', {}).get('text'):
        # Add editorial summary to description if available
        editorial_summary = place_details['editorialSummary']['text']
        if poi_data['description']:
            poi_data['description'] = f"{poi_data['description']}\n\n{editorial_summary}"
        else:
            poi_data['description'] = editorial_summary
    
    if place_details.get('regularOpeningHours'):
        poi_data['opening_hours'] = place_details['regularOpeningHours']
    
    if place_details.get('nationalPhoneNumber'):
        # Add phone number to raw_data for future use
        if 'phone_number' not in poi_data['raw_data']:
            poi_data['raw_data']['phone_number'] = place_details['nationalPhoneNumber']
    
    # Update raw_data with the full place details
    poi_data['raw_data']['enhanced_details'] = place_details
    
    # Create and return enhanced POI
    return PointOfInterest(**poi_data)


def cluster_and_anchor_pois(
    pois: List[PointOfInterest],
    search_radius_km: float,
    min_samples: int = None,
    eps_km: float = None,
    anchor_method: str = "centroid",
    use_smart_params: bool = True,
    target_clusters: int = None,
    filter_worth_visiting: bool = True,
    min_cluster_size_for_filtering: int = 5,
    max_pois_per_cluster: int = 15,
    enhance_with_google_details: bool = True,
    language_code: str = None,
    region_code: str = None,
    max_restaurants_per_cluster: int = 5
) -> Tuple[Dict[int, List[PointOfInterest]], Dict[int, PointOfInterest]]:
    """
    Complete clustering and anchor finding pipeline.
    
    Args:
        pois: List of PointOfInterest objects to cluster
        search_radius_km: Search radius in kilometers
        min_samples: Minimum number of samples in a DBSCAN cluster (optional if use_smart_params=True)
        eps_km: DBSCAN epsilon parameter in kilometers (optional if use_smart_params=True)
        anchor_method: Method to select cluster anchors
        use_smart_params: Whether to automatically calculate optimal clustering parameters
        target_clusters: Target number of clusters (e.g., trip duration in days) - also used as final limit
        filter_worth_visiting: Whether to filter out places not worth visiting (default: True)
        min_cluster_size_for_filtering: Minimum cluster size to apply worth-visiting filtering (default: 5)
        max_pois_per_cluster: Maximum number of POIs to keep in each cluster (default: 5)
        enhance_with_google_details: Whether to enhance POIs with Google Places Details API (default: True)
        language_code: Optional language code for Google API calls
        region_code: Optional region code for Google API calls
        max_restaurants_per_cluster: Maximum number of restaurants allowed per cluster (default: 5)
        
    Returns:
        Tuple of (clusters_dict, anchors_dict)
    """
    # Validate inputs
    if not pois:
        return {}, {}
    
    # Filter POIs with valid coordinates
    valid_pois = [
        poi for poi in pois 
        if poi.location.latitude is not None and poi.location.longitude is not None
    ]
    
    if len(valid_pois) < 2:
        # If less than 2 valid POIs, return individual clusters
        clusters = {i: [poi] for i, poi in enumerate(valid_pois)}
        anchors = {i: poi for i, poi in enumerate(valid_pois)}
        return clusters, anchors
    
    # Calculate smart parameters if requested
    if use_smart_params:
        smart_min_samples, smart_eps_km = calculate_smart_clustering_params(valid_pois, target_clusters)
        # Use smart parameters if not explicitly provided
        if min_samples is None:
            min_samples = smart_min_samples
        if eps_km is None:
            eps_km = smart_eps_km
    else:
        # Use defaults if not provided
        if min_samples is None:
            min_samples = 3
        if eps_km is None:
            eps_km = 2.0
    
    # Perform clustering
    clusters = cluster_pois_with_h3_and_dbscan(
        valid_pois, search_radius_km, min_samples, eps_km
    )
    
    # If we have more clusters than target, merge the smallest clusters
    if target_clusters and target_clusters > 0 and len(clusters) > target_clusters:
        clusters = _merge_clusters_to_target(clusters, target_clusters)
    
    # Filter clusters by worth visiting criteria if requested
    if filter_worth_visiting:
        clusters = _filter_clusters_by_worth_visiting(clusters, min_cluster_size_for_filtering, target_clusters, max_pois_per_cluster)
    
    # Limit restaurants per cluster if requested (0 means no limit)
    clusters = _limit_restaurants_per_cluster(clusters, max_restaurants_per_cluster)
    
    # Enhance POIs with Google Places Details if requested
    if enhance_with_google_details:
        clusters = _enhance_pois_with_google_details(clusters, language_code, region_code)
    
    # Find anchors
    anchors = find_cluster_anchors(clusters, anchor_method)
    
    return clusters, anchors


def get_cluster_statistics(clusters: Dict[int, List[PointOfInterest]]) -> Dict[str, any]:
    """
    Get statistics about the clustering results.
    
    Args:
        clusters: Dictionary mapping cluster_id to list of POIs
        
    Returns:
        Dictionary with clustering statistics
    """
    if not clusters:
        return {
            "total_clusters": 0,
            "total_pois": 0,
            "cluster_sizes": [],
            "avg_cluster_size": 0,
            "largest_cluster_size": 0,
            "smallest_cluster_size": 0
        }
    
    cluster_sizes = [len(pois) for pois in clusters.values()]
    
    return {
        "total_clusters": len(clusters),
        "total_pois": sum(cluster_sizes),
        "cluster_sizes": cluster_sizes,
        "avg_cluster_size": sum(cluster_sizes) / len(cluster_sizes),
        "largest_cluster_size": max(cluster_sizes),
        "smallest_cluster_size": min(cluster_sizes)
    }
