"""
User Profile Models
Defines user preferences and profile data structures
"""

import time
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class FoodType(str, Enum):
    """Food type preferences"""
    LOCAL = "local"
    INTERNATIONAL = "international"
    FUSION = "fusion"
    STREET_FOOD = "street_food"
    FINE_DINING = "fine_dining"
    CASUAL = "casual"
    FAST_FOOD = "fast_food"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    HALAL = "halal"
    KOSHER = "kosher"


class CuisineType(str, Enum):
    """Cuisine type preferences"""
    JAPANESE = "japanese"
    CHINESE = "chinese"
    KOREAN = "korean"
    THAI = "thai"
    VIETNAMESE = "vietnamese"
    INDIAN = "indian"
    ITALIAN = "italian"
    FRENCH = "french"
    MEXICAN = "mexican"
    AMERICAN = "american"
    MEDITERRANEAN = "mediterranean"
    MIDDLE_EASTERN = "middle_eastern"


class BudgetLevel(str, Enum):
    """Budget level preferences"""
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"


class StayType(str, Enum):
    """Accommodation type preferences"""
    HOTEL = "hotel"
    RESORT = "resort"
    HOSTEL = "hostel"
    GUEST_HOUSE = "guest_house"
    APARTMENT = "apartment"
    VILLA = "villa"
    CAMPING = "camping"
    BED_AND_BREAKFAST = "bed_and_breakfast"


class TravelStyle(str, Enum):
    """Travel style preferences"""
    ADVENTURE = "adventure"
    RELAXATION = "relaxation"
    CULTURAL = "cultural"
    BUSINESS = "business"
    FAMILY = "family"
    SOLO = "solo"
    COUPLE = "couple"
    GROUP = "group"
    BACKPACKING = "backpacking"
    LUXURY = "luxury"


class TransportMode(str, Enum):
    """Transportation mode preferences"""
    WALKING = "walking"
    PUBLIC_TRANSPORT = "public_transport"
    TAXI = "taxi"
    RENTAL_CAR = "rental_car"
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    BUS = "bus"
    TRAIN = "train"
    PLANE = "plane"
    BOAT = "boat"


class ActivityType(str, Enum):
    """Activity type preferences"""
    SIGHTSEEING = "sightseeing"
    MUSEUMS = "museums"
    NIGHTLIFE = "nightlife"
    SHOPPING = "shopping"
    OUTDOOR = "outdoor"
    SPORTS = "sports"
    WELLNESS = "wellness"
    ENTERTAINMENT = "entertainment"
    FOOD_TOURS = "food_tours"
    ADVENTURE = "adventure"


