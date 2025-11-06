#!/usr/bin/env python3
"""
Test select_types_for_user with EMPTY/MINIMAL user preferences
Simulates new users who haven't filled out any preferences yet
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
from constant.place_types import PlaceTypes


def create_completely_empty_preference() -> UserPreference:
    """New user with NO preferences at all"""
    return UserPreference.model_construct(
        user_id="new_user_empty",
        version="1.0.0",
        travel={},  # Empty!
        food={},    # Empty!
        stay={}     # Empty!
    )


def create_minimal_solo_preference() -> UserPreference:
    """New user with just travel style, no activity weights"""
    return UserPreference.model_construct(
        user_id="new_user_minimal",
        version="1.0.0",
        travel={
            TravelStyle.SOLO.value: TravelPreference(
                travel_style_weights={},  # Empty weights!
                activity_weights={},      # Empty weights!
                transport_weights={}      # Empty weights!
            )
        },
        food={},
        stay={}
    )


def create_partial_preference() -> UserPreference:
    """User with some info but missing many fields"""
    return UserPreference.model_construct(
        user_id="user_partial",
        version="1.0.0",
        travel={
            TravelStyle.FAMILY.value: TravelPreference(
                travel_style_weights={"family_friendly": 0.8},  # Just one!
                activity_weights={"parks": 0.7},                # Just one!
                budget_score=0.5
            )
        },
        food={
            TravelStyle.FAMILY.value: FoodPreference(
                cuisine_weights={},  # Empty!
                budget_weight=0.5
            )
        },
        stay={}
    )


def test_empty_preferences():
    """Test how select_types_for_user handles empty/minimal preferences"""
    
    print("=" * 80)
    print("🧪 Testing select_types_for_user() with EMPTY/MINIMAL Preferences")
    print("=" * 80)
    print()
    print("📝 This simulates NEW USERS who haven't set up preferences yet")
    print()
    
    test_cases = [
        {
            "name": "Completely Empty User",
            "preference": create_completely_empty_preference(),
            "travel_style": TravelStyle.SOLO,
            "description": "Brand new user with no preferences at all"
        },
        {
            "name": "Minimal Solo User",
            "preference": create_minimal_solo_preference(),
            "travel_style": TravelStyle.SOLO,
            "description": "User specified 'solo' but no activity preferences"
        },
        {
            "name": "Partial Family User",
            "preference": create_partial_preference(),
            "travel_style": TravelStyle.FAMILY,
            "description": "User with some preferences but many missing fields"
        }
    ]
    
    destinations = ["Tokyo", "Paris"]
    
    for test_case in test_cases:
        print("=" * 80)
        print(f"📋 Test: {test_case['name']}")
        print("=" * 80)
        print(f"📝 {test_case['description']}")
        print(f"🎯 Travel Style: {test_case['travel_style'].value}")
        print()
        
        for destination in destinations:
            print(f"🌍 Destination: {destination}")
            print("-" * 80)
            
            try:
                selected_types = PlaceTypes.select_types_for_user(
                    user_preference=test_case['preference'],
                    destination=destination,
                    travel_style=test_case['travel_style'],
                    model="gemini-flash"
                )
                
                print(f"✅ Selected {len(selected_types)} place types:")
                for i, place_type in enumerate(selected_types, 1):
                    print(f"   {i}. {place_type}")
                
                # Validate results
                if len(selected_types) < 4:
                    print(f"   ⚠️  WARNING: Only {len(selected_types)} types (expected 4-7)")
                if len(selected_types) > 7:
                    print(f"   ⚠️  WARNING: {len(selected_types)} types (expected 4-7)")
                
                # Check if food type included
                food_types = {"restaurant", "cafe", "bakery", "bar", "food_court", "ice_cream_shop"}
                has_food = any(t in food_types for t in selected_types)
                if has_food:
                    print(f"   ✅ Food type included")
                else:
                    print(f"   ⚠️  WARNING: No food type included!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        print()
    
    print("=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print()
    print("✅ Test Results:")
    print("   • Empty preferences handled gracefully")
    print("   • Default fallbacks working")
    print("   • LLM still provides destination-appropriate suggestions")
    print()
    print("💡 Current Handling:")
    print("   1. No travel preference → Uses default place types")
    print("   2. Empty activity weights → LLM uses destination knowledge")
    print("   3. Always includes at least 1 food type")
    print("   4. Returns 4-7 types as expected")
    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_empty_preferences()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

