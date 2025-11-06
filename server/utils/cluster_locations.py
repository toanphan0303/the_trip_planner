"""
Cluster anchor POIs using H3 hexagons and DBSCAN clustering
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.cluster import DBSCAN
import math

from models.point_of_interest_models import PointOfInterest
from service_api.google_api import google_place_details
from utils.poi_utils import is_restaurant


def cluster_and_anchor_pois(
    pois: List[PointOfInterest],
    search_radius_km: float,
    target_clusters: int,
    anchor_method: str = "centroid",
    max_pois_per_cluster: int = 40,
    # Advanced parameters (rarely used)
    min_samples: int = None,
    eps_km: float = None,
    filter_worth_visiting: bool = True,
    min_cluster_size_for_filtering: int = 5,
    max_restaurants_per_cluster: int = None,
    enhance_with_google_details: bool = False,
    language_code: str = None,
    region_code: str = None,
) -> Tuple[Dict[int, List[PointOfInterest]], Dict[int, PointOfInterest]]:
    """
    Cluster POIs and find anchor points for trip planning.
    
    Args:
        pois: List of PointOfInterest objects to cluster
        search_radius_km: Search radius in kilometers
        target_clusters: Number of clusters to create (typically trip duration in days)
        anchor_method: Method to select cluster anchors (default: "centroid")
        max_pois_per_cluster: Max POIs per cluster (default: 40)
        
        Advanced (auto-calculated if not provided):
        min_samples: Minimum samples in a DBSCAN cluster
        eps_km: DBSCAN epsilon in kilometers
        filter_worth_visiting: Filter low-quality places (default: True)
        min_cluster_size_for_filtering: Min size for filtering (default: 5)
        max_restaurants_per_cluster: Max restaurants per cluster (default: None, no limit)
        enhance_with_google_details: Enhance with Google Details API (default: False)
        language_code: Language for API calls
        region_code: Region for API calls
        
    Returns:
        Tuple of (clusters_dict, anchors_dict)
    """
    # Create a POIClusterer instance with the provided parameters
    clusterer = POIClusterer(
        pois=pois,
        search_radius_km=search_radius_km,
        min_samples=min_samples,
        eps_km=eps_km,
        anchor_method=anchor_method,
        target_clusters=target_clusters,
        filter_worth_visiting=filter_worth_visiting,
        min_cluster_size_for_filtering=min_cluster_size_for_filtering,
        max_pois_per_cluster=max_pois_per_cluster,
        max_restaurants_per_cluster=max_restaurants_per_cluster,
        enhance_with_google_details=enhance_with_google_details,
        language_code=language_code,
        region_code=region_code
    )
    
    # Use the cluster method
    return clusterer.cluster()


# ============================================================================
# Class-based Interface
# ============================================================================


class POIClusterer:
    """
    Class-based interface for clustering Points of Interest using H3 + DBSCAN.
    
    This class provides a clean, configurable interface for clustering POIs and
    finding representative anchor points for travel planning.
    
    Example usage:
        clusterer = POIClusterer(
            pois=my_pois,
            search_radius_km=10.0,
            target_clusters=7  # 7-day trip
        )
        
        clusters, anchors = clusterer.cluster()
        for cluster_id, cluster_pois in clusters.items():
            print(f"Cluster {cluster_id}: {len(cluster_pois)} POIs")
            print(f"  Anchor: {anchors[cluster_id].name}")
    """
    
    def __init__(
        self,
        pois: List[PointOfInterest],
        search_radius_km: float = 10.0,
        min_samples: Optional[int] = None,
        eps_km: Optional[float] = None,
        anchor_method: str = "centroid",
        target_clusters: Optional[int] = None,
        filter_worth_visiting: bool = False,
        min_cluster_size_for_filtering: int = 5,
        max_pois_per_cluster: Optional[int] = None,
        max_restaurants_per_cluster: Optional[int] = None,
        enhance_with_google_details: bool = False,
        language_code: Optional[str] = None,
        region_code: Optional[str] = None
    ):
        """
        Initialize the POI Clusterer with POIs and configuration parameters.
        
        Args:
            pois: List of PointOfInterest objects to cluster
            search_radius_km: Search radius in kilometers (used for H3 resolution)
            min_samples: Minimum samples for DBSCAN (auto-calculated if None)
            eps_km: DBSCAN epsilon in km (auto-calculated if None)
            anchor_method: Method to select anchors ("centroid", "highest_rated", "most_popular")
            target_clusters: Target number of clusters (e.g., trip days)
            filter_worth_visiting: Filter out low-quality POIs
            min_cluster_size_for_filtering: Min cluster size to apply filtering
            max_pois_per_cluster: Max non-restaurant POIs per cluster (None = no limit)
            max_restaurants_per_cluster: Max restaurants per cluster (None = no limit)
            enhance_with_google_details: Enhance with Google Places Details API
            language_code: Language code for Google API calls
            region_code: Region code for Google API calls
        """
        self.pois = pois
        self.search_radius_km = search_radius_km
        self.min_samples = min_samples
        self.eps_km = eps_km
        self.anchor_method = anchor_method
        self.target_clusters = target_clusters
        self.filter_worth_visiting = filter_worth_visiting
        self.min_cluster_size_for_filtering = min_cluster_size_for_filtering
        self.max_pois_per_cluster = max_pois_per_cluster
        self.max_restaurants_per_cluster = max_restaurants_per_cluster
        self.enhance_with_google_details = enhance_with_google_details
        self.language_code = language_code
        self.region_code = region_code
        
    # ========================================================================
    # Public Methods
    # ========================================================================
    
    def cluster(self) -> Tuple[Dict[int, List[PointOfInterest]], Dict[int, PointOfInterest]]:
        """
        Main entry point: Cluster POIs and return clusters with anchors.
        
        Returns:
            Tuple of (clusters_dict, anchors_dict) where:
            - clusters_dict: Maps cluster_id to list of POIs in that cluster
            - anchors_dict: Maps cluster_id to the anchor POI for that cluster
        """
        # Validate inputs
        if not self.pois:
            return {}, {}
        
        # Filter POIs with valid coordinates
        valid_pois = [
            poi for poi in self.pois 
            if poi.location.latitude is not None and poi.location.longitude is not None
        ]
        
        if len(valid_pois) < 2:
            # If less than 2 valid POIs, return individual clusters
            clusters = {i: [poi] for i, poi in enumerate(valid_pois)}
            anchors = {i: poi for i, poi in enumerate(valid_pois)}
            return clusters, anchors
        
        # Calculate smart parameters
        min_samples = self.min_samples
        eps_km = self.eps_km
        
        smart_min_samples, smart_eps_km = self._calculate_smart_clustering_params(valid_pois)
        if min_samples is None:
            min_samples = smart_min_samples
        if eps_km is None:
            eps_km = smart_eps_km
        
        # Perform clustering
        clusters = self._cluster_pois_with_h3_and_dbscan(
            valid_pois, min_samples, eps_km
        )
        
        # If we have more clusters than target, merge the smallest clusters
        if self.target_clusters and self.target_clusters > 0 and len(clusters) > self.target_clusters:
            clusters = self._merge_clusters_to_target(clusters)
        
        # Filter clusters by worth visiting criteria if requested
        if self.filter_worth_visiting:
            clusters = self._filter_clusters_by_worth_visiting(clusters)
        
        # Limit restaurants per cluster if requested (0 means no limit)
        clusters = self._limit_restaurants_per_cluster(clusters)
        
        # Enhance POIs with Google Places Details if requested
        if self.enhance_with_google_details:
            clusters = self._enhance_pois_with_google_details(clusters)
        
        # Find anchors
        anchors = self._find_cluster_anchors(clusters)
        
        return clusters, anchors
    
    # ========================================================================
    # Core Clustering Methods
    # ========================================================================
    
    def _cluster_pois_with_h3_and_dbscan(
        self,
        pois: List[PointOfInterest],
        min_samples: int,
        eps_km: float
    ) -> Dict[int, List[PointOfInterest]]:
        """
        Cluster PointOfInterest objects using H3 hexagons for initial grouping
        and DBSCAN for fine-grained clustering within hexagons.
        """
        if not pois:
            return {}
        
        # Determine H3 resolution based on search radius
        h3_resolution = self._get_h3_resolution_for_radius()
        
        # Group POIs by H3 hexagons
        h3_groups = {}
        
        try:
            import h3
            
            for poi in pois:
                # Get H3 hexagon for this POI
                hex_id = h3.latlng_to_cell(poi.location.latitude, poi.location.longitude, h3_resolution)
                
                if hex_id not in h3_groups:
                    h3_groups[hex_id] = []
                h3_groups[hex_id].append(poi)
                
        except ImportError:
            # Fallback: if H3 is not available, use simple DBSCAN
            print("Warning: H3 library not available, using DBSCAN-only clustering")
            return self._cluster_pois_with_dbscan_only(pois, min_samples, eps_km)
        
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
    
    def _cluster_pois_with_dbscan_only(
        self,
        pois: List[PointOfInterest],
        min_samples: int,
        eps_km: float
    ) -> Dict[int, List[PointOfInterest]]:
        """Fallback clustering method using only DBSCAN without H3 preprocessing."""
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
    
    def _find_cluster_anchors(
        self,
        clusters: Dict[int, List[PointOfInterest]]
    ) -> Dict[int, PointOfInterest]:
        """Find anchor POIs for each cluster using the configured method."""
        anchors = {}
        
        for cluster_id, cluster_pois in clusters.items():
            if not cluster_pois:
                continue
            
            if self.anchor_method == "centroid":
                # Find POI closest to cluster centroid
                avg_lat = sum(poi.location.latitude for poi in cluster_pois) / len(cluster_pois)
                avg_lon = sum(poi.location.longitude for poi in cluster_pois) / len(cluster_pois)
                
                min_distance = float('inf')
                anchor = cluster_pois[0]
                
                for poi in cluster_pois:
                    distance = self.haversine_distance(
                        avg_lat, avg_lon,
                        poi.location.latitude, poi.location.longitude
                    )
                    if distance < min_distance:
                        min_distance = distance
                        anchor = poi
                
                anchors[cluster_id] = anchor
                
            elif self.anchor_method == "highest_rated":
                # Find POI with highest rating
                anchor = max(cluster_pois, key=lambda poi: poi.rating or 0)
                anchors[cluster_id] = anchor
                
            elif self.anchor_method == "most_popular":
                # Find POI with most user ratings
                anchor = max(cluster_pois, key=lambda poi: poi.user_rating_count or 0)
                anchors[cluster_id] = anchor
                
            else:
                # Default to first POI
                anchors[cluster_id] = cluster_pois[0]
        
        return anchors
    
    def _calculate_smart_clustering_params(self, pois: List[PointOfInterest]) -> Tuple[int, float]:
        """Calculate smart clustering parameters based on dataset characteristics."""
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
                    distance = self.haversine_distance(
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
        if self.target_clusters and self.target_clusters > 0:
            expected_pois_per_cluster = num_pois / self.target_clusters
            if expected_pois_per_cluster < 2:
                min_samples = 2
            elif expected_pois_per_cluster < 3:
                min_samples = 2
            elif expected_pois_per_cluster < 5:
                min_samples = 3
            else:
                min_samples = min(5, max(3, int(expected_pois_per_cluster * 0.6)))
        else:
            if num_pois <= 5:
                min_samples = 2
            elif num_pois <= 15:
                min_samples = max(2, min(3, num_pois // 5))
            elif num_pois <= 50:
                min_samples = max(3, min(5, num_pois // 10))
            else:
                min_samples = max(5, min(8, num_pois // 15))
        
        # Smart eps_km calculation
        if self.target_clusters and self.target_clusters > 0:
            expected_pois_per_cluster = num_pois / self.target_clusters
            
            if avg_distance < 1.0:
                base_eps = max(0.5, min_distance * 3)
            elif avg_distance < 3.0:
                base_eps = max(1.0, avg_distance * 0.8)
            elif avg_distance < 10.0:
                base_eps = max(2.0, avg_distance * 0.6)
            else:
                base_eps = max(5.0, avg_distance * 0.4)
            
            if self.target_clusters < num_pois / 3:
                eps_km = base_eps * 1.5
            elif self.target_clusters > num_pois / 2:
                eps_km = base_eps * 0.7
            else:
                eps_km = base_eps
        else:
            if avg_distance < 1.0:
                eps_km = max(0.5, min_distance * 3)
            elif avg_distance < 3.0:
                eps_km = max(1.0, avg_distance * 0.8)
            elif avg_distance < 10.0:
                eps_km = max(2.0, avg_distance * 0.6)
            else:
                eps_km = max(5.0, avg_distance * 0.4)
        
        # Apply constraints
        eps_km = max(0.5, min(eps_km, 15.0))
        
        return min_samples, eps_km
    
    # ========================================================================
    # Filtering and Enhancement Methods
    # ========================================================================
    
    def _merge_clusters_to_target(
        self,
        clusters: Dict[int, List[PointOfInterest]]
    ) -> Dict[int, List[PointOfInterest]]:
        """Merge clusters to achieve the target number by combining the smallest clusters."""
        if len(clusters) <= self.target_clusters:
            return clusters
        
        # Convert to list of (cluster_id, cluster_pois) sorted by size (smallest first)
        cluster_items = [(cluster_id, cluster_pois) for cluster_id, cluster_pois in clusters.items()]
        cluster_items.sort(key=lambda x: len(x[1]))
        
        # Merge smallest clusters until we reach target
        merged_clusters = {}
        next_cluster_id = 0
        
        # Keep the largest clusters as-is
        clusters_to_keep = cluster_items[-(self.target_clusters-1):] if self.target_clusters > 1 else []
        for cluster_id, cluster_pois in clusters_to_keep:
            merged_clusters[next_cluster_id] = cluster_pois
            next_cluster_id += 1
        
        # Merge all remaining small clusters into one
        if self.target_clusters > 0:
            remaining_pois = []
            for cluster_id, cluster_pois in cluster_items[:-(self.target_clusters-1)] if self.target_clusters > 1 else cluster_items:
                remaining_pois.extend(cluster_pois)
            
            if remaining_pois:
                merged_clusters[next_cluster_id] = remaining_pois
        
        return merged_clusters
    
    def _filter_clusters_by_worth_visiting(
        self,
        clusters: Dict[int, List[PointOfInterest]]
    ) -> Dict[int, List[PointOfInterest]]:
        """Filter clusters to remove places not worth visiting."""
        filtered_clusters = {}
        
        # First pass: filter clusters by worth visiting criteria
        for cluster_id, cluster_pois in clusters.items():
            if len(cluster_pois) < self.min_cluster_size_for_filtering:
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
        
        # Second pass: limit non-restaurant POIs within each cluster (if max_pois_per_cluster is set)
        if self.max_pois_per_cluster is not None:
            for cluster_id, cluster_pois in filtered_clusters.items():
                # Separate restaurants from other POIs
                restaurants = [poi for poi in cluster_pois if is_restaurant(poi)]
                other_pois = [poi for poi in cluster_pois if not is_restaurant(poi)]
                
                # Limit only non-restaurant POIs
                if len(other_pois) > self.max_pois_per_cluster:
                    # Sort non-restaurant POIs by visitability score (highest first)
                    sorted_other_pois = sorted(
                        other_pois, 
                        key=lambda poi: poi.get_visitability_score(), 
                        reverse=True
                    )
                    limited_other_pois = sorted_other_pois[:self.max_pois_per_cluster]
                    filtered_clusters[cluster_id] = restaurants + limited_other_pois
                else:
                    filtered_clusters[cluster_id] = restaurants + other_pois
        
        # Third pass: sort by visitability score and limit to target_clusters
        if self.target_clusters is None or len(filtered_clusters) <= self.target_clusters:
            return filtered_clusters
        
        # Calculate the best visitability score for each cluster
        cluster_scores = []
        for cluster_id, cluster_pois in filtered_clusters.items():
            best_score = max(
                (poi.get_visitability_score() for poi in cluster_pois),
                default=0.0
            )
            cluster_scores.append((cluster_id, best_score, cluster_pois))
        
        # Sort by visitability score (descending)
        cluster_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take only the top target_clusters clusters
        top_clusters = cluster_scores[:self.target_clusters]
        
        # Convert back to dictionary format
        result_clusters = {}
        for i, (original_cluster_id, score, cluster_pois) in enumerate(top_clusters):
            result_clusters[i] = cluster_pois
        
        return result_clusters
    
    def _limit_restaurants_per_cluster(
        self,
        clusters: Dict[int, List[PointOfInterest]]
    ) -> Dict[int, List[PointOfInterest]]:
        """Limit the number of restaurants in each cluster while preserving other POIs."""
        # If no limit is set, return clusters unchanged
        if self.max_restaurants_per_cluster is None:
            return clusters
        
        limited_clusters = {}
        
        for cluster_id, cluster_pois in clusters.items():
            # Separate restaurants from other POIs
            restaurants = [poi for poi in cluster_pois if is_restaurant(poi)]
            other_pois = [poi for poi in cluster_pois if not is_restaurant(poi)]
            
            # Limit restaurants if there are too many
            if len(restaurants) > self.max_restaurants_per_cluster:
                # Sort restaurants by visitability score (highest first)
                sorted_restaurants = sorted(
                    restaurants, 
                    key=lambda poi: poi.get_visitability_score(), 
                    reverse=True
                )
                limited_restaurants = sorted_restaurants[:self.max_restaurants_per_cluster]
                print(f"Limited cluster {cluster_id}: {len(restaurants)} restaurants -> {len(limited_restaurants)} restaurants")
            else:
                limited_restaurants = restaurants
            
            # Combine limited restaurants with other POIs
            limited_clusters[cluster_id] = limited_restaurants + other_pois
        
        return limited_clusters
    
    def _enhance_pois_with_google_details(
        self,
        clusters: Dict[int, List[PointOfInterest]]
    ) -> Dict[int, List[PointOfInterest]]:
        """Enhance PointOfInterest objects with detailed information from Google Places API."""
        enhanced_clusters = {}
        
        for cluster_id, cluster_pois in clusters.items():
            enhanced_pois = []
            
            for poi in cluster_pois:
                try:
                    # Only enhance POIs that have a Google place_id
                    place_id = None
                    if hasattr(poi, 'google_data') and poi.google_data and hasattr(poi.google_data, 'id'):
                        place_id = poi.google_data.id
                    
                    if place_id:
                        # Call Google Places Details API - returns enhanced GooglePlace object
                        enhanced_google_place = google_place_details(
                            place_id=place_id,
                            language_code=self.language_code,
                            region_code=self.region_code
                        )
                        
                        # Create enhanced POI with the updated GooglePlace
                        poi_data = poi.dict()
                        poi_data['google_data'] = enhanced_google_place
                        enhanced_poi = PointOfInterest(**poi_data)
                        enhanced_pois.append(enhanced_poi)
                        
                    else:
                        # Keep original POI if no place_id available
                        enhanced_pois.append(poi)
                        
                except Exception as e:
                    print(f"Warning: Failed to enhance POI {poi.name}: {str(e)}")
                    place_id_str = place_id if place_id else 'N/A'
                    print(f"Place ID: {place_id_str}")
                    # Keep original POI if enhancement fails
                    enhanced_pois.append(poi)
            
            enhanced_clusters[cluster_id] = enhanced_pois
        
        return enhanced_clusters
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _calculate_cluster_center(self, cluster_pois: List[PointOfInterest]) -> Tuple[float, float]:
        """Calculate the geographic centroid of a cluster."""
        if not cluster_pois:
            return (0.0, 0.0)
        
        avg_lat = sum(poi.location.latitude for poi in cluster_pois) / len(cluster_pois)
        avg_lon = sum(poi.location.longitude for poi in cluster_pois) / len(cluster_pois)
        return (avg_lat, avg_lon)
    
    def _get_h3_resolution_for_radius(self) -> int:
        """Determine appropriate H3 resolution based on search radius."""
        radius_km = self.search_radius_km
        
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
    
    @staticmethod
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
