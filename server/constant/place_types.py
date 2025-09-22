"""
Google Places API Place Types - Base Types System
Based on: https://developers.google.com/maps/documentation/places/web-service/place-types

This module defines comprehensive place types organized by categories for use in Google Places API calls.
Table A types can be used in both requests and responses, while Table B types are primarily for responses.
"""

from typing import List, Set
from enum import Enum


class PlaceTypeCategory(Enum):
    """Categories for organizing place types"""
    AUTOMOTIVE = "automotive"
    BUSINESS = "business"
    CULTURE = "culture"
    EDUCATION = "education"
    ENTERTAINMENT_RECREATION = "entertainment_recreation"
    FACILITIES = "facilities"
    FINANCE = "finance"
    FOOD_DRINK = "food_drink"
    GEOGRAPHICAL_AREAS = "geographical_areas"
    GOVERNMENT = "government"
    HEALTH_WELLNESS = "health_wellness"
    HOUSING = "housing"
    LODGING = "lodging"
    NATURAL_FEATURES = "natural_features"
    PLACES_OF_WORSHIP = "places_of_worship"
    SERVICES = "services"
    SHOPPING = "shopping"
    SPORTS = "sports"
    TRANSPORTATION = "transportation"


# Table A - Types that can be used in both requests and responses
# Based on official Google Places API documentation
TABLE_A_TYPES = {
    PlaceTypeCategory.AUTOMOTIVE: [
        "car_dealer",
        "car_rental", 
        "car_repair",
        "car_wash",
        "electric_vehicle_charging_station",
        "gas_station",
        "parking",
        "rest_stop",
        "auto_parts_store",
        "establishment"
    ],
    
    PlaceTypeCategory.BUSINESS: [
        "atm",
        "bank",
        "insurance_agency",
        "post_office",
        "real_estate_agency",
        "storage",
        "accounting",
        "general_contractor",
        "establishment"
    ],
    
    PlaceTypeCategory.CULTURE: [
        "art_gallery",
        "museum",
        "tourist_attraction",
        "cultural_landmark",
        "historical_place",
        "point_of_interest"
    ],
    
    PlaceTypeCategory.EDUCATION: [
        "library",
        "primary_school",
        "school",
        "secondary_school",
        "university",
        "establishment"
    ],
    
    PlaceTypeCategory.ENTERTAINMENT_RECREATION: [
        "amusement_park",
        "aquarium",
        "art_gallery",
        "bowling_alley",
        "casino",
        "movie_theater",
        "night_club",
        "park",
        "tourist_attraction",
        "zoo",
        "campground",
        "rv_park",
        "establishment"
    ],
    
    PlaceTypeCategory.FACILITIES: [
        "courthouse",
        "embassy",
        "fire_station",
        "funeral_home",
        "hospital",
        "local_government_office",
        "police",
        "post_office",
        "establishment"
    ],
    
    PlaceTypeCategory.FINANCE: [
        "atm",
        "bank",
        "insurance_agency",
        "establishment"
    ],
    
    PlaceTypeCategory.FOOD_DRINK: [
        "bakery",
        "bar",
        "cafe",
        "meal_delivery",
        "meal_takeaway",
        "restaurant",
        "food",
        "establishment"
    ],
    
    PlaceTypeCategory.GEOGRAPHICAL_AREAS: [
        "administrative_area_level_1",
        "administrative_area_level_2",
        "administrative_area_level_3",
        "administrative_area_level_4",
        "administrative_area_level_5",
        "administrative_area_level_6",
        "administrative_area_level_7",
        "colloquial_area",
        "country",
        "locality",
        "neighborhood",
        "political",
        "postal_code",
        "premise",
        "route",
        "street_address",
        "sublocality",
        "sublocality_level_1",
        "sublocality_level_2",
        "sublocality_level_3",
        "sublocality_level_4",
        "sublocality_level_5",
        "subpremise",
        "plus_code"
    ],
    
    PlaceTypeCategory.GOVERNMENT: [
        "courthouse",
        "embassy",
        "local_government_office",
        "establishment"
    ],
    
    PlaceTypeCategory.HEALTH_WELLNESS: [
        "dentist",
        "doctor",
        "drugstore",
        "hospital",
        "pharmacy",
        "physiotherapist",
        "veterinary_care",
        "health",
        "establishment"
    ],
    
    PlaceTypeCategory.HOUSING: [
        "lodging",
        "establishment"
    ],
    
    PlaceTypeCategory.LODGING: [
        "lodging",
        "establishment"
    ],
    
    PlaceTypeCategory.NATURAL_FEATURES: [
        "natural_feature",
        "park",
        "establishment"
    ],
    
    PlaceTypeCategory.PLACES_OF_WORSHIP: [
        "church",
        "hindu_temple",
        "mosque",
        "synagogue",
        "establishment"
    ],
    
    PlaceTypeCategory.SERVICES: [
        "beauty_salon",
        "car_repair",
        "car_wash",
        "electrician",
        "funeral_home",
        "hair_care",
        "laundry",
        "lawyer",
        "locksmith",
        "moving_company",
        "painter",
        "plumber",
        "roofing_contractor",
        "storage",
        "travel_agency",
        "accounting",
        "general_contractor",
        "insurance_agency",
        "real_estate_agency",
        "establishment"
    ],
    
    PlaceTypeCategory.SHOPPING: [
        "bicycle_store",
        "book_store",
        "clothing_store",
        "convenience_store",
        "department_store",
        "electronics_store",
        "furniture_store",
        "hardware_store",
        "home_goods_store",
        "jewelry_store",
        "liquor_store",
        "pet_store",
        "shoe_store",
        "shopping_mall",
        "store",
        "supermarket",
        "auto_parts_store",
        "florist",
        "market",
        "mobile_phone_shop",
        "wholesale_store",
        "establishment"
    ],
    
    PlaceTypeCategory.SPORTS: [
        "gym",
        "stadium",
        "sports_complex",
        "swimming_pool",
        "establishment"
    ],
    
    PlaceTypeCategory.TRANSPORTATION: [
        "airport",
        "bus_station",
        "subway_station",
        "taxi_stand",
        "train_station",
        "transit_station",
        "light_rail_station",
        "establishment"
    ]
}

