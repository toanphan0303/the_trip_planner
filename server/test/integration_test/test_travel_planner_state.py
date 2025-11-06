"""
Test travel planner state updates with reducers
Tests that set_travel_style and upsert_preference_override work correctly
"""

import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from user_profile.models import TravelStyle
from user_profile.ephemeral import PreferenceOverride, FoodOverride, StayOverride, TravelOverride
from state import TravelPlannerState, TripState, TripData, merge_preference_overrides, pick_last, merge_trip_data, merge_trip_state


def test_set_travel_style():
    """Test that set_travel_style updates current_travel_style"""
    print("\n=== Testing set_travel_style ===")
    
    from tools.travel_planner_tools import set_travel_style
    
    # Initial state
    state = {"messages": [], "current_travel_style": None}
    
    # Call tool function directly (it's wrapped by @tool decorator)
    result = set_travel_style.func(state, travel_style="family")
    
    print(f"Tool returned: {result}")
    
    # Apply reducer
    new_style = pick_last(state.get("current_travel_style"), result.get("current_travel_style"))
    
    print(f"After reducer: current_travel_style = {new_style}")
    assert new_style == TravelStyle.FAMILY, f"Expected FAMILY, got {new_style}"
    print("✅ set_travel_style works correctly")


def test_upsert_preference_override_new():
    """Test creating a new preference override using direct PreferenceOverride"""
    print("\n=== Testing preference creation (simulating tool output) ===")
    
    # Simulate what the tool would return (bypassing LLM)
    new_food = FoodOverride(
        weights={"italian": 0.8, "vegetarian": 1.0},
        budget_weights={"moderate": 0.5}
    )
    
    tool_output = {
        "preference_overrides": {
            TravelStyle.FAMILY: PreferenceOverride(
                user_id="test_user",
                food=new_food,
                stay=None,
                travel=None
            )
        },
        "current_travel_style": TravelStyle.FAMILY
    }
    
    print(f"Tool output (simulated): {tool_output}")
    
    # Initial state with no preferences
    initial_overrides = None
    
    # Apply reducer
    new_overrides = merge_preference_overrides(
        initial_overrides,
        tool_output.get("preference_overrides")
    )
    
    print(f"After reducer: {new_overrides}")
    
    # Verify
    assert TravelStyle.FAMILY in new_overrides, "FAMILY style should be in overrides"
    family_prefs = new_overrides[TravelStyle.FAMILY]
    assert family_prefs.food is not None, "Food preferences should be set"
    assert family_prefs.food.weights.get("vegetarian") == 1.0
    print(f"✅ New preference created with food preferences")


def test_upsert_preference_override_merge():
    """Test merging preferences with existing ones"""
    print("\n=== Testing preference merging (simulating tool outputs) ===")
    
    # Initial state with existing food preferences
    existing_food = FoodOverride(
        weights={"italian": 0.8, "vegetarian": 1.0},
        budget_weights={"moderate": 0.5}
    )
    
    initial_override = PreferenceOverride(
        user_id="test_user",
        food=existing_food,
        stay=None,
        travel=None
    )
    
    initial_state = {TravelStyle.FAMILY: initial_override}
    
    print(f"Initial state: food={bool(initial_override.food)}, stay={bool(initial_override.stay)}")
    
    # Simulate tool output adding stay preferences
    new_stay = StayOverride(
        weights={"hotel": 0.8, "wifi": 1.0},
        budget_weights={"moderate": 0.5}
    )
    
    tool_output = {
        TravelStyle.FAMILY: PreferenceOverride(
            user_id="test_user",
            food=None,  # Tool only provides new stay preferences
            stay=new_stay,
            travel=None
        )
    }
    
    # Apply reducer
    merged_overrides = merge_preference_overrides(initial_state, tool_output)
    
    print(f"After reducer: {merged_overrides}")
    
    # Verify merge
    family_prefs = merged_overrides[TravelStyle.FAMILY]
    print(f"Merged preferences - food: {bool(family_prefs.food)}, stay: {bool(family_prefs.stay)}")
    
    # Check that both food and stay are present
    assert family_prefs.food is not None, "Food preferences should be preserved"
    assert family_prefs.stay is not None, "Stay preferences should be added"
    assert family_prefs.food.weights.get("vegetarian") == 1.0, "Food details preserved"
    assert family_prefs.stay.weights.get("wifi") == 1.0, "Stay details added"
    
    print("✅ Preferences merged correctly - both food and stay present")


