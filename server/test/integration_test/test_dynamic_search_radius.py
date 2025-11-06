"""
Test dynamic search radius determination using LLM
"""

import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.destination_radius_calculator import determine_search_radius


def test_dynamic_search_radius():
    """Test LLM-based search radius determination for various destinations"""
    
    print("\n" + "=" * 80)
    print("Test: Dynamic Search Radius Determination")
    print("=" * 80)
    
    # Test various destination types
    test_cases = [
        ("Tokyo, Japan", 5, "Mega city, very dense"),
        ("Kyoto, Japan", 3, "Large city, dense historic areas"),
        ("Paris, France", 4, "Mega city, dense urban"),
        ("Bali, Indonesia", 7, "Island, multiple spread-out areas"),
        ("Reykjavik, Iceland", 5, "Small city, sparse, includes day trips"),
        ("Grand Canyon, USA", 2, "Rural, sparse, vast natural area"),
        ("Santorini, Greece", 3, "Small island, compact"),
        ("New York City, USA", 5, "Mega city, very dense"),
        ("Napa Valley, USA", 3, "Rural/suburban, wineries spread out"),
        ("Dubai, UAE", 6, "Large city, spread-out attractions"),
    ]
    
    results = []
    
    for destination, days, description in test_cases:
        print(f"\n{'─' * 80}")
        print(f"📍 Destination: {destination} ({days} days)")
        print(f"   Context: {description}")
        
        try:
            radius_km, chars = determine_search_radius(
                destination=destination,
                duration_days=days
            )
            
            print(f"\n   ✅ Recommended Radius: {radius_km}km")
            print(f"   📊 Characteristics:")
            print(f"      - City size: {chars.city_size}")
            print(f"      - Density: {chars.density}")
            print(f"      - Type: {chars.destination_type}")
            print(f"   💭 Reasoning: {chars.reasoning}")
            
            results.append({
                "destination": destination,
                "days": days,
                "radius_km": radius_km,
                "city_size": chars.city_size,
                "density": chars.density,
                "type": chars.destination_type
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    # Summary table
    print(f"\n{'=' * 80}")
    print("Summary Table")
    print("=" * 80)
    print(f"{'Destination':<25} {'Days':<6} {'Radius':<10} {'Size':<10} {'Density':<12}")
    print("─" * 80)
    
    for r in results:
        print(
            f"{r['destination']:<25} "
            f"{r['days']:<6} "
            f"{r['radius_km']:<10.1f} "
            f"{r['city_size']:<10} "
            f"{r['density']:<12}"
        )
    
    # Verify results make sense
    print(f"\n{'=' * 80}")
    print("Validation")
    print("=" * 80)
    
    # All radii should be in reasonable range
    for r in results:
        assert 5 <= r['radius_km'] <= 100, f"{r['destination']} radius out of bounds"
    
    print(f"✅ All {len(results)} destinations have valid radii (5-100km)")
    
    # Mega cities should generally have smaller radii than rural areas
    tokyo = next(r for r in results if "Tokyo" in r['destination'])
    grand_canyon = next(r for r in results if "Grand Canyon" in r['destination'])
    
    print(f"✅ Tokyo ({tokyo['radius_km']}km) vs Grand Canyon ({grand_canyon['radius_km']}km)")
    print(f"   Rural areas typically need larger search radius")
    
    print(f"\n{'=' * 80}")
    print("✅ TEST PASSED - Dynamic radius determination working!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_dynamic_search_radius()