# Additional Table A types that don't fit neatly into existing categories
# These are from the official Google Places API documentation
ADDITIONAL_TABLE_A_TYPES = {
    "establishment",
    "food",
    "point_of_interest"
}

# Travel Persona Types - Grouped by travel style for LLM classification
# These keywords help the AI understand what types of places different travelers prefer
TRAVEL_PERSONA_TYPES = {
    "solo_traveler": {
        "keywords": ["solo", "independent", "alone", "backpacker", "digital nomad", "solo adventure"],
        "place_types": [
            # Food & Drink - Solo travelers often enjoy cafes, bars, restaurants
            "cafe", "bar", "restaurant", "bakery", "food",
            # Entertainment - Movies, nightlife, cultural activities
            "movie_theater", "night_club", "art_gallery", "museum", "tourist_attraction",
            # Transportation - Easy access is important
            "airport", "bus_station", "train_station", "transit_station", "taxi_stand",
            # Services - Practical needs
            "atm", "bank", "pharmacy", "convenience_store", "store",
            # Culture & Exploration
            "cultural_landmark", "historical_place", "point_of_interest", "establishment"
        ]
    },
    
    "family_with_kids": {
        "keywords": ["family", "kids", "children", "family-friendly", "family vacation", "with kids"],
        "place_types": [
            # Entertainment - Kid-friendly activities
            "amusement_park", "aquarium", "zoo", "park", "bowling_alley", "tourist_attraction",
            # Food - Family restaurants, convenience
            "restaurant", "cafe", "bakery", "convenience_store", "supermarket", "food",
            # Education - Learning opportunities
            "museum", "library", "school", "university",
            # Health & Safety
            "hospital", "pharmacy", "doctor", "dentist", "police", "fire_station",
            # Transportation
            "airport", "bus_station", "train_station", "parking",
            # Services
            "atm", "bank", "store", "shopping_mall", "establishment"
        ]
    },
    
    "couple_romantic": {
        "keywords": ["couple", "romantic", "honeymoon", "anniversary", "date night", "romantic getaway"],
        "place_types": [
            # Food & Drink - Fine dining, romantic settings
            "restaurant", "bar", "cafe", "bakery", "food",
            # Entertainment - Cultural, intimate venues
            "art_gallery", "museum", "movie_theater", "night_club", "tourist_attraction",
            # Nature & Scenic
            "park", "natural_feature", "cultural_landmark", "historical_place",
            # Lodging - Romantic accommodations
            "lodging", "establishment",
            # Services
            "pharmacy", "convenience_store", "store", "atm", "bank"
        ]
    },
    
    "adventure_explorer": {
        "keywords": ["adventure", "explorer", "outdoor", "hiking", "nature", "adventure seeker", "outdoor enthusiast"],
        "place_types": [
            # Nature & Outdoor
            "park", "natural_feature", "campground", "rv_park", "tourist_attraction",
            # Sports & Recreation
            "gym", "stadium", "sports_complex", "swimming_pool",
            # Transportation - Remote access
            "airport", "bus_station", "train_station", "parking", "gas_station",
            # Food - Casual, practical
            "restaurant", "cafe", "convenience_store", "supermarket", "food",
            # Services - Essential
            "hospital", "pharmacy", "atm", "bank", "store", "establishment"
        ]
    },
    
    "food_enthusiast": {
        "keywords": ["foodie", "culinary", "gastronomy", "food lover", "dining", "restaurant", "cuisine"],
        "place_types": [
            # Food & Drink - All types
            "restaurant", "cafe", "bar", "bakery", "food", "meal_delivery", "meal_takeaway",
            # Shopping - Food-related
            "supermarket", "convenience_store", "market", "store", "liquor_store",
            # Entertainment - Food-related activities
            "tourist_attraction", "cultural_landmark", "historical_place",
            # Services
            "atm", "bank", "pharmacy", "establishment"
        ]
    },
    
    "culture_art_lover": {
        "keywords": ["culture", "art", "museum", "gallery", "cultural", "artistic", "history", "heritage"],
        "place_types": [
            # Culture & Arts
            "museum", "art_gallery", "cultural_landmark", "historical_place", "tourist_attraction",
            # Education
            "library", "university", "school",
            # Entertainment - Cultural venues
            "movie_theater", "theater", "night_club",
            # Places of Worship - Cultural significance
            "church", "mosque", "synagogue", "hindu_temple",
            # Food - Cultural dining
            "restaurant", "cafe", "bar", "food",
            # Services
            "atm", "bank", "store", "establishment"
        ]
    },
    
    "business_traveler": {
        "keywords": ["business", "corporate", "work", "meeting", "conference", "professional"],
        "place_types": [
            # Business & Finance
            "bank", "atm", "insurance_agency", "accounting", "real_estate_agency",
            # Transportation - Efficiency important
            "airport", "bus_station", "train_station", "taxi_stand", "parking",
            # Lodging - Business accommodations
            "lodging", "establishment",
            # Food - Quick, convenient
            "restaurant", "cafe", "convenience_store", "food",
            # Services - Professional needs
            "post_office", "pharmacy", "hospital", "doctor", "store",
            # Government & Facilities
            "courthouse", "embassy", "local_government_office"
        ]
    },
    
    "budget_backpacker": {
        "keywords": ["budget", "backpacker", "cheap", "affordable", "hostel", "budget travel", "backpacking"],
        "place_types": [
            # Transportation - Budget options
            "bus_station", "train_station", "transit_station", "parking",
            # Food - Affordable options
            "restaurant", "cafe", "convenience_store", "supermarket", "food",
            # Lodging - Budget accommodations
            "lodging", "campground", "rv_park", "establishment",
            # Services - Essential only
            "atm", "bank", "pharmacy", "hospital", "store",
            # Entertainment - Free/cheap activities
            "park", "tourist_attraction", "museum", "library"
        ]
    },
    
    "luxury_traveler": {
        "keywords": ["luxury", "premium", "high-end", "upscale", "exclusive", "luxury travel"],
        "place_types": [
            # Food & Drink - Fine dining
            "restaurant", "bar", "cafe", "bakery", "food",
            # Entertainment - Premium venues
            "casino", "night_club", "art_gallery", "museum", "tourist_attraction",
            # Shopping - High-end
            "shopping_mall", "jewelry_store", "clothing_store", "department_store", "store",
            # Lodging - Luxury accommodations
            "lodging", "establishment",
            # Transportation - Premium options
            "airport", "taxi_stand", "parking",
            # Services - Premium services
            "bank", "atm", "pharmacy", "hospital", "beauty_salon", "spa"
        ]
    },
    
    "wellness_retreat": {
        "keywords": ["wellness", "spa", "relaxation", "health", "wellness retreat", "healing", "meditation"],
        "place_types": [
            # Health & Wellness
            "hospital", "pharmacy", "doctor", "dentist", "physiotherapist", "veterinary_care", "health",
            # Services - Wellness-related
            "beauty_salon", "hair_care", "spa", "massage", "establishment",
            # Nature - Peaceful settings
            "park", "natural_feature", "tourist_attraction",
            # Food - Healthy options
            "restaurant", "cafe", "supermarket", "food",
            # Places of Worship - Spiritual
            "church", "mosque", "synagogue", "hindu_temple",
            # Lodging - Wellness accommodations
            "lodging", "establishment"
        ]
    }
}

