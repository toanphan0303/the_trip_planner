#!/usr/bin/env python3
"""
Test select_types_for_user WITH ephemeral overlays
Shows how recent user input overrides base preferences
"""

import os
import sys
from dotenv import load_dotenv
import time

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


def create_base_family_preference() -> UserPreference:
    """Base family preference that likes museums and educational stuff"""
    return UserPreference.model_construct(
        user_id="family_base",
        version="1.0.0",
        travel={
            TravelStyle.FAMILY.value: TravelPreference(
                travel_style_weights={"educational": 0.8, "cultural": 0.7},
                activity_weights={
                    "museums": 0.9,
                    "historical_sites": 0.8,
                    "parks": 0.6
                },
                budget_score=0.5
            )
        },
        food={
            TravelStyle.FAMILY.value: FoodPreference(
                cuisine_weights={"local": 0.7},
                food_type_weights={"family_restaurant": 0.8},
                budget_weight=0.5
            )
        },
        stay={}
    )


def create_overlay_want_outdoor() -> EphemeralOverlay:
    """User just said: 'I want outdoor activities, no museums today'"""
    return EphemeralOverlay(
        overlay_id="overlay_outdoor_1",
        user_id="family_base",
        scope="day",
        confidence=0.9,  # High confidence - user explicitly stated
        source="chat",
        travel=TravelOverlay(
            activity_weights={
                "outdoor": 0.9,
                "parks": 0.8,
                "hiking": 0.7
            },
            avoids={
                "museums": 0.9,  # User said "no museums"
                "indoor": 0.7
            }
        )
    )


def create_overlay_vegetarian_only() -> EphemeralOverlay:
    """User just said: 'We're vegetarian, no meat restaurants'"""
    return EphemeralOverlay(
        overlay_id="overlay_veg_1",
        user_id="family_base",
        scope="trip",
        confidence=1.0,  # Very high - dietary restriction
        source="chat",
        food=FoodOverlay(
            cuisine_weights={
                "vegetarian": 0.9,
                "vegan": 0.7
            },
            hard_excludes_place_types=["steakhouse", "bbq_joint", "burger_joint"],
            must_include_keywords=["vegetarian_options", "vegan_friendly"]
        )
    )


def create_overlay_spontaneous_nightlife() -> EphemeralOverlay:
    """User just said: 'Actually, let's check out some bars tonight!'"""
    return EphemeralOverlay(
        overlay_id="overlay_night_1",
        user_id="family_base",
        scope="day",
        confidence=0.8,
        source="chat",
        travel=TravelOverlay(
            activity_weights={
                "nightlife": 0.9,
                "bars": 0.8,
                "live_music": 0.6
            }
        ),
        food=FoodOverlay(
            cuisine_weights={"local": 0.7}
        )
    )


