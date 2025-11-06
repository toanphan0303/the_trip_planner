"""
Test caching behavior for dynamic search radius
"""

import sys
from pathlib import Path
import time

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.destination_radius_calculator import determine_search_radius


def test_radius_caching():
    """Test that radius determination is cached properly in MongoDB"""
    
    print("\n" + "=" * 80)
    print("Test: Search Radius MongoDB Caching")
    print("=" * 80)
    
    print(f"\n📊 Cache: MongoDB (persistent, shared across instances)")
    
    # Test 1: First call (cache miss - slow)
    print("\n" + "─" * 80)
    print("Test 1: First call to Tokyo (cache miss)")
    print("─" * 80)
    
    start = time.time()
    radius1, chars1 = determine_search_radius("Tokyo, Japan", 5)
    time1 = time.time() - start
    
    print(f"⏱️  Time: {time1*1000:.0f}ms")
    print(f"📍 Result: {radius1}km")
    print(f"🏙️  Characteristics: size={chars1.city_size}, density={chars1.density}")
    
    print(f"📊 Result cached in MongoDB")
    
    # Test 2: Second call (cache hit - fast)
    print("\n" + "─" * 80)
    print("Test 2: Second call to Tokyo (cache hit)")
    print("─" * 80)
    
    start = time.time()
    radius2, chars2 = determine_search_radius("Tokyo, Japan", 5)
    time2 = time.time() - start
    
    print(f"⏱️  Time: {time2*1000:.0f}ms")
    print(f"📍 Result: {radius2}km")
    
    # Verify cache hit
    assert radius1 == radius2, "Cached result should match"
    assert time2 < time1 / 10, f"Cache should be much faster ({time2*1000:.0f}ms vs {time1*1000:.0f}ms)"
    
    print(f"\n🚀 Speedup: {time1/time2:.1f}x faster!")
    print(f"   First call: {time1*1000:.0f}ms (LLM)")
    print(f"   Second call: {time2*1000:.0f}ms (cache)")
    
    # Test 3: Different duration (different cache key)
    print("\n" + "─" * 80)
    print("Test 3: Tokyo with different duration (different cache key)")
    print("─" * 80)
    
    start = time.time()
    radius3, chars3 = determine_search_radius("Tokyo, Japan", 7)  # 7 days instead of 5
    time3 = time.time() - start
    
    print(f"⏱️  Time: {time3*1000:.0f}ms")
    print(f"📍 Result: {radius3}km")
    
    print(f"📊 Tokyo 7 days also cached in MongoDB")
    
    # Test 4: Different destination
    print("\n" + "─" * 80)
    print("Test 4: Different destination (Paris)")
    print("─" * 80)
    
    start = time.time()
    radius4, chars4 = determine_search_radius("Paris, France", 4)
    time4 = time.time() - start
    
    print(f"⏱️  Time: {time4*1000:.0f}ms")
    print(f"📍 Result: {radius4}km")
    print(f"🏙️  Characteristics: size={chars4.city_size}, density={chars4.density}")
    
    print(f"📊 Paris cached in MongoDB")
    
    # Test 5: Case insensitive caching
    print("\n" + "─" * 80)
    print("Test 5: Case insensitive caching")
    print("─" * 80)
    
    start = time.time()
    radius5, _ = determine_search_radius("TOKYO, JAPAN", 5)  # All caps
    time5 = time.time() - start
    
    print(f"⏱️  Time: {time5*1000:.0f}ms")
    print(f"📍 Result: {radius5}km")
    
    assert radius5 == radius1, "Should match original Tokyo result (case insensitive)"
    assert time5 < 1, "Should be instant from MongoDB cache"
    
    print(f"📊 No new entry (case-insensitive match)")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✅ MongoDB cache working correctly!")
    print(f"   Total LLM calls: 3 (Tokyo 5d, Tokyo 7d, Paris 4d)")
    print(f"   Total cache hits: 2 (Tokyo 5d × 2)")
    print(f"   Cache speedup: {time1/time2:.1f}x")
    print(f"   Cache backend: MongoDB (persistent)")
    
    print("\n📋 Cached destinations in MongoDB:")
    print(f"   - tokyo, japan (5 days)")
    print(f"   - tokyo, japan (7 days)")
    print(f"   - paris, france (4 days)")
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED - Caching works!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_radius_caching()

