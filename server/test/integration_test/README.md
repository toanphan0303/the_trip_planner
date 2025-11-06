# Integration Tests

Tests for the Travel Planner with real dependencies (MongoDB, Google APIs).

## Prerequisites

### 1. Start MongoDB
```bash
# From project root
docker-compose up -d mongodb
```

### 2. Set Environment Variables
```bash
# Copy and configure .env
cp server/env_template.txt server/.env
# Add your Google API keys
```

## Running Tests

### Run All Tests
```bash
# From project root
./venv/bin/python3 server/test/integration_test/test_*.py
```

### Run Specific Test
```bash
# State management tests (no external dependencies)
./venv/bin/python3 server/test/integration_test/test_travel_planner_state.py

# Search tool test (requires MongoDB + Google API)
./venv/bin/python3 server/test/integration_test/test_search_nearby_places_tool.py

# Place type selection
./venv/bin/python3 server/test/integration_test/test_select_types_for_user.py

# Preference parsing
./venv/bin/python3 server/test/integration_test/test_override_parser.py
```

## Test Categories

### No External Dependencies
- `test_travel_planner_state.py` - State reducers, merging logic
- `test_override_parser.py` - Preference parsing (needs API key for LLM)

### Requires MongoDB
- `test_search_nearby_places_tool.py` - **Verifies cache hits**

### Requires Google API
- `test_select_types_for_user.py` - Place type selection
- `test_detect_preferences.py` - Preference detection

## Cache Verification

The `test_search_nearby_places_tool.py` specifically tests:
1. ✅ First call searches and caches to MongoDB
2. ✅ Second call hits cache (significantly faster)
3. ✅ Returns same results
4. ✅ place_types selected correctly (4-7 types)
5. ✅ POIs captured and converted to dicts

Expected output:
```
First call: 0.5-2.0s (API calls)
Second call: 0.001-0.05s (cache hit)
Speedup: 10-100x faster
```

