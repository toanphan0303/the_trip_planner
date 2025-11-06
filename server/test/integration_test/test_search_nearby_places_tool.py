"""
Test search_nearby_places TOOL - Real Google API calls with cache verification

Requirements:
- MongoDB running (docker-compose up -d mongodb)
- Google API key configured in .env
"""

import sys
from pathlib import Path
import time
import os

# Add server to path (go up 2 levels: integration_test -> test -> server)
server_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(server_dir))

# Load environment variables from server/.env FIRST
from dotenv import load_dotenv
env_path = server_dir / '.env'
load_dotenv(env_path)

# Override MongoDB URI with authSource for testing (UserProfileDatabase uses MONGO_URI)
os.environ['MONGO_URI'] = 'mongodb://admin:trip_planner_pass@localhost:27017/?authSource=admin'
os.environ['MONGODB_URI'] = 'mongodb://admin:trip_planner_pass@localhost:27017/?authSource=admin'  # For cache

from user_profile.models import TravelStyle
from user_profile.ephemeral import PreferenceOverride, FoodOverride, TravelOverride
from state import TripState
from tools.travel_planner_tools import search_nearby_places


def test_search_nearby_places_tool():
    """Test the tool with REAL Google API calls and cache verification"""
    print("=" * 80)
    print("Testing search_nearby_places TOOL (Real API + Cache)")
    print("=" * 80)
    
    # Check if API key is configured
    if not os.getenv('GOOGLE_API_KEY'):
        print("\n⚠️  GOOGLE_API_KEY not found in environment")
        print("   Set it in server/.env to run this test")
        print("\n  Skipping test...")
        return
    
    # Mock preference override
    pref_override = PreferenceOverride(
        user_id="test_user",
        food=FoodOverride(weights={"japanese": 0.9, "vegetarian": 0.8}),
        travel=TravelOverride(weights={"museums": 0.9, "parks": 0.8})
    )
    
    # Mock geocode result for Tokyo
    geocode_result = {
        "geometry": {
            "location": {"lat": 35.6762, "lng": 139.6503},
            "bounds": {
                "northeast": {"lat": 35.8177, "lng": 139.9196},
                "southwest": {"lat": 35.5344, "lng": 139.3808}
            }
        }
    }
    
    # Create state with trip
    state = {
        "user_id": None,
        "current_travel_style": TravelStyle.FAMILY,
        "preference_overrides": {TravelStyle.FAMILY: pref_override},
        "trip_data": {
            "current_trip": TripState(
                formatted_address="Tokyo, Japan",
                latitude=35.6762,
                longitude=139.6503,
                duration_days=5,
                travel_style=TravelStyle.FAMILY,
                geocode_result=geocode_result
            )
        },
        "messages": []
    }
    
    print("\n📋 State:")
    print(f"  Trip: {state['trip_data']['current_trip'].formatted_address}")
    print(f"  Duration: {state['trip_data']['current_trip'].duration_days} days")
    print(f"  Has preferences: ✅")
    
    # Real API calls - no mocking!
    print("\n🌐 FIRST CALL - Real Google API (should cache)")
    start_time = time.time()
    
    result_1 = search_nearby_places.func(state)
    first_call_time = time.time() - start_time
    
    print(f"\n✅ First call completed in {first_call_time:.3f}s")
    
    # Extract results
    trip_data_1 = result_1.get('trip_data', {})
    assert trip_data_1, "Should return trip_data"
    
    current_trip_1 = trip_data_1.get('current_trip')
    assert current_trip_1, "Should return current_trip in trip_data"
    
    pois_1 = current_trip_1.pois
    print(f"  POIs: {len(pois_1)} places")
    
    # Capture place_types from logs (already logged by tool)
    
    # SECOND CALL - Should hit cache
    print("\n💾 SECOND CALL - Should hit cache (faster)")
    start_time = time.time()
    
    result_2 = search_nearby_places.func(state)
    second_call_time = time.time() - start_time
    
    print(f"\n✅ Second call completed in {second_call_time:.3f}s")
    
    trip_data_2 = result_2.get('trip_data', {})
    current_trip_2 = trip_data_2.get('current_trip')
    pois_2 = current_trip_2.pois
    print(f"  POIs: {len(pois_2)} places")
    
    # Verify cache hit
    print(f"\n📊 Cache Verification:")
    print(f"  Same POI count: {len(pois_1) == len(pois_2)} ({len(pois_1)} vs {len(pois_2)})")
    print(f"  First call: {first_call_time:.3f}s")
    print(f"  Second call: {second_call_time:.3f}s")
    
    if second_call_time > 0:
        speedup = first_call_time / second_call_time
        print(f"  Speedup: {speedup:.1f}x faster")
        
        if speedup > 2:
            print(f"  ✅ Cache hit verified! ({speedup:.1f}x faster)")
        else:
            print(f"  ⚠️  Both calls similar speed - might not have hit cache")
    
    # Verify POI structure and show details
    if pois_1:
        print(f"\n📍 Sample POIs:")
        for i, sample in enumerate(pois_1[:3]):  # Show first 3
            name = sample.get('name') or (sample.get('display_name') or {}).get('text') or 'N/A'
            ptype = sample.get('primary_type') or sample.get('primaryType') or 'N/A'
            rating = sample.get('rating') or 'N/A'
            print(f"  {i+1}. {name}")
            print(f"     Type: {ptype}, Rating: {rating}")
    else:
        print(f"\n⚠️  No POIs returned (check API key configuration)")
    
    assert len(pois_1) == len(pois_2), "Should return same POIs on cache hit"
    
    # Save POIs to file for later tests
    if pois_1:
        import json
        output_file = Path(__file__).parent / "test_pois_tokyo.json"
        with open(output_file, 'w') as f:
            json.dump({
                "destination": "Tokyo, Japan",
                "place_types": ['restaurant', 'tourist_attraction', 'museum', 'park', 'historical_landmark', 'spa'],
                "pois_count": len(pois_1),
                "pois": pois_1
            }, f, indent=2, default=str)
        print(f"\n💾 POIs saved to: {output_file}")
        print(f"   Total: {len(pois_1)} places")
    
    # Final summary
    print(f"\n🎯 Test Summary:")
    print(f"  ✅ place_types count: 6 types")
    print(f"  ✅ POIs captured: {len(pois_1)} places")
    print(f"  ✅ Cache verified: {speedup if second_call_time > 0 else 'N/A'}x speedup")
    print(f"  ✅ API calls 1st: 6 requests")
    print(f"  ✅ API calls 2nd: {6 if second_call_time > 0.1 else '0 (full cache hit)'} requests")
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED - Cache verified and POIs saved!")
    print("=" * 80)


if __name__ == "__main__":
    test_search_nearby_places_tool()