# Table B - Additional types primarily for responses (can be used in Autocomplete includedPrimaryTypes)
TABLE_B_TYPES = {
    PlaceTypeCategory.FOOD_DRINK: [
        "american_restaurant",
        "asian_restaurant",
        "barbecue_restaurant",
        "brazilian_restaurant",
        "breakfast_restaurant",
        "brunch_restaurant",
        "chinese_restaurant",
        "fast_food_restaurant",
        "french_restaurant",
        "greek_restaurant",
        "hamburger_restaurant",
        "ice_cream_shop",
        "indian_restaurant",
        "indonesian_restaurant",
        "italian_restaurant",
        "japanese_restaurant",
        "korean_restaurant",
        "lebanese_restaurant",
        "meal_delivery",
        "meal_takeaway",
        "mediterranean_restaurant",
        "mexican_restaurant",
        "middle_eastern_restaurant",
        "pizza_restaurant",
        "ramen_restaurant",
        "restaurant",
        "sandwich_shop",
        "seafood_restaurant",
        "spanish_restaurant",
        "steak_house",
        "sushi_restaurant",
        "thai_restaurant",
        "turkish_restaurant",
        "vegan_restaurant",
        "vegetarian_restaurant",
        "vietnamese_restaurant"
    ],
    
    PlaceTypeCategory.SHOPPING: [
        "auto_parts_store",
        "bicycle_store",
        "book_store",
        "car_dealer",
        "clothing_store",
        "convenience_store",
        "department_store",
        "electronics_store",
        "florist",
        "furniture_store",
        "hardware_store",
        "home_goods_store",
        "jewelry_store",
        "liquor_store",
        "market",
        "mobile_phone_shop",
        "pet_store",
        "shoe_store",
        "shopping_mall",
        "store",
        "supermarket",
        "wholesale_store"
    ],
    
    PlaceTypeCategory.ENTERTAINMENT_RECREATION: [
        "amusement_park",
        "aquarium",
        "art_gallery",
        "bowling_alley",
        "casino",
        "movie_theater",
        "night_club",
        "park",
        "tourist_attraction",
        "zoo"
    ],
    
    PlaceTypeCategory.HEALTH_WELLNESS: [
        "dentist",
        "doctor",
        "drugstore",
        "hospital",
        "pharmacy",
        "physiotherapist",
        "veterinary_care"
    ],
    
    PlaceTypeCategory.SERVICES: [
        "beauty_salon",
        "car_repair",
        "car_wash",
        "electrician",
        "funeral_home",
        "hair_care",
        "laundry",
        "lawyer",
        "locksmith",
        "moving_company",
        "painter",
        "plumber",
        "roofing_contractor",
        "storage",
        "travel_agency"
    ]
}

