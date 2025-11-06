#!/usr/bin/env python3
"""
Focused Test: EphemeralOverlay with Must Include / Exclude
Tests how user's explicit requests override base preferences
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))
load_dotenv(os.path.join(os.path.dirname(__file__), 'server', '.env'))

from user_profile.models import (
    UserPreference,
    TravelPreference,
    FoodPreference,
    TravelStyle
)
from user_profile.ephemeral.overlay import (
    EphemeralOverlay,
    TravelOverlay,
    FoodOverlay
)
from constant.place_types import PlaceTypes


def create_standard_family_base() -> UserPreference:
    """Standard family preference (baseline for overlay tests)"""
    return UserPreference.model_construct(
        user_id="family_standard",
        version="1.0.0",
        travel={
            TravelStyle.FAMILY.value: TravelPreference(
                travel_style_weights={"family_friendly": 0.8, "educational": 0.7},
                activity_weights={
                    "museums": 0.8,
                    "parks": 0.7,
                    "aquariums": 0.6
                },
                budget_score=0.5
            )
        },
        food={
            TravelStyle.FAMILY.value: FoodPreference(
                cuisine_weights={"local": 0.7, "kid_friendly": 0.8},
                food_type_weights={"family_restaurant": 0.7},
                budget_weight=0.5
            )
        },
        stay={}
    )


def test_overlay_scenarios():
    """Test various overlay scenarios with explicit inclusions/exclusions"""
    
    print("=" * 80)
    print("🧪 FOCUSED TEST: Ephemeral Overlay - Must Include / Exclude")
    print("=" * 80)
    print()
    print("Testing how explicit user requests override base preferences")
    print()
    
    base_pref = create_standard_family_base()
    destination = "Tokyo"
    travel_style = TravelStyle.FAMILY
    
    # ==========================================================================
    # SCENARIO 1: User says "I want to visit temples and shrines"
    # ==========================================================================
    print("=" * 80)
    print("SCENARIO 1: User wants temples (not in base preferences)")
    print("=" * 80)
    print()
    print("💬 User said: 'I really want to visit temples and shrines in Tokyo'")
    print("📋 Base preference: Museums (0.8), Parks (0.7), Aquariums (0.6)")
    print()
    
    overlay_temples = EphemeralOverlay(
        overlay_id="overlay_1",
        user_id="family_standard",
        scope="trip",
        confidence=0.9,
        source="chat",
        travel=TravelOverlay(
            activity_weights={
                "place_of_worship": 0.9,  # Valid type for temples/shrines
                "hindu_temple": 0.9,
                "historical_sites": 0.8
            }
        )
    )
    
    result_baseline = PlaceTypes.select_types_for_user(base_pref, destination, travel_style)
    result_with_temples = PlaceTypes.select_types_for_user(base_pref, destination, travel_style, overlay_temples)
    
    print(f"❌ WITHOUT overlay: {result_baseline}")
    has_worship_baseline = any(t in result_baseline for t in ['place_of_worship', 'hindu_temple', 'church'])
    print(f"   Has worship places: {'✅' if has_worship_baseline else '❌ NO'}")
    print()
    print(f"✅ WITH overlay: {result_with_temples}")
    has_worship_overlay = any(t in result_with_temples for t in ['place_of_worship', 'hindu_temple', 'church'])
    print(f"   Has worship places: {'✅ YES' if has_worship_overlay else '❌ NO'}")
    print(f"   Impact: {'✅ OVERLAY WORKED!' if has_worship_overlay and not has_worship_baseline else '⚠️  Overlay did not add temples'}")
    print()
    
    # ==========================================================================
    # SCENARIO 2: User says "No zoos, my kids are scared of animals"
    # ==========================================================================
    print("=" * 80)
    print("SCENARIO 2: User explicitly excludes zoos")
    print("=" * 80)
    print()
    print("💬 User said: 'No zoos please, my kids are scared of animals'")
    print()
    
    overlay_no_zoo = EphemeralOverlay(
        overlay_id="overlay_2",
        user_id="family_standard",
        scope="trip",
        confidence=1.0,  # Very high - explicit avoid
        source="chat",
        travel=TravelOverlay(
            avoids={
                "zoo": 0.9,
                "animal": 0.8
            }
        )
    )
    
    result_with_no_zoo = PlaceTypes.select_types_for_user(base_pref, destination, travel_style, overlay_no_zoo)
    
    print(f"❌ WITHOUT overlay: {result_baseline}")
    print(f"   Has 'zoo': {'⚠️  YES' if 'zoo' in result_baseline else '✅ NO'}")
    print()
    print(f"✅ WITH overlay: {result_with_no_zoo}")
    print(f"   Has 'zoo': {'❌ STILL THERE!' if 'zoo' in result_with_no_zoo else '✅ EXCLUDED'}")
    print(f"   Impact: {'✅ AVOIDED SUCCESSFULLY!' if 'zoo' not in result_with_no_zoo else '⚠️  Zoo still included'}")
    print()
    
    # ==========================================================================
    # SCENARIO 3: User says "We're vegetarian, no steakhouses or BBQ"
    # ==========================================================================
    print("=" * 80)
    print("SCENARIO 3: Dietary restriction - exclude meat restaurants")
    print("=" * 80)
    print()
    print("💬 User said: 'We're vegetarian, please exclude steakhouses and BBQ places'")
    print()
    
    overlay_vegetarian = EphemeralOverlay(
        overlay_id="overlay_3",
        user_id="family_standard",
        scope="trip",
        confidence=1.0,
        source="chat",
        food=FoodOverlay(
            cuisine_weights={
                "vegetarian": 0.9,
                "vegan": 0.6
            },
            hard_excludes_place_types=["steakhouse", "bbq_restaurant", "barbecue_restaurant"],
            must_include_keywords=["vegetarian_options"]
        )
    )
    
    result_with_veg = PlaceTypes.select_types_for_user(base_pref, destination, travel_style, overlay_vegetarian)
    
    print(f"❌ WITHOUT overlay: {result_baseline}")
    print()
    print(f"✅ WITH overlay: {result_with_veg}")
    excluded_check = not any(t in result_with_veg for t in ["steakhouse", "bbq_restaurant", "barbecue_restaurant"])
    print(f"   Steakhouse/BBQ excluded: {'✅ YES' if excluded_check else '❌ STILL THERE'}")
    print(f"   Impact: {'✅ EXCLUSION WORKED!' if excluded_check else '⚠️  Exclusion failed'}")
    print()
    
    # ==========================================================================
    # SCENARIO 4: User says "Must have shopping, we need souvenirs"
    # ==========================================================================
    print("=" * 80)
    print("SCENARIO 4: Must include shopping")
    print("=" * 80)
    print()
    print("💬 User said: 'We must include shopping for souvenirs'")
    print()
    
    overlay_shopping = EphemeralOverlay(
        overlay_id="overlay_4",
        user_id="family_standard",
        scope="trip",
        confidence=0.8,
        source="chat",
        travel=TravelOverlay(
            activity_weights={
                "shopping": 0.9,
                "souvenirs": 0.8
            }
        )
    )
    
    result_with_shopping = PlaceTypes.select_types_for_user(base_pref, destination, travel_style, overlay_shopping)
    
    print(f"❌ WITHOUT overlay: {result_baseline}")
    has_shopping_baseline = any('shop' in t for t in result_baseline)
    print(f"   Has shopping: {'✅' if has_shopping_baseline else '❌ NO'}")
    print()
    print(f"✅ WITH overlay: {result_with_shopping}")
    has_shopping_overlay = any('shop' in t for t in result_with_shopping)
    print(f"   Has shopping: {'✅ YES' if has_shopping_overlay else '❌ NO'}")
    print(f"   Impact: {'✅ SHOPPING ADDED!' if has_shopping_overlay and not has_shopping_baseline else '✅ Shopping maintained' if has_shopping_overlay else '⚠️  No shopping'}")
    print()
    
    # ==========================================================================
    # SCENARIO 5: Complex - "Want beaches, avoid crowded places, no fast food"
    # ==========================================================================
    print("=" * 80)
    print("SCENARIO 5: Complex multi-constraint overlay")
    print("=" * 80)
    print()
    print("💬 User said: 'Want beaches, avoid crowded tourist spots, no fast food'")
    print()
    
    overlay_complex = EphemeralOverlay(
        overlay_id="overlay_5",
        user_id="family_standard",
        scope="day",
        confidence=0.85,
        source="chat",
        travel=TravelOverlay(
            activity_weights={
                "beach": 0.9,
                "coastal": 0.7
            },
            avoids={
                "tourist_trap": 0.8,
                "crowds": 0.7
            }
        ),
        food=FoodOverlay(
            hard_excludes_place_types=["fast_food_restaurant", "fast_food"],
            must_include_keywords=["quality", "local"]
        )
    )
    
    result_with_complex = PlaceTypes.select_types_for_user(base_pref, destination, travel_style, overlay_complex)
    
    print(f"✅ WITH complex overlay: {result_with_complex}")
    has_beach = any('beach' in t for t in result_with_complex)
    no_fast_food = not any('fast_food' in t for t in result_with_complex)
    print(f"   Has beach: {'✅ YES' if has_beach else '⚠️  NO (may not exist in destination)'}")
    print(f"   No fast food: {'✅ EXCLUDED' if no_fast_food else '❌ STILL THERE'}")
    print()
    
    # ==========================================================================
    # SCENARIO 6: Overlay OVERPOWERS base preference on same activity
    # ==========================================================================
    print("=" * 80)
    print("SCENARIO 6: Overlay overpowers base weight on same activity")
    print("=" * 80)
    print()
    print("💬 User said: 'Actually, I REALLY want to focus on museums today'")
    print("📋 Base has: museums:0.8, parks:0.7, aquariums:0.6")
    print("📋 Overlay has: museums:0.3 (3x weight → 0.9 effective)")
    print()
    
    overlay_museums_boost = EphemeralOverlay(
        overlay_id="overlay_6a",
        user_id="family_standard",
        scope="day",
        confidence=0.9,
        source="chat",
        travel=TravelOverlay(
            activity_weights={
                "museum": 0.3,  # Will be 3x → 0.9 effective weight
                "art_gallery": 0.3,  # Related activity
                # parks is NOT mentioned → base weight stays 0.7
            }
        )
    )
    
    result_with_museum_boost = PlaceTypes.select_types_for_user(base_pref, destination, travel_style, overlay_museums_boost)
    
    print(f"❌ WITHOUT overlay: {result_baseline}")
    print()
    print(f"✅ WITH overlay (museums boosted): {result_with_museum_boost}")
    has_more_museums = 'museum' in result_with_museum_boost or 'art_gallery' in result_with_museum_boost
    print(f"   Museums prioritized: {'✅ YES' if has_more_museums else '❌ NO'}")
    print(f"   Impact: {'✅ OVERLAY OVERPOWERED BASE!' if has_more_museums else '⚠️  Not strong enough'}")
    print()
    
    # ==========================================================================
    # SCENARIO 7: Override travel style - "Just bars and nightlife tonight"
    # ==========================================================================
    print("=" * 80)
    print("SCENARIO 7: Override family style with nightlife")
    print("=" * 80)
    print()
    print("💬 User said: 'Parents' night out - just bars and nightlife please'")
    print("📋 This CONTRADICTS family style which normally avoids bars")
    print()
    
    overlay_nightlife = EphemeralOverlay(
        overlay_id="overlay_7",
        user_id="family_standard",
        scope="day",
        confidence=0.9,
        source="chat",
        strict_mode=True,  # Force override of style guidance!
        travel=TravelOverlay(
            activity_weights={
                "bar": 0.9,         # Use exact place type name
                "night_club": 0.9,
                "live_music": 0.7
            }
        )
    )
    
    result_with_nightlife = PlaceTypes.select_types_for_user(base_pref, destination, travel_style, overlay_nightlife)
    
    print(f"❌ WITHOUT overlay: {result_baseline}")
    print(f"   Has bar: {'✅' if 'bar' in result_baseline else '❌ NO (family style avoids)'}")
    print()
    print(f"✅ WITH overlay: {result_with_nightlife}")
    has_bar = 'bar' in result_with_nightlife or 'night_club' in result_with_nightlife
    print(f"   Has bar/nightlife: {'✅ OVERRIDE WORKED!' if has_bar else '⚠️  Style guidance still blocking'}")
    print()
    
    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("=" * 80)
    print("📊 OVERLAY EFFECTIVENESS SUMMARY")
    print("=" * 80)
    print()
    
    test_results = [
        {
            "scenario": "Must include temples/worship places",
            "success": any(t in result_with_temples for t in ['place_of_worship', 'hindu_temple', 'church']) and not any(t in result_baseline for t in ['place_of_worship', 'hindu_temple', 'church']),
            "before": result_baseline,
            "after": result_with_temples
        },
        {
            "scenario": "Avoid zoos",
            "success": 'zoo' not in result_with_no_zoo,
            "before": result_baseline,
            "after": result_with_no_zoo
        },
        {
            "scenario": "Exclude steakhouse/BBQ (vegetarian)",
            "success": not any(t in result_with_veg for t in ["steakhouse", "bbq_restaurant"]),
            "before": result_baseline,
            "after": result_with_veg
        },
        {
            "scenario": "Must include shopping",
            "success": any('shop' in t for t in result_with_shopping),
            "before": result_baseline,
            "after": result_with_shopping
        },
        {
            "scenario": "Complex: beach + no fast food",
            "success": not any('fast_food' in t for t in result_with_complex),
            "before": result_baseline,
            "after": result_with_complex
        },
        {
            "scenario": "Overlay overpowers base (museums)",
            "success": 'museum' in result_with_museum_boost or 'art_gallery' in result_with_museum_boost,
            "before": result_baseline,
            "after": result_with_museum_boost
        },
        {
            "scenario": "Override family style with nightlife",
            "success": 'bar' in result_with_nightlife or 'night_club' in result_with_nightlife,
            "before": result_baseline,
            "after": result_with_nightlife
        }
    ]
    
    passed = sum(1 for r in test_results if r["success"])
    total = len(test_results)
    
    print(f"✅ Overlay Tests Passed: {passed}/{total} ({passed/total*100:.0f}%)")
    print()
    
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{i}. {result['scenario']}: {status}")
    
    print()
    print("=" * 80)
    print("🔍 Detailed Comparison")
    print("=" * 80)
    print()
    
    for i, result in enumerate(test_results, 1):
        print(f"{i}. {result['scenario']}:")
        print(f"   Before: {result['before']}")
        print(f"   After:  {result['after']}")
        
        # Find what changed
        before_set = set(result['before'])
        after_set = set(result['after'])
        added = after_set - before_set
        removed = before_set - after_set
        
        if added:
            print(f"   ➕ Added: {', '.join(added)}")
        if removed:
            print(f"   ➖ Removed: {', '.join(removed)}")
        if not added and not removed:
            print(f"   ↔️  Same (overlay may have reinforced existing types)")
        print()
    
    print("=" * 80)
    print("💡 Recommendations")
    print("=" * 80)
    print()
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("   Overlay system is working perfectly!")
    elif passed >= total * 0.8:
        print("✅ MOSTLY WORKING (80%+ pass rate)")
        print("   Review failed scenarios for improvements")
    else:
        print("⚠️  NEEDS ATTENTION (< 80% pass rate)")
        print("   Overlay weight multiplier may need adjustment")
    
    print()
    print("Key Findings:")
    print(f"  • Overlay weight multiplier: 3.0x")
    print(f"  • Weights normalized to 0-1 scale")
    print(f"  • Hard exclusions post-processed")
    print(f"  • Success rate: {passed}/{total}")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_overlay_scenarios()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

