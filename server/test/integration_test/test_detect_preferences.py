#!/usr/bin/env python3
"""
Test: detect_and_save_preferences tool
Tests detecting preferences from user input and saving to Redis
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))
load_dotenv(os.path.join(os.path.dirname(__file__), 'server', '.env'))

from tools.travel_planner_tools import detect_and_save_preferences
from user_profile.ephemeral.redis_overlay_store import get_redis_overlay_store


def test_detect_preferences():
    """Test preference detection and Redis storage"""
    
    print("=" * 80)
    print("🧪 TEST: Detect and Save Preferences to Redis")
    print("=" * 80)
    print()
    
    test_cases = [
        {
            "name": "Vegetarian Food Preference",
            "user_id": "test_user_1",
            "message": "I want to eat vegetarian food during this trip, no meat please",
            "scope": "trip",
            "context": "Planning Tokyo trip"
        },
        {
            "name": "Museum and Shopping Activities",
            "user_id": "test_user_2",
            "message": "I really love museums and want to do some shopping for souvenirs",
            "scope": "trip",
            "context": "Planning Tokyo trip"
        },
        {
            "name": "Day-Specific: Nightlife Tonight",
            "user_id": "test_user_3",
            "message": "Tonight I want to experience Tokyo nightlife, bars and live music",
            "scope": "day",
            "context": "Day 2 evening plans"
        },
        {
            "name": "No Preferences Mentioned",
            "user_id": "test_user_4",
            "message": "What time does the museum open?",
            "scope": "conversation",
            "context": "Asking about logistics"
        }
    ]
    
    results = []
    
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {idx}: {test_case['name']}")
        print(f"{'='*80}\n")
        
        print(f"💬 User message: \"{test_case['message']}\"")
        print(f"🔖 Scope: {test_case['scope']}")
        print(f"📝 Context: {test_case['context']}")
        print()
        
        # Call the tool
        result = detect_and_save_preferences.invoke({
            "user_id": test_case['user_id'],
            "user_message": test_case['message'],
            "scope": test_case['scope'],
            "context": test_case['context']
        })
        
        print(f"\n📊 Result:")
        print(f"   Success: {result.get('success')}")
        
        if result.get('success') and result.get('data', {}).get('preferences_detected'):
            data = result['data']
            print(f"   Action: {data.get('action')}")
            print(f"   Overlay ID: {data.get('overlay_id')}")
            print(f"   Scope: {data.get('scope')}")
            print(f"   Confidence: {data.get('confidence'):.2f}")
            
            prefs = data.get('preferences', {})
            if prefs:
                print(f"   Detected Preferences:")
                for key, value in prefs.items():
                    print(f"      - {key}: {value}")
            
            results.append({
                "test": test_case['name'],
                "detected": True,
                "success": True
            })
        elif result.get('success'):
            print(f"   ℹ️  {result.get('data', {}).get('message')}")
            results.append({
                "test": test_case['name'],
                "detected": False,
                "success": True
            })
        else:
            error = result.get('error', {})
            print(f"   ❌ Error: {error.get('message')}")
            results.append({
                "test": test_case['name'],
                "detected": False,
                "success": False
            })
        
        # Verify it's in Redis
        if result.get('success') and result.get('data', {}).get('preferences_detected'):
            overlay_id = result['data']['overlay_id']
            scope = result['data']['scope']
            
            redis_store = get_redis_overlay_store()
            stored_overlays = redis_store.get_active_overlays(test_case['user_id'], scope)
            
            if stored_overlays:
                print(f"\n   ✅ Verified in Redis: Found {len(stored_overlays)} overlay(s)")
                for overlay in stored_overlays:
                    print(f"      - {overlay.overlay_id} (expires in {overlay.expires_at - int(__import__('time').time())}s)")
            else:
                print(f"\n   ⚠️  Not found in Redis")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*80}\n")
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    detected = sum(1 for r in results if r['detected'])
    
    print(f"Total Tests: {total}")
    print(f"Successful: {successful}/{total}")
    print(f"Preferences Detected: {detected}/{total}")
    print()
    
    for idx, result in enumerate(results, 1):
        status = "✅" if result['success'] else "❌"
        detection = "🔍 Detected" if result['detected'] else "⏭️  Skipped"
        print(f"{idx}. {status} {result['test']}: {detection}")
    
    if successful == total:
        print(f"\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")


if __name__ == "__main__":
    test_detect_preferences()

