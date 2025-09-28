# Categorized Mock User Profiles

The mock user profiles have been reorganized into travel categories for easier management and loading.

## File Structure

### Categorized Files
- `family_travel_profiles.json` - 36 users with family-friendly travel preferences
- `couple_travel_profiles.json` - 34 users with romantic/couple travel preferences  
- `solo_travel_profiles.json` - 30 users with solo/adventure travel preferences

### Index and Utility Files
- `mock_user_profiles_index.json` - Index file with metadata about the categorization
- `categorization_summary.json` - Summary of categorization results
- `profile_loader.py` - Utility class for loading categorized profiles
- `mock_user_profiles.json` - Original file with all 100 users (preserved)

## Categorization Criteria

### Family Travel (36 users)
Users categorized as family travel have one or more of:
- `must_include_keywords` contains "family_friendly"
- `stay.child_ages` is not empty (has children)
- `stay.adult_count` > 2 (large group bookings)

### Couple Travel (34 users)  
Users categorized as couple travel have one or more of:
- `must_include_keywords` contains "romantic"
- `must_include_keywords` contains "luxury"
- `stay.adult_count` == 2 (couple-sized bookings)

### Solo Travel (30 users)
Users categorized as solo travel have one or more of:
- `travel.adventure_score` > 0.7 (high adventure preference)
- `travel.group_size_preference` < 0.3 (prefers small groups)
- `must_include_keywords` contains "adventure"

## Usage

### Using the Profile Loader
```python
from profile_loader import ProfileLoader

loader = ProfileLoader()

# Load all profiles
all_users = loader.load_all_profiles()

# Load by category
family_users = loader.load_family_travel_profiles()
couple_users = loader.load_couple_travel_profiles()
solo_users = loader.load_solo_travel_profiles()

# Load by category name
adventure_users = loader.load_by_category('solo')
```

### Direct File Access
```python
import json

# Load specific category
with open('family_travel_profiles.json', 'r') as f:
    family_users = json.load(f)
```

## Benefits

1. **Targeted Loading**: Load only the user profiles relevant to your use case
2. **Reduced Memory Usage**: Smaller files for specific travel types
3. **Better Organization**: Clear separation of travel preferences
4. **Easy Testing**: Test with specific user types (family, couple, solo)
5. **Preserved Original**: Original file remains unchanged for backward compatibility

## File Sizes
- `family_travel_profiles.json`: ~36 users
- `couple_travel_profiles.json`: ~34 users  
- `solo_travel_profiles.json`: ~30 users
- `mock_user_profiles.json`: 100 users (original)

Each categorized file contains the complete user profile data with an additional `categorization_reason` field explaining why the user was placed in that category.
