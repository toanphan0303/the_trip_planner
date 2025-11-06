#!/usr/bin/env python3
"""
Test select_types_for_user with different TravelStyle preferences
Creates mock UserPreference objects for various travel styles and tests place type selection
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'server', '.env'))

from user_profile.models import (
    UserPreference,
    TravelPreference,
    FoodPreference,
    TravelStyle,
    PreferenceStyle
)
from constant.place_types import PlaceTypes

# Import TravelStyleEnum (might be an alias for TravelStyle)
try:
    from user_profile.models import TravelStyleEnum
except ImportError:
    # Use TravelStyle if TravelStyleEnum doesn't exist
    TravelStyleEnum = TravelStyle


def create_solo_adventure_preference() -> UserPreference:
    """Create mock UserPreference for solo adventure traveler"""
    # Create with minimal init to avoid DEFAULT checks
    return UserPreference.model_construct(
        user_id="test_solo_adventure",
        version="1.0.0",
        travel={
            TravelStyle.SOLO.value: TravelPreference(
                travel_style_weights={
                    "adventure": 0.9,
                    "outdoor": 0.8,
                    "active": 0.9
                },
                activity_weights={
                    "hiking": 0.9,
                    "outdoor_activities": 0.8,
                    "scenic_views": 0.7,
                    "museums": 0.4,
                    "nightlife": 0.6
                },
                transport_weights={
                    "walking": 0.8,
                    "public_transport": 0.7,
                    "rental_car": 0.5
                },
                budget_score=0.4  # Moderate budget
            )
        },
        food={
            TravelStyle.SOLO.value: FoodPreference(
                cuisine_weights={
                    "local": 0.9,
                    "street_food": 0.8
                },
                food_type_weights={
                    "casual": 0.7,
                    "quick": 0.6
                },
                budget_weight=0.4
            )
        },
        stay={}
    )


def create_family_with_kids_preference() -> UserPreference:
    """Create mock UserPreference for family with young children"""
    return UserPreference.model_construct(
        user_id="test_family_kids",
        version="1.0.0",
        travel={
            TravelStyle.FAMILY.value: TravelPreference(
                travel_style_weights={
                    "family_friendly": 0.9,
                    "educational": 0.7,
                    "relaxation": 0.6
                },
                activity_weights={
                    "parks": 0.9,
                    "aquariums": 0.8,
                    "zoos": 0.8,
                    "museums": 0.6,
                    "beaches": 0.7,
                    "amusement_parks": 0.9
                },
                transport_weights={
                    "rental_car": 0.7,
                    "public_transport": 0.5
                },
                budget_score=0.5  # Moderate budget
            )
        },
        food={
            TravelStyle.FAMILY.value: FoodPreference(
                cuisine_weights={
                    "kid_friendly": 0.9,
                    "familiar": 0.7
                },
                food_type_weights={
                    "family_restaurant": 0.9,
                    "casual": 0.8
                },
                dietary_restrictions=["peanut_allergy", "vegetarian_options_needed"],
                budget_weight=0.5
            )
        },
        stay={}
    )


def create_couple_romantic_preference() -> UserPreference:
    """Create mock UserPreference for romantic couple travel"""
    return UserPreference.model_construct(
        user_id="test_couple_romantic",
        travel={
            TravelStyle.COUPLE.value: TravelPreference(
                travel_style_weights={
                    "romantic": 0.9,
                    "cultural": 0.7,
                    "relaxation": 0.8
                },
                activity_weights={
                    "scenic_views": 0.9,
                    "fine_dining": 0.8,
                    "cultural_sites": 0.7,
                    "spas": 0.6,
                    "gardens": 0.7,
                    "romantic_spots": 0.9
                },
                transport_weights={
                    "walking": 0.8,
                    "private_car": 0.6
                },
                budget_score=0.7  # Higher budget
            )
        },
        food={
            TravelStyle.COUPLE.value: FoodPreference(
                cuisine_weights={
                    "fine_dining": 0.8,
                    "local": 0.7,
                    "fusion": 0.6
                },
                food_type_weights={
                    "romantic_ambiance": 0.9,
                    "upscale": 0.7
                },
                alcohol_weight=0.8,
                budget_weight=0.7
            )
        },
        stay={}
    )


def create_cultural_explorer_preference() -> UserPreference:
    """Create mock UserPreference for cultural enthusiast"""
    return UserPreference.model_construct(
        user_id="test_cultural_explorer",
        travel={
            TravelStyle.CULTURAL.value: TravelPreference(
                travel_style_weights={
                    "cultural": 0.9,
                    "educational": 0.8,
                    "historical": 0.9
                },
                activity_weights={
                    "museums": 0.9,
                    "historical_sites": 0.9,
                    "art_galleries": 0.8,
                    "temples": 0.8,
                    "cultural_shows": 0.7,
                    "local_markets": 0.7
                },
                transport_weights={
                    "walking": 0.7,
                    "public_transport": 0.8
                },
                budget_score=0.6  # Moderate to high budget
            )
        },
        food={
            TravelStyle.CULTURAL.value: FoodPreference(
                cuisine_weights={
                    "local": 0.9,
                    "traditional": 0.9,
                    "authentic": 0.8
                },
                food_type_weights={
                    "local_experience": 0.9
                },
                budget_weight=0.6
            )
        },
        stay={}
    )


def create_luxury_relaxation_preference() -> UserPreference:
    """Create mock UserPreference for luxury relaxation traveler"""
    return UserPreference.model_construct(
        user_id="test_luxury_relaxation",
        travel={
            TravelStyle.LUXURY.value: TravelPreference(
                travel_style_weights={
                    "luxury": 0.9,
                    "relaxation": 0.9,
                    "comfort": 0.9
                },
                activity_weights={
                    "spas": 0.9,
                    "fine_dining": 0.8,
                    "shopping": 0.7,
                    "scenic_views": 0.8,
                    "beaches": 0.7
                },
                transport_weights={
                    "private_car": 0.9,
                    "taxi": 0.8
                },
                budget_score=0.9  # High budget
            )
        },
        food={
            TravelStyle.LUXURY.value: FoodPreference(
                cuisine_weights={
                    "fine_dining": 0.9,
                    "gourmet": 0.9
                },
                food_type_weights={
                    "upscale": 0.9,
                    "michelin": 0.8
                },
                alcohol_weight=0.9,
                budget_weight=0.9
            )
        },
        stay={}
    )


def create_backpacker_budget_preference() -> UserPreference:
    """Create mock UserPreference for budget backpacker"""
    return UserPreference.model_construct(
        user_id="test_backpacker",
        travel={
            TravelStyle.BACKPACKING.value: TravelPreference(
                travel_style_weights={
                    "backpacking": 0.9,
                    "adventure": 0.7,
                    "social": 0.8
                },
                activity_weights={
                    "free_activities": 0.9,
                    "parks": 0.8,
                    "walking_tours": 0.8,
                    "local_markets": 0.7,
                    "street_food": 0.9
                },
                transport_weights={
                    "walking": 0.9,
                    "public_transport": 0.8,
                    "hitchhiking": 0.3
                },
                budget_score=0.1  # Very low budget
            )
        },
        food={
            TravelStyle.BACKPACKING.value: FoodPreference(
                cuisine_weights={
                    "street_food": 0.9,
                    "local": 0.8
                },
                food_type_weights={
                    "cheap_eats": 0.9,
                    "markets": 0.8
                },
                budget_weight=0.1
            )
        },
        stay={}
    )


def create_foodie_traveler_preference() -> UserPreference:
    """Food-focused traveler who plans trips around cuisine"""
    return UserPreference.model_construct(
        user_id="test_foodie",
        version="1.0.0",
        travel={
            TravelStyle.SOLO.value: TravelPreference(
                travel_style_weights={
                    "culinary": 0.9,
                    "cultural": 0.6
                },
                activity_weights={
                    "food_tours": 0.9,
                    "markets": 0.8,
                    "cooking_classes": 0.7,
                    "local_restaurants": 0.9
                },
                budget_score=0.6
            )
        },
        food={
            TravelStyle.SOLO.value: FoodPreference(
                cuisine_weights={
                    "local": 0.9,
                    "street_food": 0.8,
                    "fine_dining": 0.7,
                    "authentic": 0.9
                },
                food_type_weights={
                    "michelin": 0.6,
                    "local_specialties": 0.9
                },
                alcohol_weight=0.7,
                budget_weight=0.6
            )
        },
        stay={}
    )


def create_wellness_retreat_preference() -> UserPreference:
    """Wellness-focused traveler seeking health and relaxation"""
    return UserPreference.model_construct(
        user_id="test_wellness",
        version="1.0.0",
        travel={
            TravelStyle.RELAXATION.value: TravelPreference(
                travel_style_weights={
                    "wellness": 0.9,
                    "relaxation": 0.9,
                    "mindfulness": 0.8
                },
                activity_weights={
                    "spa": 0.9,
                    "yoga": 0.8,
                    "meditation": 0.7,
                    "nature": 0.8,
                    "hiking": 0.6
                },
                budget_score=0.7
            )
        },
        food={
            TravelStyle.RELAXATION.value: FoodPreference(
                cuisine_weights={
                    "healthy": 0.9,
                    "organic": 0.8,
                    "vegetarian": 0.7
                },
                food_type_weights={
                    "health_food": 0.9,
                    "juice_bar": 0.7
                },
                budget_weight=0.7
            )
        },
        stay={}
    )


def create_nightlife_enthusiast_preference() -> UserPreference:
    """Young traveler focused on nightlife and social experiences"""
    return UserPreference.model_construct(
        user_id="test_nightlife",
        version="1.0.0",
        travel={
            TravelStyle.SOLO.value: TravelPreference(
                travel_style_weights={
                    "nightlife": 0.9,
                    "social": 0.8,
                    "entertainment": 0.8
                },
                activity_weights={
                    "bars": 0.9,
                    "night_clubs": 0.8,
                    "live_music": 0.8,
                    "rooftop_bars": 0.7,
                    "dancing": 0.7
                },
                budget_score=0.5
            )
        },
        food={
            TravelStyle.SOLO.value: FoodPreference(
                cuisine_weights={
                    "late_night": 0.8,
                    "local": 0.6
                },
                food_type_weights={
                    "casual": 0.7
                },
                alcohol_weight=0.9,
                budget_weight=0.5
            )
        },
        stay={}
    )


def create_nature_photographer_preference() -> UserPreference:
    """Photographer seeking scenic natural locations"""
    return UserPreference.model_construct(
        user_id="test_photographer",
        version="1.0.0",
        travel={
            TravelStyle.SOLO.value: TravelPreference(
                travel_style_weights={
                    "photography": 0.9,
                    "nature": 0.9,
                    "adventure": 0.6
                },
                activity_weights={
                    "scenic_views": 0.9,
                    "hiking": 0.8,
                    "national_parks": 0.9,
                    "sunrise_spots": 0.8,
                    "viewpoints": 0.9,
                    "beaches": 0.7
                },
                budget_score=0.4
            )
        },
        food={
            TravelStyle.SOLO.value: FoodPreference(
                cuisine_weights={
                    "quick": 0.7,
                    "local": 0.6
                },
                food_type_weights={
                    "takeaway": 0.7,
                    "cafe": 0.6
                },
                budget_weight=0.3
            )
        },
        stay={}
    )


def create_shopping_enthusiast_preference() -> UserPreference:
    """Traveler who loves shopping and fashion"""
    return UserPreference.model_construct(
        user_id="test_shopper",
        version="1.0.0",
        travel={
            TravelStyle.SOLO.value: TravelPreference(
                travel_style_weights={
                    "shopping": 0.9,
                    "fashion": 0.8,
                    "urban": 0.7
                },
                activity_weights={
                    "shopping_malls": 0.9,
                    "boutiques": 0.8,
                    "markets": 0.7,
                    "fashion_districts": 0.9,
                    "outlets": 0.6
                },
                budget_score=0.6
            )
        },
        food={
            TravelStyle.SOLO.value: FoodPreference(
                cuisine_weights={
                    "trendy": 0.8,
                    "instagram_worthy": 0.7
                },
                food_type_weights={
                    "cafe": 0.8,
                    "brunch": 0.7
                },
                budget_weight=0.6
            )
        },
        stay={}
    )


def create_business_traveler_preference() -> UserPreference:
    """Business traveler with limited time"""
    return UserPreference.model_construct(
        user_id="test_business",
        version="1.0.0",
        travel={
            TravelStyle.BUSINESS.value: TravelPreference(
                travel_style_weights={
                    "efficiency": 0.9,
                    "business": 0.9,
                    "convenience": 0.8
                },
                activity_weights={
                    "business_district": 0.8,
                    "cafes": 0.7,
                    "gyms": 0.5,
                    "quick_attractions": 0.4
                },
                budget_score=0.7
            )
        },
        food={
            TravelStyle.BUSINESS.value: FoodPreference(
                cuisine_weights={
                    "business_lunch": 0.8,
                    "local": 0.6
                },
                food_type_weights={
                    "quick": 0.7,
                    "upscale": 0.6
                },
                budget_weight=0.7
            )
        },
        stay={}
    )


def create_history_buff_preference() -> UserPreference:
    """History enthusiast focused on historical sites"""
    return UserPreference.model_construct(
        user_id="test_history",
        version="1.0.0",
        travel={
            TravelStyle.CULTURAL.value: TravelPreference(
                travel_style_weights={
                    "historical": 0.9,
                    "educational": 0.8,
                    "cultural": 0.8
                },
                activity_weights={
                    "historical_landmarks": 0.9,
                    "castles": 0.8,
                    "monuments": 0.8,
                    "archaeological_sites": 0.7,
                    "heritage_sites": 0.9
                },
                budget_score=0.5
            )
        },
        food={
            TravelStyle.CULTURAL.value: FoodPreference(
                cuisine_weights={
                    "traditional": 0.9,
                    "historical": 0.7
                },
                food_type_weights={
                    "authentic": 0.8
                },
                budget_weight=0.5
            )
        },
        stay={}
    )


def create_sports_fan_preference() -> UserPreference:
    """Sports enthusiast seeking games and sporting events"""
    return UserPreference.model_construct(
        user_id="test_sports",
        version="1.0.0",
        travel={
            TravelStyle.GROUP.value: TravelPreference(
                travel_style_weights={
                    "sports": 0.9,
                    "entertainment": 0.7,
                    "social": 0.7
                },
                activity_weights={
                    "stadiums": 0.9,
                    "sports_bars": 0.8,
                    "sporting_events": 0.9,
                    "fan_zones": 0.7
                },
                budget_score=0.5
            )
        },
        food={
            TravelStyle.GROUP.value: FoodPreference(
                cuisine_weights={
                    "casual": 0.8,
                    "local": 0.6
                },
                food_type_weights={
                    "sports_bar": 0.8,
                    "pub": 0.7
                },
                alcohol_weight=0.8,
                budget_weight=0.5
            )
        },
        stay={}
    )


def test_select_types_for_user():
    """Test select_types_for_user with different travel style preferences"""
    
    print("=" * 80)
    print("🧪 Comprehensive Testing: select_types_for_user()")
    print("=" * 80)
    print()
    
    # Test destinations
    destinations = ["Tokyo", "Paris", "New York"]
    
    # Expanded test cases with diverse travel styles
    test_cases = [
        {
            "name": "Solo Adventure Traveler",
            "preference": create_solo_adventure_preference(),
            "travel_style": TravelStyle.SOLO,
            "description": "Young adventurous traveler seeking outdoor activities and local experiences",
            "expected_types": ["park", "hiking_area", "scenic_view", "outdoor"]
        },
        {
            "name": "Family with Young Kids",
            "preference": create_family_with_kids_preference(),
            "travel_style": TravelStyle.FAMILY,
            "description": "Parents with 2 young children (ages 5 and 8) looking for kid-friendly activities",
            "expected_types": ["park", "aquarium", "zoo", "amusement_park", "ice_cream_shop"]
        },
        {
            "name": "Romantic Couple",
            "preference": create_couple_romantic_preference(),
            "travel_style": TravelStyle.COUPLE,
            "description": "Couple celebrating anniversary, looking for romantic experiences",
            "expected_types": ["scenic_view", "museum", "park", "cafe"]
        },
        {
            "name": "Cultural Explorer",
            "preference": create_cultural_explorer_preference(),
            "travel_style": TravelStyle.CULTURAL,
            "description": "History buff and art lover seeking deep cultural immersion",
            "expected_types": ["museum", "art_gallery", "historical_landmark", "cultural"]
        },
        {
            "name": "Luxury Relaxation",
            "preference": create_luxury_relaxation_preference(),
            "travel_style": TravelStyle.LUXURY,
            "description": "High-end traveler seeking relaxation and pampering",
            "expected_types": ["spa", "fine_dining", "scenic_view"]
        },
        {
            "name": "Budget Backpacker",
            "preference": create_backpacker_budget_preference(),
            "travel_style": TravelStyle.BACKPACKING,
            "description": "Budget-conscious traveler seeking authentic local experiences",
            "expected_types": ["market", "park", "free", "cheap"]
        },
        {
            "name": "Foodie Traveler",
            "preference": create_foodie_traveler_preference(),
            "travel_style": TravelStyle.SOLO,
            "description": "Food-focused traveler who plans trips around cuisine",
            "expected_types": ["restaurant", "market", "food", "cafe"]
        },
        {
            "name": "Wellness Retreat Seeker",
            "preference": create_wellness_retreat_preference(),
            "travel_style": TravelStyle.RELAXATION,
            "description": "Wellness-focused traveler seeking health and relaxation",
            "expected_types": ["spa", "yoga", "park", "nature"]
        },
        {
            "name": "Nightlife Enthusiast",
            "preference": create_nightlife_enthusiast_preference(),
            "travel_style": TravelStyle.SOLO,
            "description": "Young traveler focused on nightlife and social experiences",
            "expected_types": ["bar", "night_club", "live_music"]
        },
        {
            "name": "Nature Photographer",
            "preference": create_nature_photographer_preference(),
            "travel_style": TravelStyle.SOLO,
            "description": "Photographer seeking scenic natural locations",
            "expected_types": ["scenic_view", "park", "hiking_area", "viewpoint"]
        },
        {
            "name": "Shopping Enthusiast",
            "preference": create_shopping_enthusiast_preference(),
            "travel_style": TravelStyle.SOLO,
            "description": "Traveler who loves shopping and fashion",
            "expected_types": ["shopping_mall", "market", "boutique"]
        },
        {
            "name": "Business Traveler",
            "preference": create_business_traveler_preference(),
            "travel_style": TravelStyle.BUSINESS,
            "description": "Business traveler with limited free time",
            "expected_types": ["cafe", "restaurant", "gym"]
        },
        {
            "name": "History Buff",
            "preference": create_history_buff_preference(),
            "travel_style": TravelStyle.CULTURAL,
            "description": "History enthusiast focused on historical sites",
            "expected_types": ["historical_landmark", "monument", "castle", "archaeological"]
        },
        {
            "name": "Sports Fan",
            "preference": create_sports_fan_preference(),
            "travel_style": TravelStyle.GROUP,
            "description": "Sports enthusiast seeking games and sporting events",
            "expected_types": ["stadium", "sports_bar", "sporting"]
        }
    ]
    
    # Run tests for each case
    results_by_case = {}
    
    for test_case in test_cases:
        print("=" * 80)
        print(f"📋 Test Case: {test_case['name']}")
        print("=" * 80)
        print(f"📝 Description: {test_case['description']}")
        print(f"🎯 Travel Style: {test_case['travel_style'].value}")
        print(f"📍 Expected types: {', '.join(test_case.get('expected_types', []))}")
        print()
        
        case_results = {}
        
        for destination in destinations:
            print(f"🌍 Destination: {destination}")
            print("-" * 80)
            
            try:
                # Call select_types_for_user
                selected_types = PlaceTypes.select_types_for_user(
                    user_preference=test_case['preference'],
                    destination=destination,
                    travel_style=test_case['travel_style'],
                    model="gemini-flash"
                )
                
                case_results[destination] = selected_types
                
                print(f"✅ Selected {len(selected_types)} place types:")
                for i, place_type in enumerate(selected_types, 1):
                    print(f"   {i}. {place_type}")
                
                # Check if expected types are present
                expected = test_case.get('expected_types', [])
                if expected:
                    matched = sum(1 for exp in expected if any(exp in t for t in selected_types))
                    match_rate = (matched / len(expected)) * 100
                    print(f"   📊 Match rate: {matched}/{len(expected)} expected keywords ({match_rate:.0f}%)")
                
                # Validate food type included
                food_types = {"restaurant", "cafe", "bakery", "bar", "food_court", "ice_cream_shop"}
                has_food = any(t in food_types for t in selected_types)
                print(f"   {'✅' if has_food else '❌'} Food type included: {has_food}")
                
                # Validate count
                count_ok = 4 <= len(selected_types) <= 7
                print(f"   {'✅' if count_ok else '⚠️ '} Type count (4-7): {count_ok}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                case_results[destination] = []
                import traceback
                traceback.print_exc()
            
            print()
        
        results_by_case[test_case['name']] = case_results
        print()
    
    # Summary analysis
    print("=" * 80)
    print("📊 COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print()
    
    # Analyze consistency across destinations
    print("🔍 Consistency Analysis:")
    print("-" * 80)
    for case_name, case_destinations in results_by_case.items():
        if len(case_destinations) >= 2:
            dest_lists = list(case_destinations.values())
            # Count common types across all destinations
            if dest_lists:
                all_types_in_case = set()
                for types_list in dest_lists:
                    all_types_in_case.update(types_list)
                
                common_count = len([t for t in all_types_in_case if all(t in dest_list for dest_list in dest_lists)])
                print(f"{case_name}:")
                print(f"   Common across all destinations: {common_count} types")
                print(f"   Shows {'✅ consistent' if common_count >= 3 else '⚠️  highly variable'} pattern")
                print()
    
    print("=" * 80)
    print("✅ Comprehensive Test Complete!")
    print("=" * 80)
    print()
    print(f"📈 Total Test Cases: {len(test_cases)}")
    print(f"📍 Destinations Tested: {len(destinations)}")
    print(f"🔢 Total Scenarios: {len(test_cases) * len(destinations)}")
    print()
    
    print("=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)
    print()
    print("💡 Analysis Tips:")
    print("   • Compare how place types differ by travel style")
    print("   • Check if destination knowledge influences selection")
    print("   • Verify food types are included for each style")
    print("   • Ensure 4-7 types returned as expected")
    print()


if __name__ == "__main__":
    try:
        test_select_types_for_user()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