def test_reducer_deep_merge():
    """Test that the reducer properly deep-merges PreferenceOverride fields"""
    print("\n=== Testing merge_preference_overrides reducer ===")
    
    # Old state: has food preferences
    old_food = FoodOverride(
        weights={"italian": 0.8, "vegetarian": 1.0},
        budget_weights={"moderate": 0.5}
    )
    old_overrides = {
        TravelStyle.FAMILY: PreferenceOverride(
            user_id="user1",
            food=old_food,
            stay=None,
            travel=None
        )
    }
    
    # New update: has stay preferences
    new_stay = StayOverride(
        weights={"hotel": 0.8, "wifi": 1.0},
        budget_weights={"moderate": 0.5}
    )
    new_overrides = {
        TravelStyle.FAMILY: PreferenceOverride(
            user_id="user1",
            food=None,
            stay=new_stay,
            travel=None
        )
    }
    
    print(f"Old: food={bool(old_overrides[TravelStyle.FAMILY].food)}, stay={bool(old_overrides[TravelStyle.FAMILY].stay)}")
    print(f"New: food={bool(new_overrides[TravelStyle.FAMILY].food)}, stay={bool(new_overrides[TravelStyle.FAMILY].stay)}")
    
    # Merge with reducer
    merged = merge_preference_overrides(old_overrides, new_overrides)
    
    print(f"Merged: food={bool(merged[TravelStyle.FAMILY].food)}, stay={bool(merged[TravelStyle.FAMILY].stay)}")
    
    # Verify deep merge
    family_prefs = merged[TravelStyle.FAMILY]
    assert family_prefs.food is not None, "Food should be preserved from old"
    assert family_prefs.stay is not None, "Stay should be added from new"
    assert family_prefs.food.weights.get("vegetarian") == 1.0, "Food details should be preserved"
    assert family_prefs.stay.weights.get("wifi") == 1.0, "Stay details should be preserved"
    
    print("✅ Reducer deep-merges correctly")


def test_multiple_travel_styles():
    """Test that different travel styles are handled independently"""
    print("\n=== Testing multiple travel styles ===")
    
    # Old state: has family preferences
    old_overrides = {
        TravelStyle.FAMILY: PreferenceOverride(
            user_id="user1",
            food=FoodOverride(weights={"kid_friendly": 1.0}),
            stay=None,
            travel=None
        )
    }
    
    # New update: add solo preferences
    new_overrides = {
        TravelStyle.SOLO: PreferenceOverride(
            user_id="user1",
            food=FoodOverride(weights={"vegetarian": 1.0}),
            stay=None,
            travel=None
        )
    }
    
    # Merge
    merged = merge_preference_overrides(old_overrides, new_overrides)
    
    print(f"Merged styles: {list(merged.keys())}")
    
    # Verify both styles exist
    assert TravelStyle.FAMILY in merged, "Family style should be preserved"
    assert TravelStyle.SOLO in merged, "Solo style should be added"
    assert merged[TravelStyle.FAMILY].food.weights.get("kid_friendly") == 1.0
    assert merged[TravelStyle.SOLO].food.weights.get("vegetarian") == 1.0
    
    print("✅ Multiple travel styles handled independently")


def test_start_new_trip_no_existing():
    """Test starting a new trip when there's no current trip"""
    print("\n=== Testing start_new_trip (no existing trip) ===")
    
    from tools.travel_planner_tools import start_new_trip
    
    # State with no current trip
    state = {
        "trip_data": None,
        "current_travel_style": TravelStyle.FAMILY
    }
    
    # Start new trip
    result = start_new_trip.func(state, destination="Tokyo", duration_days=7)
    
    print(f"Tool returned: {result}")
    
    # Apply reducer
    new_trip_data = merge_trip_data(state.get("trip_data"), result.get("trip_data"))
    
    print(f"After reducer:")
    print(f"  current_trip: {new_trip_data.get('current_trip').formatted_address if new_trip_data.get('current_trip') else None}")
    print(f"  history_trips: {len(new_trip_data.get('history_trips', [])) if new_trip_data.get('history_trips') else 0} trips")
    
    # Verify
    assert new_trip_data.get("current_trip") is not None, "Current trip should be created"
    assert new_trip_data["current_trip"].formatted_address == "Tokyo"
    assert new_trip_data["current_trip"].duration_days == 7
    assert new_trip_data["current_trip"].status == "planning"
    assert not new_trip_data.get("history_trips"), "History should be empty"
    
    print("✅ New trip created successfully")