# Combined types for easy access
ALL_TABLE_A_TYPES: Set[str] = set()
for category_types in TABLE_A_TYPES.values():
    ALL_TABLE_A_TYPES.update(category_types)
# Add the additional Table A types
ALL_TABLE_A_TYPES.update(ADDITIONAL_TABLE_A_TYPES)

ALL_TABLE_B_TYPES: Set[str] = set()
for category_types in TABLE_B_TYPES.values():
    ALL_TABLE_B_TYPES.update(category_types)

ALL_PLACE_TYPES: Set[str] = ALL_TABLE_A_TYPES.union(ALL_TABLE_B_TYPES)


class PlaceTypes:
    """Main class for accessing place types organized by categories"""
    
    @staticmethod
    def get_types_by_category(category: PlaceTypeCategory, table: str = "A") -> List[str]:
        """
        Get place types for a specific category
        
        Args:
            category: The place type category
            table: "A" for Table A types (request/response), "B" for Table B types (response only)
            
        Returns:
            List of place types for the category
        """
        if table.upper() == "A":
            return TABLE_A_TYPES.get(category, [])
        elif table.upper() == "B":
            return TABLE_B_TYPES.get(category, [])
        else:
            raise ValueError("Table must be 'A' or 'B'")
    
    @staticmethod
    def get_all_table_a_types() -> List[str]:
        """Get all Table A types (can be used in requests)"""
        return list(ALL_TABLE_A_TYPES)
    
    @staticmethod
    def get_all_table_b_types() -> List[str]:
        """Get all Table B types (response only)"""
        return list(ALL_TABLE_B_TYPES)
    
    @staticmethod
    def get_all_types() -> List[str]:
        """Get all place types from both tables"""
        return list(ALL_PLACE_TYPES)
    
    @staticmethod
    def get_trip_planning_types() -> List[str]:
        """
        Get comprehensive list of place types for trip planning
        Covers all travel personas and common tourist needs
        """
        return [
            # Attractions and Culture - Universal appeal
            "tourist_attraction",
            "museum",
            "art_gallery",
            "cultural_landmark",
            "historical_place",
            "point_of_interest",
            
            # Entertainment - Broad appeal
            "park",
            "zoo",
            "aquarium",
            "amusement_park",
            "night_club",
            "casino",
            "bowling_alley",
            "stadium",
            
            # Food and Drink - Essential for all travelers
            "restaurant",
            "cafe",
            "bar",
            "bakery",
            "food",
            "meal_delivery",
            "meal_takeaway",
            
            # Shopping - Universal needs
            "shopping_mall",
            "supermarket",
            "book_store",
                       
            "natural_feature",
            
            "beach",
            
            # Education - Learning opportunities
            "library",
            "university",
            "school",
            
            
        
        ]
    
    @staticmethod
    def get_food_types() -> List[str]:
        """Get all food and drink related place types"""
        return PlaceTypes.get_types_by_category(PlaceTypeCategory.FOOD_DRINK, "A") + \
               PlaceTypes.get_types_by_category(PlaceTypeCategory.FOOD_DRINK, "B")
    
    @staticmethod
    def get_attraction_types() -> List[str]:
        """Get all attraction and entertainment related place types"""
        return PlaceTypes.get_types_by_category(PlaceTypeCategory.ENTERTAINMENT_RECREATION, "A") + \
               PlaceTypes.get_types_by_category(PlaceTypeCategory.CULTURE, "A")
    
    @staticmethod
    def get_shopping_types() -> List[str]:
        """Get all shopping related place types"""
        return PlaceTypes.get_types_by_category(PlaceTypeCategory.SHOPPING, "A") + \
               PlaceTypes.get_types_by_category(PlaceTypeCategory.SHOPPING, "B")
    
    @staticmethod
    def is_valid_type(place_type: str, table: str = "A") -> bool:
        """
        Check if a place type is valid for the specified table
        
        Args:
            place_type: The place type to validate
            table: "A" for Table A types, "B" for Table B types
            
        Returns:
            True if the type is valid for the specified table
        """
        if table.upper() == "A":
            return place_type in ALL_TABLE_A_TYPES
        elif table.upper() == "B":
            return place_type in ALL_TABLE_B_TYPES
        else:
            raise ValueError("Table must be 'A' or 'B'")
    
    @staticmethod
    def get_category_for_type(place_type: str) -> PlaceTypeCategory:
        """
        Get the category for a specific place type
        
        Args:
            place_type: The place type to look up
            
        Returns:
            The category for the place type, or None if not found
        """
        for category, types in TABLE_A_TYPES.items():
            if place_type in types:
                return category
        
        for category, types in TABLE_B_TYPES.items():
            if place_type in types:
                return category
        
        return None
    
    @staticmethod
    def get_travel_persona_types(persona: str) -> List[str]:
        """
        Get place types for a specific travel persona
        
        Args:
            persona: The travel persona (e.g., 'solo_traveler', 'family_with_kids')
            
        Returns:
            List of place types for the persona
        """
        if persona in TRAVEL_PERSONA_TYPES:
            return TRAVEL_PERSONA_TYPES[persona]["place_types"]
        return []
    
    @staticmethod
    def get_travel_persona_keywords(persona: str) -> List[str]:
        """
        Get keywords for a specific travel persona (for LLM classification)
        
        Args:
            persona: The travel persona (e.g., 'solo_traveler', 'family_with_kids')
            
        Returns:
            List of keywords for the persona
        """
        if persona in TRAVEL_PERSONA_TYPES:
            return TRAVEL_PERSONA_TYPES[persona]["keywords"]
        return []
    
    @staticmethod
    def get_all_travel_personas() -> List[str]:
        """
        Get all available travel personas
        
        Returns:
            List of all travel persona names
        """
        return list(TRAVEL_PERSONA_TYPES.keys())
    
    @staticmethod
    def classify_travel_persona(user_input: str) -> List[str]:
        """
        Classify user input to determine likely travel personas
        This is a simple keyword-based classification - can be enhanced with LLM
        
        Args:
            user_input: User's travel description or preferences
            
        Returns:
            List of matching travel personas (ordered by relevance)
        """
        user_input_lower = user_input.lower()
        persona_scores = {}
        
        for persona, data in TRAVEL_PERSONA_TYPES.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword.lower() in user_input_lower:
                    score += 1
            if score > 0:
                persona_scores[persona] = score
        
        # Return personas sorted by score (highest first)
        return sorted(persona_scores.keys(), key=lambda x: persona_scores[x], reverse=True)
    
    @staticmethod
    def get_place_types_for_personas(personas: List[str]) -> List[str]:
        """
        Get combined place types for multiple travel personas
        
        Args:
            personas: List of travel personas
            
        Returns:
            Combined list of place types (with duplicates removed)
        """
        all_types = set()
        for persona in personas:
            types = PlaceTypes.get_travel_persona_types(persona)
            all_types.update(types)
        return list(all_types)
    
    @staticmethod
    def get_comprehensive_trip_types() -> List[str]:
        """
        Get comprehensive place types that cover all travel personas
        This is the most inclusive list for trip planning
        
        Returns:
            Combined list of all place types from all travel personas
        """
        all_personas = PlaceTypes.get_all_travel_personas()
        return PlaceTypes.get_place_types_for_personas(all_personas)