class FoodPreference(BaseModel):
    """Food and dining preferences with ML-optimized numerical representations"""
    # Cuisine preferences as weights (0-1, where 1 = highly preferred)
    cuisine_weights: Dict[str, float] = Field(default_factory=dict, description="Cuisine type preferences as weights (0-1, where 1=highly preferred). Example: {'japanese': 0.9, 'italian': 0.7, 'mexican': 0.3}")
    
    # Food type preferences as weights (0-1, where 1 = highly preferred)
    food_type_weights: Dict[str, float] = Field(default_factory=dict, description="Food type preferences as weights (0-1, where 1=highly preferred). Example: {'fine_dining': 0.8, 'street_food': 0.6, 'fast_food': 0.1}")
    
    # Budget level as numerical score (0=budget, 0.5=moderate, 1=luxury)
    budget_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Budget level preference (0=budget, 0.5=moderate, 1=luxury). Example: 0.8 for luxury dining, 0.2 for budget meals")
    
    # Dietary restrictions as weights (0=no restriction, 1=strict requirement)
    dietary_restriction_weights: Dict[str, float] = Field(default_factory=dict, description="Dietary restrictions as weights (0=no restriction, 1=strict requirement). Example: {'vegetarian': 1.0, 'gluten_free': 0.8}")
    
    # Dish preferences as weights (0-1, where 1 = highly preferred)
    dish_weights: Dict[str, float] = Field(default_factory=dict, description="Dish preferences as weights (0-1, where 1=highly preferred). Example: {'sushi': 0.9, 'pasta': 0.7, 'salad': 0.4}")
    
    # Meal timing preferences as weights (0-1, where 1 = highly preferred)
    meal_weights: Dict[str, float] = Field(default_factory=dict, description="Meal timing preferences as weights (0-1, where 1=highly preferred). Example: {'breakfast': 0.8, 'lunch': 0.6, 'dinner': 0.9}")
    
    # Spice tolerance as normalized score (0-1)
    spice_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Spice tolerance level (0=mild, 1=very spicy). Example: 0.3 for mild, 0.8 for very spicy")
    
    # Alcohol preference as weight (0=no alcohol, 1=alcohol preferred)
    alcohol_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Alcohol preference (0=no alcohol, 1=alcohol preferred). Example: 0.0 for teetotaler, 0.7 for occasional drinker")
    
    # Avoidance weights (0-1, where 1 = completely avoid)
    avoids: Dict[str, float] = Field(default_factory=dict, description="Food items/restaurants to avoid (0=don't avoid, 1=completely avoid). Example: {'seafood': 1.0, 'spicy_food': 0.8}")
    
    # Additional ML features
    price_sensitivity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Price sensitivity (0=not price sensitive, 1=very price sensitive). Example: 0.2 for price-insensitive, 0.9 for very price-conscious")
    quality_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Quality preference (0=quantity over quality, 1=quality over quantity). Example: 0.1 for quantity-focused, 0.9 for quality-focused")
    authenticity_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Authenticity preference (0=fusion/modern ok, 1=authentic traditional only). Example: 0.3 for fusion-friendly, 0.9 for traditional-only")
    
    # Text data for NLP processing
    notes: str = Field(default="", description="Additional notes about food preferences")
    
    # Health and wellness preferences (0-1, where 1 = highly important)
    health_wellness: Dict[str, float] = Field(default_factory=dict, description="Health and wellness preferences (0=not important, 1=very important). Example: {'organic': 0.8, 'low_carb': 0.6, 'keto': 0.4}")
    discovery_patterns: Dict[str, float] = Field(default_factory=dict, description="Food discovery patterns (0=not applicable, 1=highly applicable). Example: {'foodie_adventurer': 0.9, 'comfort_food_seeker': 0.3}")
    
    # Additional behavioral scores
    nutritional_focus: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Nutritional focus (0=taste-focused, 1=nutrition-focused). Example: 0.2 for taste-first, 0.8 for health-first")
    culinary_curiosity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Culinary curiosity (0=stick to known foods, 1=try everything new). Example: 0.1 for conservative eater, 0.9 for adventurous foodie")
    
    # Meta & lifecycle
    schema_version: str = Field(default="1.0.0", description="Schema version for data compatibility and migration. Example: '1.0.0', '1.1.0'")
    updated_at: int = Field(default_factory=lambda: int(time.time()), description="Last update timestamp in Unix epoch. Example: 1695849600")
    data_freshness_days: int = Field(default=180, ge=1, le=3650, description="Data freshness threshold in days before preferences need refresh. Example: 180 for 6 months, 365 for 1 year")
    
    # Deterministic controls (search/ranking knobs)
    hard_excludes_place_types: List[str] = Field(default_factory=list, description="Hard exclusions for place types that should never appear. Example: ['bar', 'night_club'] for families")
    must_include_keywords: List[str] = Field(default_factory=list, description="Keywords that must be included in search queries. Example: ['ramen', 'udon'] to force Japanese noodle search")
    open_now_bias: float = Field(default=0.5, ge=0.0, le=1.0, description="Bias towards places that are currently open (0=ignore open status, 1=only open places). Example: 0.8 for immediate dining needs")
    queue_tolerance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Queue tolerance level (0=avoid queues completely, 1=don't mind waiting). Example: 0.1 for queue-averse, 0.8 for patient diner")
    max_distance_km: Optional[float] = Field(default=None, ge=0.1, le=100.0, description="Maximum distance willing to travel for food in kilometers. Example: 2.0 for local dining, 10.0 for destination restaurants")
    time_budget_per_meal_min: Optional[int] = Field(default=None, ge=5, le=300, description="Maximum time budget per meal in minutes. Example: 30 for quick lunch, 120 for leisurely dinner")
    
    # Budget & price
    meal_budget_pp_usd: Dict[str, float] = Field(default_factory=dict, description="Per-person meal budget in USD by meal type. Example: {'breakfast': 15, 'lunch': 25, 'dinner': 45}")
    tip_sensitivity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Tip sensitivity for US dining (0=not concerned, 1=very tip-conscious). Example: 0.3 for casual dining, 0.9 for fine dining")
    
    # Dietary & allergens (separate from general dietary_restriction_weights)
    allergen_avoidance: Dict[str, float] = Field(default_factory=dict, description="Allergen avoidance weights (0=no avoidance, 1=strict avoidance). Example: {'nuts': 1.0, 'shellfish': 0.8, 'dairy': 0.6}")
    religious_diet_weights: Dict[str, float] = Field(default_factory=dict, description="Religious dietary requirement weights (0=not required, 1=strict requirement). Example: {'halal': 1.0, 'kosher': 0.8, 'vegetarian_strict': 0.9}")
    
    # Experience & ambience
    ambience_weights: Dict[str, float] = Field(default_factory=dict, description="Ambience preference weights (0=not preferred, 1=highly preferred). Example: {'casual': 0.8, 'romantic': 0.3, 'family_friendly': 0.9}")
    seating_preferences: Dict[str, float] = Field(default_factory=dict, description="Seating preference weights (0=not preferred, 1=highly preferred). Example: {'outdoor': 0.7, 'booth': 0.6, 'private_room': 0.4}")
    noise_tolerance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Noise tolerance level (0=quiet only, 1=noise doesn't matter). Example: 0.2 for quiet dining, 0.8 for lively atmosphere")
    service_speed_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Service speed preference (0=fast casual pace, 1=tasting menu pace). Example: 0.2 for quick service, 0.8 for leisurely dining")
    
    # Modality & service
    service_mode_weights: Dict[str, float] = Field(default_factory=dict, description="Service mode preference weights (0=not preferred, 1=highly preferred). Example: {'dine_in': 0.9, 'takeout': 0.4, 'delivery': 0.2}")
    reservation_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Reservation preference (0=walk-in only, 1=prefers reservations). Example: 0.1 for spontaneous dining, 0.9 for planned meals")
    alcohol_style_weights: Dict[str, float] = Field(default_factory=dict, description="Alcohol style preference weights (0=not preferred, 1=highly preferred). Example: {'wine': 0.8, 'cocktails': 0.6, 'beer': 0.3}")
    
    # Brand & ingredient signals
    brand_weights: Dict[str, float] = Field(default_factory=dict, description="Brand/chain preference weights (0=avoid, 1=strongly prefer). Example: {'mcdonalds': 0.1, 'chipotle': 0.7, 'local_chef': 0.9}")
    ingredient_weights: Dict[str, float] = Field(default_factory=dict, description="Ingredient preference weights (0=avoid, 1=love). Example: {'cilantro': 0.0, 'truffle': 0.9, 'garlic': 0.8}")
    prep_method_weights: Dict[str, float] = Field(default_factory=dict, description="Cooking method preference weights (0=not preferred, 1=highly preferred). Example: {'grilled': 0.8, 'fried': 0.3, 'raw': 0.6}")
    
    # Time of day & cadence
    meal_time_windows: Dict[str, Tuple[int, int]] = Field(default_factory=dict, description="Preferred meal time windows as (start_hour, end_hour). Example: {'breakfast': (7, 10), 'dinner': (18, 21)}")
    snack_frequency: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Snack frequency likelihood (0=rarely snacks, 1=always snacks). Example: 0.2 for structured meals, 0.8 for frequent snacking")
    
    # Legacy fields for backward compatibility (will be computed from weights)
    @property
    def preferred_cuisines(self) -> List[CuisineType]:
        """Convert cuisine weights back to preferred cuisines list"""
        return [CuisineType(k) for k, v in self.cuisine_weights.items() if v > 0.5]
    
    @property
    def food_types(self) -> List[FoodType]:
        """Convert food type weights back to food types list"""
        return [FoodType(k) for k, v in self.food_type_weights.items() if v > 0.5]
    
    @property
    def budget_level(self) -> BudgetLevel:
        """Convert budget score back to budget level"""
        if self.budget_score is None:
            return BudgetLevel.MODERATE # Default for legacy if not set
        elif self.budget_score <= 0.33:
            return BudgetLevel.BUDGET
        elif self.budget_score <= 0.66:
            return BudgetLevel.MODERATE
        else:
            return BudgetLevel.LUXURY


class StayPreference(BaseModel):
    """Accommodation and lodging preferences with ML-optimized numerical representations"""
    # Accommodation type preferences as weights (0-1, where 1 = highly preferred)
    type_weights: Dict[str, float] = Field(default_factory=dict, description="Accommodation type preferences (0=not preferred, 1=highly preferred). Example: {'hotel': 0.8, 'hostel': 0.2, 'apartment': 0.6}")
    
    # Budget level as numerical score (0=budget, 0.5=moderate, 1=luxury)
    budget_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Budget level preference (0=budget, 0.5=moderate, 1=luxury). Example: 0.2 for budget hostels, 0.9 for luxury resorts")
    
    # Amenity preferences as weights (0-1, where 1 = highly important)
    amenity_weights: Dict[str, float] = Field(default_factory=dict, description="Amenity preferences (0=not important, 1=very important). Example: {'wifi': 0.9, 'pool': 0.4, 'gym': 0.6}")
    
    # Location preferences as weights (0-1, where 1 = highly preferred)
    location_weights: Dict[str, float] = Field(default_factory=dict, description="Location preferences (0=not preferred, 1=highly preferred). Example: {'city_center': 0.8, 'airport': 0.3, 'beachfront': 0.9}")
    
    # Room feature preferences as weights (0-1, where 1 = highly important)
    room_feature_weights: Dict[str, float] = Field(default_factory=dict, description="Room feature preferences (0=not important, 1=very important). Example: {'balcony': 0.7, 'kitchenette': 0.5, 'ocean_view': 0.9}")
    
    # Check-in/out time preferences (converted to numerical values)
    check_in_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Check-in time preference (0=early morning, 1=late evening). Example: 0.2 for 6 AM, 0.8 for 8 PM")
    check_out_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Check-out time preference (0=early morning, 1=late evening). Example: 0.3 for 9 AM, 0.9 for 11 PM")
    
    # Avoidance weights (0-1, where 1 = completely avoid)
    avoids: Dict[str, float] = Field(default_factory=dict, description="Accommodation types/features to avoid (0=don't avoid, 1=completely avoid). Example: {'noisy_areas': 0.9, 'shared_bathrooms': 0.7}")
    
    # Additional ML features
    comfort_level: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Comfort level preference (0=basic comfort, 1=luxury comfort). Example: 0.2 for basic, 0.8 for luxury")
    social_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Social preference (0=private/quiet, 1=social/communal). Example: 0.1 for private, 0.8 for social")
    flexibility: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Booking flexibility (0=strict dates, 1=flexible dates). Example: 0.2 for fixed dates, 0.8 for flexible")
    
    # Text data for NLP processing
    notes: str = Field(default="", description="Additional notes about accommodation preferences")
    
    # Technology and sustainability preferences (0-1, where 1 = highly important)
    technology_needs: Dict[str, float] = Field(default_factory=dict, description="Technology and connectivity needs (0=not important, 1=very important). Example: {'smart_room': 0.6, 'high_speed_wifi': 0.9, 'work_space': 0.7}")
    sustainability: Dict[str, float] = Field(default_factory=dict, description="Sustainability preferences (0=not important, 1=very important). Example: {'eco_friendly': 0.8, 'carbon_offset': 0.5, 'local_sourcing': 0.6}")
    
    # Additional behavioral scores
    connectivity_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Connectivity importance (0=not important, 1=critical). Example: 0.2 for leisure traveler, 0.9 for digital nomad")
    environmental_consciousness: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Environmental consciousness (0=not important, 1=very important). Example: 0.1 for eco-indifferent, 0.8 for eco-conscious")
    
    # Meta & lifecycle
    schema_version: str = Field(default="1.0.0", description="Schema version for data compatibility and migration. Example: '1.0.0', '1.1.0'")
    updated_at: int = Field(default_factory=lambda: int(time.time()), description="Last update timestamp in Unix epoch. Example: 1695849600")
    data_freshness_days: int = Field(default=180, ge=1, le=3650, description="Data freshness threshold in days before preferences need refresh. Example: 180 for 6 months, 365 for 1 year")
    
    # Deterministic controls
    hard_excludes_place_types: List[str] = Field(default_factory=list, description="Hard exclusions for place types that should never appear. Example: ['rv_park', 'campground'] for hotel-only stays")
    must_include_place_types: List[str] = Field(default_factory=list, description="Required place types that must be included. Example: ['lodging'] for standard stays, ['spa_resort'] for luxury")
    required_amenities: List[str] = Field(default_factory=list, description="Hard must-have amenities separate from weights. Example: ['wifi', 'parking', 'gym']")
    
    # Budget & quality guardrails
    nightly_budget_usd: Optional[Tuple[float, float]] = Field(default=None, description="Nightly budget range in USD as (min, max). Example: (100.0, 300.0) for mid-range stays")
    star_class_min: Optional[int] = Field(default=None, ge=1, le=5, description="Minimum star class requirement. Example: 3 for mid-range, 5 for luxury only")
    review_score_min: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Minimum review score requirement (0-10 scale). Example: 4.2 for good reviews, 8.5 for excellent")
    
    # Occupancy & family needs
    adult_count: Optional[int] = Field(default=None, ge=1, le=20, description="Number of adults staying. Example: 2 for couple, 4 for family")
    child_ages: List[int] = Field(default_factory=list, description="Ages of children staying (for family-friendly amenities). Example: [5, 8, 12] for family with kids")
    bed_config_weights: Dict[str, float] = Field(default_factory=dict, description="Bed configuration preference weights (0=not preferred, 1=highly preferred). Example: {'king': 0.8, 'twin': 0.3, 'sofa_bed': 0.5}")
    crib_needed: bool = Field(default=False, description="Whether crib/baby bed is needed. Example: True for families with infants")
    room_count_min: Optional[int] = Field(default=None, ge=1, le=10, description="Minimum number of rooms needed. Example: 2 for family requiring separate rooms")
    
    # Accessibility & quiet
    accessibility_requirements: Dict[str, float] = Field(default_factory=dict, description="Accessibility requirement weights (0=not needed, 1=essential). Example: {'elevator': 1.0, 'step_free': 0.8, 'roll_in_shower': 0.9}")
    noise_tolerance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Noise tolerance level (0=quiet only, 1=noise doesn't matter). Example: 0.2 for light sleepers, 0.8 for noise-tolerant")
    floor_preference: Dict[str, float] = Field(default_factory=dict, description="Floor preference weights (0=not preferred, 1=highly preferred). Example: {'high_floor': 0.7, 'low_floor': 0.3}")
    
    # Location/proximity
    preferred_neighborhood_tags: Dict[str, float] = Field(default_factory=dict, description="Neighborhood preference weights (0=not preferred, 1=highly preferred). Example: {'quiet': 0.8, 'nightlife': 0.2, 'near_metro': 0.9}")
    max_walk_time_to_transit_min: Optional[int] = Field(default=None, ge=1, le=60, description="Maximum walking time to transit in minutes. Example: 10 for transit-dependent travelers")
    max_distance_to_anchor_km: Optional[float] = Field(default=None, ge=0.1, le=50.0, description="Maximum distance to anchor point (conference, family) in km. Example: 2.0 for conference attendees")
    
    # Check-in/out & policy tolerance
    early_checkin_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Early check-in importance (0=not important, 1=critical). Example: 0.8 for early arrivals")
    late_checkout_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Late checkout importance (0=not important, 1=critical). Example: 0.6 for late departures")
    cancellation_flex_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Cancellation flexibility preference (0=strict ok, 1=flexible required). Example: 0.9 for uncertain plans")
    prepay_tolerance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Prepayment tolerance (0=avoid prepay, 1=prepay ok). Example: 0.3 for flexible payment, 0.8 for budget-conscious")
    deposit_tolerance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Deposit tolerance (0=avoid deposits, 1=deposits ok). Example: 0.2 for deposit-averse, 0.7 for deposit-tolerant")
    self_checkin_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Self check-in preference (0=front desk only, 1=self check-in preferred). Example: 0.8 for contactless travelers")
    front_desk_24h_importance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="24-hour front desk importance (0=not needed, 1=essential). Example: 0.6 for late arrivals")
    
    # Brand/loyalty & channels
    brand_weights: Dict[str, float] = Field(default_factory=dict, description="Hotel brand preference weights (0=avoid, 1=strongly prefer). Example: {'marriott': 0.8, 'hyatt': 0.6, 'airbnb': 0.3}")
    loyalty_levels: Dict[str, int] = Field(default_factory=dict, description="Loyalty program tier levels (program → tier). Example: {'marriott_bonvoy': 3, 'hilton_hhonors': 2}")
    points_optimization_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Points optimization importance (0=price first, 1=points first). Example: 0.7 for points collectors")
    booking_channel_weights: Dict[str, float] = Field(default_factory=dict, description="Booking channel preference weights (0=not preferred, 1=highly preferred). Example: {'direct': 0.9, 'expedia': 0.4, 'booking.com': 0.5}")
    
    # Stay strategy
    stay_cadence_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Stay cadence preference (0=one base hotel, 1=hotel-hopping). Example: 0.2 for base camp style, 0.8 for variety seeking")
    housekeeping_frequency_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Housekeeping frequency preference (0=daily, 1=minimal). Example: 0.3 for daily service, 0.8 for privacy")
    kitchen_requirement: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Kitchen requirement level (0=not needed, 1=essential). Example: 0.2 for dining out, 0.9 for cooking needs")
    parking_requirement: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Parking requirement level (0=not needed, 1=essential). Example: 0.1 for city travelers, 0.9 for road trippers")
    pet_friendly_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Pet-friendly accommodation preference (0=not needed, 1=essential). Example: 0.9 for pet owners")
    smoking_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Smoking accommodation preference (0=non-smoking only, 1=smoking ok). Example: 0.0 for non-smokers, 0.8 for smokers")
    
    # Legacy fields for backward compatibility
    @property
    def preferred_types(self) -> List[StayType]:
        """Convert type weights back to preferred types list"""
        return [StayType(k) for k, v in self.type_weights.items() if v > 0.5]
    
    @property
    def budget_level(self) -> BudgetLevel:
        """Convert budget score back to budget level"""
        if self.budget_score is None:
            return BudgetLevel.MODERATE # Default for legacy if not set
        elif self.budget_score <= 0.33:
            return BudgetLevel.BUDGET
        elif self.budget_score <= 0.66:
            return BudgetLevel.MODERATE
        else:
            return BudgetLevel.LUXURY
    
    @property
    def check_in_time(self) -> Optional[str]:
        """Convert check-in preference to time string"""
        if self.check_in_preference is None:
            return None
        hour = int(self.check_in_preference * 24)
        return f"{hour:02d}:00"
    
    @property
    def check_out_time(self) -> Optional[str]:
        """Convert check-out preference to time string"""
        if self.check_out_preference is None:
            return None
        hour = int(self.check_out_preference * 24)
        return f"{hour:02d}:00"


class TravelPreference(BaseModel):
    """Travel and activity preferences with ML-optimized numerical representations"""
    # Travel style preferences as weights (0-1, where 1 = highly preferred)
    travel_style_weights: Dict[str, float] = Field(default_factory=dict, description="Travel style preferences (0=not preferred, 1=highly preferred). Example: {'adventure': 0.9, 'relaxation': 0.3, 'cultural': 0.7}")
    
    # Transportation mode preferences as weights (0-1, where 1 = highly preferred)
    transport_weights: Dict[str, float] = Field(default_factory=dict, description="Transportation mode preferences (0=not preferred, 1=highly preferred). Example: {'walking': 0.8, 'public_transport': 0.6, 'rental_car': 0.4}")
    
    # Activity type preferences as weights (0-1, where 1 = highly preferred)
    activity_weights: Dict[str, float] = Field(default_factory=dict, description="Activity type preferences (0=not preferred, 1=highly preferred). Example: {'museums': 0.8, 'nightlife': 0.3, 'outdoor': 0.9}")
    
    # Budget level as numerical score (0=budget, 0.5=moderate, 1=luxury)
    budget_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Budget level preference (0=budget, 0.5=moderate, 1=luxury). Example: 0.2 for backpacker, 0.8 for luxury traveler")
    
    # Group size preference (normalized 0-1)
    group_size_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Group size preference (0=solo travel, 1=large group travel). Example: 0.1 for solo, 0.8 for group traveler")
    
    # Duration preferences as numerical values
    min_duration_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum trip duration (0=1 day, 1=30+ days). Example: 0.1 for weekend trips, 0.8 for long-term travel")
    max_duration_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Maximum trip duration (0=1 day, 1=30+ days). Example: 0.3 for short trips, 0.9 for extended travel")
    preferred_duration: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Preferred trip duration (0=1 day, 1=30+ days). Example: 0.2 for quick getaways, 0.7 for extended vacations")
    
    # Season preferences as weights (0-1, where 1 = highly preferred)
    season_weights: Dict[str, float] = Field(default_factory=dict, description="Season preferences (0=not preferred, 1=highly preferred). Example: {'summer': 0.8, 'winter': 0.3, 'spring': 0.6}")
    
    # Weather preferences as numerical values
    rain_tolerance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Rain tolerance (0=avoid completely, 1=don't mind rain). Example: 0.1 for rain-averse, 0.8 for rain-tolerant")
    sun_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Sun preference (0=avoid sun, 1=prefer sunny weather). Example: 0.2 for sun-averse, 0.9 for sun-seeker")
    min_temperature_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum temperature preference (0=cold, 1=hot). Example: 0.2 for cold-weather lover, 0.8 for warm-weather seeker")
    max_temperature_preference: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Maximum temperature preference (0=cold, 1=hot). Example: 0.3 for cool climate, 0.9 for hot climate")
    
    # Accessibility needs as weights (0-1, where 1 = highly important)
    accessibility_weights: Dict[str, float] = Field(default_factory=dict, description="Accessibility needs (0=not needed, 1=essential). Example: {'wheelchair_accessible': 1.0, 'elevator': 0.8}")
    
    # Language preferences as weights (0-1, where 1 = highly preferred)
    language_weights: Dict[str, float] = Field(default_factory=dict, description="Language preferences (0=not preferred, 1=highly preferred). Example: {'english': 0.9, 'spanish': 0.4, 'french': 0.3}")
    
    # Adventure and Safety Preferences (normalized to 0-1)
    adventure_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Adventure level preference (0=very safe, 1=extreme adventure). Example: 0.2 for safety-first, 0.9 for thrill-seeker")
    physical_fitness_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Physical fitness level (0=poor fitness, 1=excellent fitness). Example: 0.3 for low fitness, 0.8 for high fitness")
    medical_consideration_weights: Dict[str, float] = Field(default_factory=dict, description="Medical considerations (0=not applicable, 1=highly applicable). Example: {'motion_sickness': 0.8, 'allergies': 0.6}")
    
    # Activity preferences as weights (0-1, where 1 = highly preferred)
    activity_preference_weights: Dict[str, float] = Field(default_factory=dict, description="Activity preferences (0=not preferred, 1=highly preferred). Example: {'hiking': 0.9, 'shopping': 0.2, 'photography': 0.7}")
    
    # Avoidance weights (0-1, where 1 = completely avoid)
    avoids: Dict[str, float] = Field(default_factory=dict, description="Activities to avoid (0=don't avoid, 1=completely avoid). Example: {'crowds': 0.9, 'heights': 0.7, 'water_activities': 0.8}")
    
    # Text data for NLP processing
    notes: str = Field(default="", description="Additional notes about travel preferences")
    
    # Temporal and behavioral preferences (0-1, where 1 = highly applicable)
    temporal_preferences: Dict[str, float] = Field(default_factory=dict, description="Time-based preferences (0=not applicable, 1=highly applicable). Example: {'morning_person': 0.8, 'weekend_traveler': 0.6}")
    social_dynamics: Dict[str, float] = Field(default_factory=dict, description="Social interaction patterns (0=not applicable, 1=highly applicable). Example: {'solo_comfort': 0.9, 'group_leadership': 0.3}")
    risk_profile: Dict[str, float] = Field(default_factory=dict, description="Risk tolerance patterns (0=not applicable, 1=highly applicable). Example: {'safety_first': 0.9, 'off_beat_destinations': 0.2}")
    cultural_adaptation: Dict[str, float] = Field(default_factory=dict, description="Cultural adaptation patterns (0=not applicable, 1=highly applicable). Example: {'local_customs_respect': 0.8, 'language_barrier_comfort': 0.4}")
    
    # Additional behavioral scores
    spontaneity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Spontaneity preference (0=highly planned, 1=very spontaneous). Example: 0.2 for planner, 0.8 for spontaneous")
    social_interaction: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Social interaction preference (0=solitary travel, 1=social travel). Example: 0.1 for solitary, 0.9 for social")
    cultural_immersion: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Cultural immersion preference (0=tourist experience, 1=local experience). Example: 0.3 for tourist, 0.8 for local experience")
    photo_orientation: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Photo/documentation importance (0=not important, 1=very important). Example: 0.2 for casual, 0.9 for photography-focused")
    
    # Queue and walking preferences
    queue_tolerance: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Queue tolerance level (0=avoid queues completely, 1=don't mind waiting). Example: 0.1 for queue-averse, 0.8 for patient traveler")
    daily_walk_km_target: Optional[float] = Field(default=None, ge=0.0, le=50.0, description="Daily walking distance target in kilometers (0=no walking, 50=very active). Example: 2.0 for light walker, 15.0 for hiking enthusiast")
    
    # Schema version for data migration and compatibility
    schema_version: Optional[str] = Field(default=None, description="Schema version for data compatibility and migration. Example: '1.0.0', '1.1.0'")
    
    # Legacy fields for backward compatibility
    @property
    def travel_style(self) -> Optional[TravelStyle]:
        """Convert travel style weights back to primary travel style"""
        if not self.travel_style_weights:
            return None
        max_style = max(self.travel_style_weights.items(), key=lambda x: x[1])
        return TravelStyle(max_style[0])
    
    @property
    def preferred_transport(self) -> List[TransportMode]:
        """Convert transport weights back to preferred transport modes"""
        return [TransportMode(k) for k, v in self.transport_weights.items() if v > 0.5]
    
    @property
    def activity_interests(self) -> List[ActivityType]:
        """Convert activity weights back to activity interests"""
        return [ActivityType(k) for k, v in self.activity_weights.items() if v > 0.5]
    
    @property
    def budget_level(self) -> Optional[BudgetLevel]:
        """Convert budget score back to budget level"""
        if self.budget_score is None:
            return None
        elif self.budget_score <= 0.33:
            return BudgetLevel.BUDGET
        elif self.budget_score <= 0.66:
            return BudgetLevel.MODERATE
        else:
            return BudgetLevel.LUXURY
    
    @property
    def group_size(self) -> Optional[int]:
        """Convert group size preference back to integer"""
        if self.group_size_preference is None:
            return None
        return max(1, int(self.group_size_preference * 20))
    
    @property
    def duration_preference(self) -> Dict[str, Optional[int]]:
        """Convert duration preferences back to dictionary"""
        return {
            "min_days": max(1, int(self.min_duration_preference * 30)) if self.min_duration_preference is not None else None,
            "max_days": max(1, int(self.max_duration_preference * 30)) if self.max_duration_preference is not None else None,
            "preferred_days": max(1, int(self.preferred_duration * 30)) if self.preferred_duration is not None else None
        }
    
    @property
    def season_preferences(self) -> List[str]:
        """Convert season weights back to preferred seasons"""
        return [season for season, weight in self.season_weights.items() if weight > 0.5]
    
    @property
    def weather_preferences(self) -> Dict[str, Any]:
        """Convert weather preferences back to dictionary"""
        return {
            "avoid_rain": self.rain_tolerance is not None and self.rain_tolerance < 0.3,
            "prefer_sunny": self.sun_preference is not None and self.sun_preference > 0.7,
            "temperature_range": {
                "min": int(self.min_temperature_preference * 40 - 10) if self.min_temperature_preference is not None else None,  # -10 to 30°C
                "max": int(self.max_temperature_preference * 40 - 10) if self.max_temperature_preference is not None else None
            }
        }
    
    @property
    def accessibility_needs(self) -> List[str]:
        """Convert accessibility weights back to needs list"""
        return [need for need, weight in self.accessibility_weights.items() if weight > 0.5]
    
    @property
    def language_preferences(self) -> List[str]:
        """Convert language weights back to preferences list"""
        return [lang for lang, weight in self.language_weights.items() if weight > 0.5]
    
    @property
    def adventure_level(self) -> Optional[int]:
        """Convert adventure score back to 1-5 scale"""
        if self.adventure_score is None:
            return None
        return max(1, min(5, int(self.adventure_score * 5) + 1))
    
    @property
    def physical_fitness_level(self) -> Optional[int]:
        """Convert fitness score back to 1-5 scale"""
        if self.physical_fitness_score is None:
            return None
        return max(1, min(5, int(self.physical_fitness_score * 5) + 1))
    
    @property
    def medical_considerations(self) -> List[str]:
        """Convert medical consideration weights back to list"""
        return [consideration for consideration, weight in self.medical_consideration_weights.items() if weight > 0.5]
    
    @property
    def preferred_activities(self) -> List[str]:
        """Convert activity preference weights back to list"""
        return [activity for activity, weight in self.activity_preference_weights.items() if weight > 0.5]
    
    def get_travel_preference(self, include_empty: bool = False) -> Dict[str, Any]:
        """
        Get travel preference data as dictionary
        
        Args:
            include_empty: If True, include fields with None/empty values. If False, omit them.
            
        Returns:
            Dictionary representation of travel preferences
        """
        data = self.model_dump()
        
        if include_empty:
            return data
        
        # Filter out None values and empty collections
        filtered_data = {}
        
        for key, value in data.items():
            # Skip None values
            if value is None:
                continue
                
            # Skip empty dictionaries and lists
            if isinstance(value, (dict, list)) and len(value) == 0:
                continue
                
            # Skip empty strings
            if isinstance(value, str) and value == "":
                continue
                
            filtered_data[key] = value
        
        return filtered_data


class UserPreference(BaseModel):
    """Complete user preference profile with ML-optimized numerical representations"""
    user_id: str
    version: str = "1.0.0"
    food: FoodPreference = Field(default_factory=FoodPreference)
    stay: StayPreference = Field(default_factory=StayPreference)
    travel: TravelPreference = Field(default_factory=TravelPreference)
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    
    # Additional ML metadata
    preference_completeness: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Completeness score of user preferences")
    last_ml_update: Optional[int] = Field(default=None, description="Last time preferences were updated by ML")
    
    # Cross-category behavioral attributes (0-1, where 1 = highly applicable)
    decision_patterns: Dict[str, float] = Field(default_factory=dict, description="Decision-making patterns (0=not applicable, 1=highly applicable). Example: {'impulsive_booker': 0.7, 'research_intensive': 0.8}")
    experience_convenience: Dict[str, float] = Field(default_factory=dict, description="Experience vs convenience trade-offs (0=not applicable, 1=highly applicable). Example: {'authentic_experience': 0.9, 'tourist_comfort': 0.2}")
    value_perception: Dict[str, float] = Field(default_factory=dict, description="Value perception patterns (0=not applicable, 1=highly applicable). Example: {'value_seeker': 0.8, 'premium_payer': 0.3}")
    
    # Global search controls
    must_include_keywords: List[str] = Field(default_factory=list, description="Global keywords that must be included in all search queries. Example: ['family_friendly', 'accessible', 'pet_friendly']")
    
    # Additional behavioral scores
    decision_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Decision-making confidence (0=very hesitant, 1=very confident). Example: 0.3 for indecisive, 0.9 for decisive")
    experience_orientation: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Experience orientation (0=convenience-focused, 1=authentic experience-focused). Example: 0.2 for convenience-first, 0.8 for experience-first")
    quality_sensitivity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Quality sensitivity (0=price-focused, 1=quality-focused). Example: 0.2 for price-sensitive, 0.9 for quality-focused")

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "version": self.version,
            "food": self.food.model_dump(),
            "stay": self.stay.model_dump(),
            "travel": self.travel.model_dump(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "preference_completeness": self.preference_completeness,
            "last_ml_update": self.last_ml_update
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreference":
        """Create from dictionary (database data)"""
        return cls(
            user_id=data["user_id"],
            version=data.get("version", "1.0.0"),
            food=FoodPreference(**data.get("food", {})),
            stay=StayPreference(**data.get("stay", {})),
            travel=TravelPreference(**data.get("travel", {})),
            created_at=data.get("created_at", int(time.time())),
            updated_at=data.get("updated_at", int(time.time())),
            preference_completeness=data.get("preference_completeness"),
            last_ml_update=data.get("last_ml_update")
        )

    
    def get_travel_preference(self, include_empty: bool = False) -> Dict[str, Any]:
        """
        Get travel preference data from this user preference
        
        Args:
            include_empty: If True, include fields with None/empty values. If False, omit them.
            
        Returns:
            Dictionary representation of travel preferences
        """
        return self.travel.get_travel_preference(include_empty=include_empty)