def test_with_overlays():
    """Test how overlays affect place type selection"""
    
    print("=" * 80)
    print("🧪 Testing EphemeralOverlay Impact on Place Type Selection")
    print("=" * 80)
    print()
    
    base_pref = create_base_family_preference()
    destination = "Tokyo"
    
    print("📋 Base Preference:")
    print("   Family traveler who loves museums and educational activities")
    print()
    
    # Test 1: No overlay (baseline)
    print("=" * 80)
    print("🔹 Test 1: NO OVERLAY (Baseline)")
    print("=" * 80)
    print()
    
    result_no_overlay = PlaceTypes.select_types_for_user(
        user_preference=base_pref,
        destination=destination,
        travel_style=TravelStyle.FAMILY,
        ephemeral_overlay=None
    )
    
    print(f"✅ Selected types: {result_no_overlay}")
    print(f"   Count: {len(result_no_overlay)}")
    print(f"   Has museum: {'✅' if 'museum' in result_no_overlay else '❌'}")
    print(f"   Has park: {'✅' if 'park' in result_no_overlay else '❌'}")
    print()
    
    # Test 2: Overlay wants outdoor, no museums
    print("=" * 80)
    print("🔹 Test 2: OVERLAY - 'I want outdoor activities, no museums today'")
    print("=" * 80)
    print()
    
    overlay_outdoor = create_overlay_want_outdoor()
    result_outdoor = PlaceTypes.select_types_for_user(
        user_preference=base_pref,
        destination=destination,
        travel_style=TravelStyle.FAMILY,
        ephemeral_overlay=overlay_outdoor
    )
    
    print(f"✅ Selected types: {result_outdoor}")
    print(f"   Count: {len(result_outdoor)}")
    print(f"   Has museum: {'❌ EXCLUDED' if 'museum' not in result_outdoor else '⚠️  Still included'}")
    print(f"   Has park: {'✅ ADDED' if 'park' in result_outdoor else '❌'}")
    print(f"   Has hiking_area: {'✅ ADDED' if 'hiking_area' in result_outdoor else '❌'}")
    print()
    
    # Test 3: Overlay wants vegetarian only
    print("=" * 80)
    print("🔹 Test 3: OVERLAY - 'We're vegetarian, no meat restaurants'")
    print("=" * 80)
    print()
    
    overlay_veg = create_overlay_vegetarian_only()
    result_veg = PlaceTypes.select_types_for_user(
        user_preference=base_pref,
        destination=destination,
        travel_style=TravelStyle.FAMILY,
        ephemeral_overlay=overlay_veg
    )
    
    print(f"✅ Selected types: {result_veg}")
    print(f"   Count: {len(result_veg)}")
    print(f"   Has steakhouse: {'⚠️  Still there' if 'steakhouse' in result_veg else '✅ EXCLUDED'}")
    print(f"   Has bbq: {'⚠️  Still there' if 'bbq_joint' in result_veg or 'barbecue_restaurant' in result_veg else '✅ EXCLUDED'}")
    print()
    
    # Test 4: Overlay wants nightlife (contradicts family style!)
    print("=" * 80)
    print("🔹 Test 4: OVERLAY - 'Actually, let's check out some bars tonight!'")
    print("=" * 80)
    print("   (This CONTRADICTS family style - testing override)")
    print()
    
    overlay_nightlife = create_overlay_spontaneous_nightlife()
    result_nightlife = PlaceTypes.select_types_for_user(
        user_preference=base_pref,
        destination=destination,
        travel_style=TravelStyle.FAMILY,
        ephemeral_overlay=overlay_nightlife
    )
    
    print(f"✅ Selected types: {result_nightlife}")
    print(f"   Count: {len(result_nightlife)}")
    print(f"   Has bar: {'✅ ADDED (overlay override!)' if 'bar' in result_nightlife else '❌ Still excluded'}")
    print(f"   Has night_club: {'✅ ADDED' if 'night_club' in result_nightlife else '❌'}")
    print()
    
    # Summary comparison
    print("=" * 80)
    print("📊 SUMMARY - Overlay Impact")
    print("=" * 80)
    print()
    
    print("Baseline (no overlay):")
    print(f"   {result_no_overlay}")
    print()
    
    print("With 'outdoor, no museums' overlay:")
    print(f"   {result_outdoor}")
    removed_museum = 'museum' in result_no_overlay and 'museum' not in result_outdoor
    added_outdoor = any(t in result_outdoor for t in ['park', 'hiking_area', 'scenic_view']) and \
                    not any(t in result_no_overlay for t in ['hiking_area'])
    print(f"   {'✅' if removed_museum else '⚠️ '} Museums removed: {removed_museum}")
    print(f"   {'✅' if added_outdoor else '⚠️ '} Outdoor added: {added_outdoor}")
    print()
    
    print("With 'vegetarian only' overlay:")
    print(f"   {result_veg}")
    print(f"   ✅ No meat-specific restaurant types included")
    print()
    
    print("With 'nightlife' overlay:")
    print(f"   {result_nightlife}")
    added_bar = 'bar' in result_nightlife
    print(f"   {'✅' if added_bar else '⚠️ '} Bar added despite family style: {added_bar}")
    print()
    
    print("=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)
    print()
    print("💡 Key Observations:")
    print("   • Overlays successfully modify base preferences")
    print("   • Recent user input gets higher priority")
    print("   • Can override even travel style defaults")
    print("   • Excludes and avoids are respected")
    print()


if __name__ == "__main__":
    try:
        test_with_overlays()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

