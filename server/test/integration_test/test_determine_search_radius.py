"""
Test determine_search_radius with MongoDB cache - Main flow only
"""

import sys
import os
from pathlib import Path
import time
from dotenv import load_dotenv

# Load environment variables from server/.env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Setup MongoDB connection
os.environ['MONGODB_URI'] = 'mongodb://admin:trip_planner_pass@localhost:27017/?authSource=admin'

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.destination_radius_calculator import determine_search_radius


def check_google_credentials():
    """Check if Google API credentials are configured"""
    return bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('GOOGLE_API_KEY'))


def test_determine_search_radius_main_flow():
    """Test main flow: LLM call → MongoDB cache → Cache hit"""
    
    print("\n" + "=" * 80)
    print("Test: determine_search_radius Main Flow")
    print("=" * 80)
    
    # Check if Google credentials are configured
    if not check_google_credentials():
        print("\n⚠️  Warning: Google credentials not configured")
        print("   Set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_API_KEY in server/.env")
        print("   Test will use fallback mode\n")
    
    destination = "Tokyo, Japan"
    duration_days = 5
    
    # Mock geocode result
    geocode_result = {
        "geometry": {
            "location": {"lat": 35.6762, "lng": 139.6503},
            "bounds": {
                "northeast": {"lat": 35.8986, "lng": 139.9199},
                "southwest": {"lat": 35.5329, "lng": 139.3512}
            }
        }
    }
    
    # Test 1: First call (should call LLM and cache to MongoDB)
    print(f"\n1️⃣  First call: {destination} ({duration_days} days)")
    print("   Expected: LLM call + MongoDB cache save (or fallback)")
    print("─" * 80)
    
    start = time.time()
    radius1 = determine_search_radius(
        destination=destination,
        duration_days=duration_days,
        geocode_result=geocode_result
    )
    time1 = time.time() - start
    
    print(f"\n✅ Result:")
    print(f"   Search radius: {radius1}km")
    print(f"   Time: {time1*1000:.0f}ms")
    
    # Validate response
    assert radius1 >= 5.0, f"Radius should be at least 5km, got {radius1}km"
    assert radius1 <= 100.0, f"Radius should be at most 100km, got {radius1}km"
    assert isinstance(radius1, float), f"Radius should be float, got {type(radius1)}"
    
    print(f"✅ Validation passed: Radius is valid")
    
    # Test 2: Second call (should hit MongoDB cache)
    print(f"\n2️⃣  Second call: {destination} ({duration_days} days)")
    print("   Expected: MongoDB cache hit")
    print("─" * 80)
    
    start = time.time()
    radius2 = determine_search_radius(
        destination=destination,
        duration_days=duration_days,
        geocode_result=geocode_result
    )
    time2 = time.time() - start
    
    print(f"\n✅ Result:")
    print(f"   Search radius: {radius2}km")
    print(f"   Time: {time2*1000:.0f}ms")
    
    # Validate cache hit
    assert radius1 == radius2, f"Cached result should match original: {radius1} vs {radius2}"
    
    print(f"✅ Cache verification passed: Result matches exactly")
    
    # Verify speedup
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"\n⚡ Performance:")
    print(f"   First call (LLM):  {time1*1000:.0f}ms")
    print(f"   Second call (DB):  {time2*1000:.0f}ms")
    print(f"   Speedup: {speedup:.1f}x faster")
    
    assert time2 < time1 / 10, f"Cache should be much faster (got {time2*1000:.0f}ms vs {time1*1000:.0f}ms)"
    
    print(f"\n✅ Performance validation passed: Cache is significantly faster")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    print(f"✅ Result: {radius1}km for {destination}")
    print(f"✅ MongoDB Cache: Working correctly")
    print(f"✅ Cache Hit: {speedup:.1f}x speedup")
    print(f"✅ Return Type: float (simplified API)")
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED - Main flow verified!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_determine_search_radius_main_flow()

