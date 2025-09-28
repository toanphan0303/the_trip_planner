#!/usr/bin/env python3
"""
Utility to load categorized mock user profiles
"""

import json
import os
from typing import List, Dict, Optional

class ProfileLoader:
    """Utility class to load categorized user profiles"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
    
    def load_all_profiles(self) -> List[Dict]:
        """Load all user profiles from the original file"""
        file_path = os.path.join(self.base_dir, 'mock_user_profiles.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def load_family_travel_profiles(self) -> List[Dict]:
        """Load profiles for family travel users"""
        file_path = os.path.join(self.base_dir, 'family_travel_profiles.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def load_couple_travel_profiles(self) -> List[Dict]:
        """Load profiles for couple travel users"""
        file_path = os.path.join(self.base_dir, 'couple_travel_profiles.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def load_solo_travel_profiles(self) -> List[Dict]:
        """Load profiles for solo travel users"""
        file_path = os.path.join(self.base_dir, 'solo_travel_profiles.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def load_by_category(self, category: str) -> List[Dict]:
        """Load profiles by travel category"""
        category_map = {
            'family': self.load_family_travel_profiles,
            'couple': self.load_couple_travel_profiles,
            'solo': self.load_solo_travel_profiles
        }
        
        if category.lower() not in category_map:
            raise ValueError(f"Invalid category: {category}. Must be one of: {list(category_map.keys())}")
        
        return category_map[category.lower()]()
    
    def get_categorization_summary(self) -> Dict:
        """Get the categorization summary"""
        file_path = os.path.join(self.base_dir, 'categorization_summary.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def get_index_info(self) -> Dict:
        """Get the index file information"""
        file_path = os.path.join(self.base_dir, 'mock_user_profiles_index.json')
        with open(file_path, 'r') as f:
            return json.load(f)

# Example usage
if __name__ == "__main__":
    loader = ProfileLoader()
    
    print("Profile Loader Demo")
    print("=" * 50)
    
    # Load summary
    summary = loader.get_categorization_summary()
    print(f"Total users: {summary['total_users']}")
    print(f"Family travel: {summary['family_travel_count']}")
    print(f"Couple travel: {summary['couple_travel_count']}")
    print(f"Solo travel: {summary['solo_travel_count']}")
    
    # Load specific categories
    family_users = loader.load_family_travel_profiles()
    couple_users = loader.load_couple_travel_profiles()
    solo_users = loader.load_solo_travel_profiles()
    
    print(f"\nLoaded {len(family_users)} family travel profiles")
    print(f"Loaded {len(couple_users)} couple travel profiles")
    print(f"Loaded {len(solo_users)} solo travel profiles")
    
    # Show first user from each category
    if family_users:
        print(f"\nFirst family user: {family_users[0]['user_id']}")
    if couple_users:
        print(f"First couple user: {couple_users[0]['user_id']}")
    if solo_users:
        print(f"First solo user: {solo_users[0]['user_id']}")
