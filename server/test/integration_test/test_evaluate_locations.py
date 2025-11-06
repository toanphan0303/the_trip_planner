"""
Integration test for evaluate_locations function

Tests:
1. POI evaluation using test data
2. Separation of restaurants vs attractions
3. POI object updates (travel_style, poi_evaluation)
4. Evaluation result mapping
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add server directory to Python path
server_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(server_dir))

import pytest
from models.point_of_interest_models import PointOfInterest, POIType, Location
from models.google_map_models import GooglePlace
from user_profile.models import TravelStyle, UserPreference, FoodPreference, TravelPreference
from user_profile.ephemeral.preference_override_model import PreferenceOverride, FoodOverride, TravelOverride
from utils.location_evaluator import evaluate_locations
from models.location_preference_model import LocationPreferenceMatch, LocationPreferenceMatches


def load_tokyo_pois():
    """Load POIs from test_pois_tokyo.json - simplified version"""
    test_dir = Path(__file__).parent
    json_path = test_dir / "test_pois_tokyo.json"
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    pois = []
    for poi_data in data['pois'][:15]:  # Use first 15 POIs for faster testing
        # Extract basic info directly from JSON
        display_name_obj = poi_data.get('display_name', {})
        name = display_name_obj.get('text', 'Unknown') if isinstance(display_name_obj, dict) else 'Unknown'
        
        location_obj = poi_data.get('location', {})
        
        poi = PointOfInterest(
            name=name,
            type_POI=POIType.place,
            types=poi_data.get('types', []),
            address=poi_data.get('formatted_address', ''),
            location=Location(
                latitude=location_obj.get('latitude') if location_obj else None,
                longitude=location_obj.get('longitude') if location_obj else None
            )
        )
        pois.append(poi)
    
    return pois


def create_family_user_preference():
    """Create mock UserPreference for family travel"""
    return UserPreference(
        user_id="test_family_user",
        food={
            TravelStyle.FAMILY: FoodPreference(
                weights={
                    "cuisine:japanese": 0.8,
                    "kid_friendly": 0.9,
                    "fast_food": -0.5,
                },
                budget_weights={
                    "budget": 0.7,
                    "moderate": 0.8,
                    "luxury": 0.3
                }
            )
        },
        travel={
            TravelStyle.FAMILY: TravelPreference(
                weights={
                    "museums": 0.8,
                    "zoo": 0.9,
                    "temple": 0.6,
                    "kid_friendly": 1.0,
                    "educational": 0.8,
                    "bars": -1.0,
                    "nightlife": -0.9
                }
            )
        }
    )


def create_family_preference_override():
    """Create mock PreferenceOverride for family with recent requests"""
    return PreferenceOverride(
        user_id="test_family_user",
        food=FoodOverride(
            weights={
                "sushi": 1.0,  # Recent explicit request
                "ramen": 0.9
            }
        ),
        travel=TravelOverride(
            weights={
                "temple": 1.0,  # Want to visit temples specifically
                "museum": 0.8
            }
        )
    )


def create_mock_llm_response(pois):
    """Create mock LLM evaluation response for given POIs"""
    matches = []
    for poi in pois:
        from utils.poi_utils import is_restaurant
        
        # Create realistic mock evaluations
        if is_restaurant(poi):
            fit_score = 0.75 if 'japanese' in str(poi.types).lower() else 0.60
            reason = "Good restaurant option for families with kid-friendly atmosphere"
        else:
            fit_score = 0.80 if any(t in poi.types for t in ['museum', 'zoo', 'park']) else 0.65
            reason = "Great family attraction with educational value"
        
        match = LocationPreferenceMatch(
            name=poi.name,
            fit_score=fit_score,
            reason=reason,
            highlights=f"Perfect for families visiting {poi.name}",
            confidence="high",
            key_attractions=["Family-friendly", "Educational", "Safe"],
            travel_style_match="family",
            concern=None,
            tips="Best visited in the morning"
        )
        matches.append(match)
    
    return LocationPreferenceMatches(matches=matches)


def test_poi_objects_updated():
    """
    MAIN TEST: Verify POI objects are updated with evaluation data
    
    Tests:
    1. Load POIs from test_pois_tokyo.json
    2. Mock LLM evaluation responses
    3. Call evaluate_locations()
    4. Verify POI objects have:
       - travel_style set
       - poi_evaluation populated with correct data
    """
    # Load test POIs
    pois = load_tokyo_pois()
    
    # Separate restaurants and attractions for mocking
    from utils.poi_utils import is_restaurant
    restaurants = [poi for poi in pois if is_restaurant(poi)]
    attractions = [poi for poi in pois if not is_restaurant(poi)]
    
    print(f"\n📊 Loaded {len(pois)} POIs: {len(restaurants)} restaurants, {len(attractions)} attractions")
    
    # Before evaluation - should have no evaluation data
    for poi in pois:
        assert poi.travel_style is None, "travel_style should be None before evaluation"
        assert poi.poi_evaluation is None, "poi_evaluation should be None before evaluation"
    
    # Mock the internal _evaluate_poi_batch function to return mock data
    with patch('utils.location_evaluator._evaluate_poi_batch') as mock_batch:
        # Return mock evaluations for each batch call
        def mock_evaluate_batch(pois, **kwargs):
            if not pois:
                return None
            return [match for match in create_mock_llm_response(pois).matches]
        
        mock_batch.side_effect = mock_evaluate_batch
        
        # MAIN ACTION: Evaluate locations
        matches = evaluate_locations(
            pois=pois,
            travel_style=TravelStyle.FAMILY,
            user_preference=create_family_user_preference()
        )
    
    # ASSERTIONS: Verify results
    assert matches is not None, "Should return evaluation results"
    print(f"✅ Returned {len(matches)} evaluation matches")
    
    # Check POI objects are updated
    updated_count = 0
    for poi in pois:
        if poi.poi_evaluation is not None:
            updated_count += 1
            
            # Check travel_style is set
            assert poi.travel_style == TravelStyle.FAMILY, f"POI {poi.name} should have travel_style=FAMILY"
            
            # Check poi_evaluation fields
            assert isinstance(poi.poi_evaluation, LocationPreferenceMatch), f"POI {poi.name} should have LocationPreferenceMatch"
            assert poi.poi_evaluation.name == poi.name, f"Evaluation name should match POI name"
            assert 0.0 <= poi.poi_evaluation.fit_score <= 1.0, f"Fit score should be 0-1"
            assert poi.poi_evaluation.reason, f"Should have a reason"
            assert poi.poi_evaluation.highlights, f"Should have highlights"
            assert poi.poi_evaluation.travel_style_match == "family", f"Should match family style"
            
            print(f"   ✓ {poi.name}: score={poi.poi_evaluation.fit_score:.2f}")
    
    assert updated_count > 0, "At least some POIs should be updated with evaluation data"
    print(f"\n✅ SUCCESS: Updated {updated_count}/{len(pois)} POIs with evaluation data")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

