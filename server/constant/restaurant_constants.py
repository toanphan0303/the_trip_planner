"""
Constants for restaurant detection and categorization
"""

# Keywords that indicate a place is a restaurant or food establishment
RESTAURANT_KEYWORDS = [
    'restaurant', 'food', 'dining', 'cafe', 'coffee', 'bar', 'pub',
    'bistro', 'eatery', 'diner', 'grill', 'kitchen', 'cuisine',
    'bakery', 'delivery', 'takeaway', 'fast_food', 'buffet', 'cafeteria',
    'deli', 'dessert', 'ice_cream', 'pizza', 'sandwich', 'burger',
    'ramen', 'sushi', 'steak', 'seafood', 'wine', 'tea', 'juice',
    'chocolate', 'candy', 'confectionery', 'brunch', 'breakfast'
]

# Google Places types that represent restaurants
RESTAURANT_PLACE_TYPES = [
    'restaurant', 'meal_takeaway', 'meal_delivery', 'cafe', 'bar',
    'acai_shop', 'afghani_restaurant', 'african_restaurant', 'american_restaurant',
    'asian_restaurant', 'bagel_shop', 'bakery', 'bar_and_grill', 'barbecue_restaurant',
    'brazilian_restaurant', 'breakfast_restaurant', 'brunch_restaurant', 'buffet_restaurant',
    'cafeteria', 'candy_store', 'cat_cafe', 'chinese_restaurant', 'chocolate_factory',
    'chocolate_shop', 'coffee_shop', 'confectionery', 'deli', 'dessert_restaurant',
    'dessert_shop', 'diner', 'dog_cafe', 'donut_shop', 'fast_food_restaurant',
    'fine_dining_restaurant', 'food_court', 'french_restaurant', 'greek_restaurant',
    'hamburger_restaurant', 'ice_cream_shop', 'indian_restaurant', 'indonesian_restaurant',
    'italian_restaurant', 'japanese_restaurant', 'juice_shop', 'korean_restaurant',
    'lebanese_restaurant', 'mediterranean_restaurant', 'mexican_restaurant',
    'middle_eastern_restaurant', 'pizza_restaurant', 'pub', 'ramen_restaurant',
    'sandwich_shop', 'seafood_restaurant', 'spanish_restaurant', 'steak_house',
    'sushi_restaurant', 'tea_house', 'thai_restaurant', 'turkish_restaurant',
    'vegan_restaurant', 'vegetarian_restaurant', 'vietnamese_restaurant', 'wine_bar'
]

# Yelp categories that represent restaurants  
YELP_RESTAURANT_CATEGORIES = [
    "restaurants", "food", "cafes", "coffee", "bars"
]