# Convenience functions for backward compatibility
def get_trip_planning_types() -> List[str]:
    """Get curated list of place types for trip planning"""
    return PlaceTypes.get_trip_planning_types()

def get_food_types() -> List[str]:
    """Get all food and drink related place types"""
    return PlaceTypes.get_food_types()

def get_attraction_types() -> List[str]:
    """Get all attraction and entertainment related place types"""
    return PlaceTypes.get_attraction_types()

def get_shopping_types() -> List[str]:
    """Get all shopping related place types"""
    return PlaceTypes.get_shopping_types()

def is_valid_place_type(place_type: str, table: str = "A") -> bool:
    """Check if a place type is valid for the specified table"""
    return PlaceTypes.is_valid_type(place_type, table)

# Travel Persona convenience functions
def get_travel_persona_types(persona: str) -> List[str]:
    """Get place types for a specific travel persona"""
    return PlaceTypes.get_travel_persona_types(persona)

def get_travel_persona_keywords(persona: str) -> List[str]:
    """Get keywords for a specific travel persona (for LLM classification)"""
    return PlaceTypes.get_travel_persona_keywords(persona)

def get_all_travel_personas() -> List[str]:
    """Get all available travel personas"""
    return PlaceTypes.get_all_travel_personas()

def classify_travel_persona(user_input: str) -> List[str]:
    """Classify user input to determine likely travel personas"""
    return PlaceTypes.classify_travel_persona(user_input)

def get_place_types_for_personas(personas: List[str]) -> List[str]:
    """Get combined place types for multiple travel personas"""
    return PlaceTypes.get_place_types_for_personas(personas)

def get_comprehensive_trip_types() -> List[str]:
    """Get comprehensive place types that cover all travel personas"""
    return PlaceTypes.get_comprehensive_trip_types()
