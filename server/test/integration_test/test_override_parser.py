"""
Test suite for create_override_from_message
Tests LLM-based preference parsing with various user messages
"""

import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from user_profile.ephemeral.override_parser import create_override_from_message
from user_profile.models import TravelStyle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_result(scenario: str, result):
    """Pretty print test result"""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario}")
    print(f"{'='*80}")
    
    if result is None:
        print("❌ Result: None (parsing failed)")
        return
    
    print(f"✅ Has Override: {result.has_override}")
    print(f"   Confidence: {result.confidence:.2f}")
    
    if result.travel_style:
        print(f"   Travel Style: {result.travel_style}")
    
    if result.food:
        print(f"\n📍 FOOD PREFERENCES:")
        if result.food.weights:
            print(f"   Weights: {result.food.weights}")
        if result.food.budget_weights:
            print(f"   Budget: {result.food.budget_weights}")
    
    if result.stay:
        print(f"\n🏨 STAY PREFERENCES:")
        if result.stay.weights:
            print(f"   Weights: {result.stay.weights}")
        if result.stay.budget_weights:
            print(f"   Budget: {result.stay.budget_weights}")
    
    if result.travel:
        print(f"\n✈️ TRAVEL PREFERENCES:")
        if result.travel.weights:
            print(f"   Weights: {result.travel.weights}")
        if result.travel.budget_weights:
            print(f"   Budget: {result.travel.budget_weights}")


# ============================================================================
# Test Scenarios
# ============================================================================

test_messages = [
    {
        "scenario": "Food: Italian & Vegetarian",
        "user_id": "user_001",
        "message": "I want Italian food and I'm vegetarian",
        "travel_style": TravelStyle.FAMILY
    },
    {
        "scenario": "Food: Avoid Spicy & Seafood",
        "user_id": "user_002",
        "message": "No spicy food please, and I don't like seafood",
        "travel_style": TravelStyle.SOLO
    },
    {
        "scenario": "Activity: Museums & Culture",
        "user_id": "user_003",
        "message": "I love visiting museums and historical sites",
        "travel_style": TravelStyle.COUPLE
    },
    {
        "scenario": "Activity: Avoid Crowds & Nightlife",
        "user_id": "user_004",
        "message": "Please skip nightlife and crowded places, I prefer quiet spots",
        "travel_style": TravelStyle.FAMILY
    },
    {
        "scenario": "Budget: Cheap & Budget-Friendly",
        "user_id": "user_005",
        "message": "I'm on a tight budget, looking for cheap eats and budget-friendly activities",
        "travel_style": TravelStyle.SOLO
    },
    {
        "scenario": "Budget: Luxury & High-End",
        "user_id": "user_006",
        "message": "I want fine dining and luxury experiences, money is not a concern",
        "travel_style": TravelStyle.COUPLE
    },
    {
        "scenario": "Mixed: Food + Activities",
        "user_id": "user_007",
        "message": "I want Japanese cuisine, especially sushi, and I love shopping and temples",
        "travel_style": TravelStyle.FAMILY
    },
    {
        "scenario": "Mixed: Food + Budget + Avoid",
        "user_id": "user_008",
        "message": "I want Mexican food but nothing too expensive, and please avoid touristy places",
        "travel_style": TravelStyle.SOLO
    },
    {
        "scenario": "Stay: Hotel with WiFi",
        "user_id": "user_009",
        "message": "I need a hotel with good WiFi and air conditioning",
        "travel_style": TravelStyle.COUPLE
    },
    {
        "scenario": "Stay: Avoid Hostels, Prefer Hotels",
        "user_id": "user_010",
        "message": "No hostels please, I prefer hotels or Airbnb",
        "travel_style": TravelStyle.FAMILY
    },
    {
        "scenario": "Kid-Friendly Activities",
        "user_id": "user_011",
        "message": "Looking for kid-friendly activities, like parks and interactive museums",
        "travel_style": TravelStyle.FAMILY
    },
    {
        "scenario": "No Preferences (Generic)",
        "user_id": "user_012",
        "message": "What's the weather like in Tokyo?",
        "travel_style": TravelStyle.SOLO
    },
    {
        "scenario": "No Preferences (Question)",
        "user_id": "user_013",
        "message": "Can you help me plan my trip?",
        "travel_style": TravelStyle.COUPLE
    },
    {
        "scenario": "Complex: Multiple Categories",
        "user_id": "user_014",
        "message": "I want vegetarian Italian food, need WiFi in hotel, love art museums but hate crowds, and I'm on a moderate budget",
        "travel_style": TravelStyle.SOLO
    },
    {
        "scenario": "Vegan with Strong Preferences",
        "user_id": "user_015",
        "message": "I'm vegan, absolutely no animal products, and I prefer organic restaurants",
        "travel_style": TravelStyle.COUPLE
    }
]


def run_tests():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("TESTING: create_override_from_message")
    print("="*80)
    
    results = []
    
    for test in test_messages:
        print(f"\n🔍 Testing: {test['scenario']}")
        print(f"   Message: \"{test['message']}\"")
        
        result = create_override_from_message(
            user_id=test["user_id"],
            message=test["message"],
            travel_style=test["travel_style"]
        )
        
        print_result(test["scenario"], result)
        
        results.append({
            "scenario": test["scenario"],
            "has_override": result.has_override if result else False,
            "confidence": result.confidence if result else 0.0
        })
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total = len(results)
    with_overrides = sum(1 for r in results if r["has_override"])
    without_overrides = total - with_overrides
    avg_confidence = sum(r["confidence"] for r in results) / total if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"With Overrides: {with_overrides}")
    print(f"Without Overrides: {without_overrides}")
    print(f"Average Confidence: {avg_confidence:.2f}")
    
    print("\n📊 Results by Scenario:")
    for r in results:
        status = "✅" if r["has_override"] else "❌"
        print(f"{status} {r['scenario']} (confidence: {r['confidence']:.2f})")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    run_tests()

