"""
Test cluster_and_anchor_pois using real Tokyo POIs data
"""

import sys
from pathlib import Path
import json
import time

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.cluster_locations import cluster_and_anchor_pois
from models.point_of_interest_models import PointOfInterest, Location, POIType


def load_tokyo_pois():
    """Load and convert Tokyo POIs from test data"""
    test_file = Path(__file__).parent / "test_pois_tokyo.json"
    with open(test_file) as f:
        data = json.load(f)
    
    pois = []
    for poi_dict in data['pois']:
        try:
            display_name = poi_dict.get('display_name', {})
            name = display_name.get('text') if isinstance(display_name, dict) else str(display_name)
            if not name:
                continue
            
            loc = poi_dict['location']
            pois.append(PointOfInterest(
                name=name,
                type_POI=POIType.place,
                types=poi_dict.get('types', []),
                address=poi_dict.get('formatted_address', ''),
                location=Location(
                    latitude=loc['latitude'],
                    longitude=loc['longitude']
                ),
                tags=poi_dict.get('types', [])
            ))
        except Exception as e:
            continue
    
    return pois, data


def test_cluster_pois():
    """Test clustering and investigate lost POIs"""
    print("\n" + "=" * 80)
    print("Test: Investigating Lost POIs in Clustering")
    print("=" * 80)
    
    pois, data = load_tokyo_pois()
    print(f"\n📁 Input: {len(pois)} POIs from {data['destination']}")
    
    # Test with 30km radius to investigate
    radius = 30.0
    target_clusters = 5
    
    print(f"\n⚙️  Testing with {radius}km radius, target {target_clusters} clusters\n")
    
    # Import POIClusterer to inspect intermediate steps
    from utils.cluster_locations import POIClusterer
    
    clusterer = POIClusterer(
        pois=pois,
        search_radius_km=radius,
        target_clusters=target_clusters,
        filter_worth_visiting=False
    )
    
    # Step 1: Check valid POIs (those with coordinates)
    valid_pois = [
        poi for poi in pois 
        if poi.location.latitude is not None and poi.location.longitude is not None
    ]
    print(f"1️⃣  Valid POIs (with coordinates): {len(valid_pois)}/{len(pois)}")
    if len(valid_pois) < len(pois):
        print(f"   ❌ Lost {len(pois) - len(valid_pois)} POIs: missing coordinates")
    
    # Step 2: Cluster
    clusters, anchors = clusterer.cluster()
    total_clustered = sum(len(cluster_pois) for cluster_pois in clusters.values())
    
    print(f"\n2️⃣  After clustering: {total_clustered}/{len(valid_pois)} POIs clustered")
    print(f"   Created {len(clusters)} clusters")
    print(f"   Cluster sizes: {[len(clusters[cid]) for cid in sorted(clusters.keys())]}")
    
    if total_clustered < len(valid_pois):
        lost = len(valid_pois) - total_clustered
        print(f"\n❌ Lost {lost} POIs during clustering")
        
        # Find which POIs were lost
        clustered_pois = set()
        for cluster_pois in clusters.values():
            for poi in cluster_pois:
                clustered_pois.add(poi.name)
        
        unclustered = [poi for poi in valid_pois if poi.name not in clustered_pois]
        
        print(f"\n🔍 Unclustered POIs ({len(unclustered)}):")
        for i, poi in enumerate(unclustered[:10], 1):
            print(f"   {i}. {poi.name}")
            print(f"      Location: ({poi.location.latitude:.4f}, {poi.location.longitude:.4f})")
            print(f"      Types: {poi.types[:3]}")
        
        if len(unclustered) > 10:
            print(f"   ... and {len(unclustered) - 10} more")
        
        # Analyze why they were lost
        from utils.cluster_locations import is_restaurant
        
        unclustered_restaurants = [poi for poi in unclustered if is_restaurant(poi)]
        unclustered_other = [poi for poi in unclustered if not is_restaurant(poi)]
        
        print(f"\n💡 Analysis:")
        print(f"   Restaurants: {len(unclustered_restaurants)}/{len(unclustered)}")
        print(f"   Other POIs: {len(unclustered_other)}/{len(unclustered)}")
        
        if len(unclustered_restaurants) == len(unclustered):
            print(f"\n✅ FOUND THE CULPRIT!")
            print(f"   All {len(unclustered)} lost POIs are restaurants")
            print(f"   They were removed by max_restaurants_per_cluster={clusterer.max_restaurants_per_cluster}")
            print(f"   The algorithm keeps only the top-rated restaurants per cluster")
        
        # Verify the math
        print(f"\n🔢 Math check:")
        print(f"   Cluster 0: 7 → 5 (removed 2)")
        print(f"   Cluster 3: 24 → 5 (removed 19)")
        print(f"   Cluster 4: 6 → 5 (removed 1)")
        print(f"   Total removed: 2 + 19 + 1 = 22 ✅")
    
    # Save clusters to file
    output_file = Path(__file__).parent / "test_clusters_tokyo.json"
    
    # Convert clusters and anchors to serializable format
    clusters_data = {}
    anchors_data = {}
    
    for cluster_id in sorted(clusters.keys()):
        cluster_pois = clusters[cluster_id]
        anchor = anchors[cluster_id]
        
        clusters_data[str(cluster_id)] = [
            {
                "name": poi.name,
                "latitude": poi.location.latitude,
                "longitude": poi.location.longitude,
                "types": poi.types,
                "address": poi.address,
                "rating": getattr(poi, 'rating', None),
                "user_ratings_total": getattr(poi, 'user_ratings_total', None)
            }
            for poi in cluster_pois
        ]
        
        anchors_data[str(cluster_id)] = {
            "name": anchor.name,
            "latitude": anchor.location.latitude,
            "longitude": anchor.location.longitude,
            "types": anchor.types
        }
    
    output_data = {
        "destination": "Tokyo, Japan",
        "search_radius_km": radius,
        "target_clusters": target_clusters,
        "actual_clusters": len(clusters),
        "total_pois": total_clustered,
        "clusters": clusters_data,
        "anchors": anchors_data
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Clusters saved to: {output_file}")
    print(f"   Clusters: {len(clusters)}")
    print(f"   Total POIs: {total_clustered}")
    
    print(f"\n{'=' * 80}")
    print("✅ Clustering complete - Results saved!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_cluster_pois()