def test_start_new_trip_with_existing():
    """Test starting a new trip when there's already a current trip"""
    print("\n=== Testing start_new_trip (moves existing to history) ===")
    
    from tools.travel_planner_tools import start_new_trip
    
    # State with existing trip
    existing_trip = TripState(
        formatted_address="Paris",
        duration_days=5,
        travel_style=TravelStyle.COUPLE,
        status="planning"
    )
    
    state = {
        "trip_data": {
            "current_trip": existing_trip,
            "history_trips": []
        },
        "current_travel_style": TravelStyle.FAMILY
    }
    
    print(f"Initial state:")
    print(f"  current_trip: {existing_trip.formatted_address}")
    print(f"  history: 0 trips")
    
    # Start new trip
    result = start_new_trip.func(state, destination="Tokyo", duration_days=7)
    
    print(f"\nTool returned: {result}")
    
    # Apply reducer
    new_trip_data = merge_trip_data(state.get("trip_data"), result.get("trip_data"))
    
    print(f"\nAfter reducer:")
    print(f"  current_trip: {new_trip_data['current_trip'].formatted_address}")
    print(f"  history_trips: {len(new_trip_data.get('history_trips', []))} trips")
    if new_trip_data.get("history_trips"):
        print(f"  - History[0]: {new_trip_data['history_trips'][0].formatted_address} (status: {new_trip_data['history_trips'][0].status})")
    
    # Verify
    assert new_trip_data["current_trip"].formatted_address == "Tokyo", "Current trip should be Tokyo"
    assert new_trip_data["current_trip"].duration_days == 7
    assert new_trip_data["current_trip"].status == "planning"
    
    assert len(new_trip_data.get("history_trips", [])) == 1, "History should have 1 trip"
    assert new_trip_data["history_trips"][0].formatted_address == "Paris", "Paris trip should be in history"
    assert new_trip_data["history_trips"][0].status == "completed", "Old trip should be marked completed"
    
    print("✅ Trip moved to history and new trip created")


def test_merge_trip_state():
    """Test that current_trip merges fields instead of replacing"""
    print("\n=== Testing merge_trip_state reducer ===")
    
    # Existing trip with some fields
    existing_trip = TripState(
        duration_days=7,
        status="planning"
    )
    
    print(f"Existing trip: destination={existing_trip.formatted_address}, duration={existing_trip.duration_days}, trip_id={existing_trip.trip_id}")
    
    # Partial update (just location from geocode) - SAME trip_id to trigger merge
    location_update = TripState(
        trip_id=existing_trip.trip_id,  # Same ID = merge
        formatted_address="Tokyo, Japan",
        latitude=35.6762,
        longitude=139.6503,
        geocode_result={"some": "data"}
    )
    
    print(f"Location update: address={location_update.formatted_address}, lat/lng={location_update.latitude}/{location_update.longitude}")
    
    # Debug before merge
    print(f"\nBefore merge:")
    print(f"  existing_trip.duration_days: {existing_trip.duration_days}")
    print(f"  location_update.duration_days: {location_update.duration_days}")
    
    # Apply merge reducer
    merged_trip = merge_trip_state(existing_trip, location_update)
    
    print(f"\nMerged trip:")
    print(f"  address: {merged_trip.formatted_address}")
    print(f"  duration_days: {merged_trip.duration_days}")
    print(f"  latitude: {merged_trip.latitude}")
    print(f"  longitude: {merged_trip.longitude}")
    
    # Verify both old and new fields are present
    assert merged_trip.duration_days == 7, "Duration should be preserved"
    assert merged_trip.formatted_address == "Tokyo, Japan", "Address should be updated"
    assert merged_trip.latitude == 35.6762, "Latitude should be added"
    assert merged_trip.longitude == 139.6503, "Longitude should be added"
    
    print("✅ TripState fields merged correctly - old preserved, new added")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing Travel Planner State Updates")
    print("=" * 60)
    
    try:
        test_set_travel_style()
        test_upsert_preference_override_new()
        test_upsert_preference_override_merge()
        test_reducer_deep_merge()
        test_multiple_travel_styles()
        # test_start_new_trip_no_existing()  # Removed - use geocode_destination instead
        # test_start_new_trip_with_existing()  # Removed - use geocode_destination instead
        test_merge_trip_state()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

