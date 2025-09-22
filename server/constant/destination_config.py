"""
Destination Classification and Search Configuration
Replaces hardcoded values in cluster_locations.py with configurable system
"""

from typing import List, Dict
from enum import Enum


class DestinationType(Enum):
    """Types of destinations for classification"""
    MAJOR_CITY = "major_city"
    TOURIST_DESTINATION = "tourist_destination"
    ISLAND_RESORT = "island_resort"
    SMALL_TOWN = "small_town"
    METROPOLITAN_AREA = "metropolitan_area"
    CULTURAL_CENTER = "cultural_center"
    BUSINESS_CENTER = "business_center"
    NATURAL_AREA = "natural_area"
    HISTORIC_SITE = "historic_site"
    DEFAULT = "default"


class DestinationClassification:
    """Configuration for destination classification and search parameters"""
    
    # Major cities and tourist destinations (higher diversity factor)
    MAJOR_DESTINATIONS: List[str] = [
        # Global Capitals
        "tokyo", "london", "paris", "new york", "los angeles", "chicago",
        "moscow", "beijing", "shanghai", "mumbai", "delhi", "mexico city",
        "sao paulo", "buenos aires", "sydney", "melbourne", "toronto",
        "vancouver", "miami", "houston", "phoenix", "philadelphia",
        "san antonio", "san diego", "dallas", "san jose", "austin",
        "seattle", "denver", "washington", "boston", "nashville", "baltimore",
        "portland", "las vegas", "milwaukee", "atlanta", "long beach",
        
        # European Cities
        "rome", "barcelona", "madrid", "berlin", "amsterdam", "vienna",
        "prague", "budapest", "copenhagen", "stockholm", "oslo", "helsinki",
        "zurich", "brussels", "munich", "frankfurt", "hamburg", "cologne",
        "milan", "florence", "venice", "naples", "lisbon", "porto",
        "athens", "thessaloniki", "warsaw", "krakow", "bucharest", "sofia",
        
        # Asian Cities
        "dubai", "singapore", "hong kong", "bangkok", "kuala lumpur",
        "jakarta", "manila", "seoul", "taipei", "osaka", "kyoto",
        "ho chi minh city", "hanoi", "phnom penh", "vientiane", "yangon",
        "dhaka", "karachi", "lahore", "islamabad", "kathmandu", "thimphu",
        
        # African Cities
        "cairo", "alexandria", "casablanca", "marrakech", "tunis",
        "algiers", "lagos", "abuja", "accra", "nairobi", "addis ababa",
        "cape town", "johannesburg", "durban", "pretoria",
        
        # South American Cities
        "lima", "bogota", "caracas", "quito", "guayaquil", "la paz",
        "santiago", "valparaiso", "montevideo", "asuncion",
        
        # North American Cities
        "montreal", "quebec city", "calgary", "edmonton", "winnipeg",
        "ottawa", "halifax", "st. john's", "victoria", "windsor",
        
        # Australian Cities
        "perth", "adelaide", "brisbane", "gold coast", "newcastle",
        "wollongong", "hobart", "darwin", "canberra"
    ]
    
    # Tourist-related keywords (moderate diversity factor)
    TOURIST_KEYWORDS: List[str] = [
        "capital", "metropolitan", "city", "downtown", "center", "central",
        "tourist", "attraction", "historic", "cultural", "museum", "gallery",
        "heritage", "monument", "palace", "cathedral", "temple", "shrine",
        "festival", "carnival", "exhibition", "convention", "conference",
        "university", "college", "campus", "research", "institute"
    ]
    
    # Island and resort keywords (lower diversity factor)
    ISLAND_RESORT_KEYWORDS: List[str] = [
        "island", "isle", "beach", "resort", "coast", "bay", "harbor",
        "peninsula", "archipelago", "atoll", "coral", "lagoon", "cove",
        "shore", "seaside", "waterfront", "marina", "port", "dock",
        "tropical", "paradise", "retreat", "spa", "wellness", "relaxation"
    ]
    
    # Small town keywords (lower diversity factor)
    SMALL_TOWN_KEYWORDS: List[str] = [
        "village", "hamlet", "town", "small", "little", "tiny", "mini",
        "rural", "countryside", "farm", "ranch", "settlement", "community",
        "neighborhood", "district", "borough", "municipality", "county"
    ]
    
    # Cultural center keywords (higher diversity factor)
    CULTURAL_KEYWORDS: List[str] = [
        "cultural", "art", "music", "theater", "opera", "ballet", "dance",
        "literature", "poetry", "philosophy", "academic", "scholarly",
        "creative", "artistic", "bohemian", "avant-garde", "experimental"
    ]
    
    # Business center keywords (moderate diversity factor)
    BUSINESS_KEYWORDS: List[str] = [
        "business", "financial", "commercial", "corporate", "headquarters",
        "office", "tower", "plaza", "center", "district", "quarter",
        "industrial", "manufacturing", "technology", "innovation", "startup"
    ]
    
    # Natural area keywords (moderate diversity factor)
    NATURAL_KEYWORDS: List[str] = [
        "national park", "forest", "mountain", "lake", "river", "valley",
        "desert", "canyon", "cliff", "peak", "summit", "trail", "hiking",
        "camping", "wildlife", "nature", "conservation", "reserve", "sanctuary"
    ]
    
    # Historic site keywords (higher diversity factor)
    HISTORIC_KEYWORDS: List[str] = [
        "historic", "historical", "ancient", "medieval", "renaissance",
        "colonial", "victorian", "gothic", "baroque", "romanesque",
        "archaeological", "ruins", "fortress", "castle", "citadel",
        "monastery", "abbey", "church", "cathedral", "basilica", "mosque",
        "synagogue", "temple", "pagoda", "stupa", "shrine"
    ]
    
    # Diversity factors for different destination types
    DIVERSITY_FACTORS: Dict[DestinationType, float] = {
        DestinationType.MAJOR_CITY: 1.5,           # 50% more results
        DestinationType.TOURIST_DESTINATION: 1.3,  # 30% more results
        DestinationType.CULTURAL_CENTER: 1.4,      # 40% more results
        DestinationType.HISTORIC_SITE: 1.3,        # 30% more results
        DestinationType.METROPOLITAN_AREA: 1.2,    # 20% more results
        DestinationType.BUSINESS_CENTER: 1.1,      # 10% more results
        DestinationType.NATURAL_AREA: 1.0,         # Default
        DestinationType.ISLAND_RESORT: 0.8,        # 20% fewer results
        DestinationType.SMALL_TOWN: 0.7,           # 30% fewer results
        DestinationType.DEFAULT: 1.0               # Default
    }
    
    @classmethod
    def classify_destination(cls, destination_name: str) -> DestinationType:
        """
        Classify a destination based on its name and keywords.
        
        Args:
            destination_name: Name of the destination to classify
            
        Returns:
            DestinationType enum value
        """
        if not destination_name:
            return DestinationType.DEFAULT
        
        destination_lower = destination_name.lower()
        
        # Check for major destinations first (highest priority)
        for major_dest in cls.MAJOR_DESTINATIONS:
            if major_dest in destination_lower:
                return DestinationType.MAJOR_CITY
        
        # Check for cultural centers
        for keyword in cls.CULTURAL_KEYWORDS:
            if keyword in destination_lower:
                return DestinationType.CULTURAL_CENTER
        
        # Check for historic sites
        for keyword in cls.HISTORIC_KEYWORDS:
            if keyword in destination_lower:
                return DestinationType.HISTORIC_SITE
        
        # Check for tourist destinations
        for keyword in cls.TOURIST_KEYWORDS:
            if keyword in destination_lower:
                return DestinationType.TOURIST_DESTINATION
        
        # Check for business centers
        for keyword in cls.BUSINESS_KEYWORDS:
            if keyword in destination_lower:
                return DestinationType.BUSINESS_CENTER
        
        # Check for natural areas
        for keyword in cls.NATURAL_KEYWORDS:
            if keyword in destination_lower:
                return DestinationType.NATURAL_AREA
        
        # Check for island/resort destinations
        for keyword in cls.ISLAND_RESORT_KEYWORDS:
            if keyword in destination_lower:
                return DestinationType.ISLAND_RESORT
        
        # Check for small towns
        for keyword in cls.SMALL_TOWN_KEYWORDS:
            if keyword in destination_lower:
                return DestinationType.SMALL_TOWN
        
        # Default classification
        return DestinationType.DEFAULT
    
    @classmethod
    def get_diversity_factor(cls, destination_name: str) -> float:
        """
        Get diversity factor for a destination based on its classification.
        
        Args:
            destination_name: Name of the destination
            
        Returns:
            Diversity factor multiplier
        """
        destination_type = cls.classify_destination(destination_name)
        return cls.DIVERSITY_FACTORS.get(destination_type, 1.0)
    
    @classmethod
    def get_search_types_for_destination(cls, destination_name: str) -> List[str]:
        """
        Get appropriate search types for a destination based on its classification.
        
        Args:
            destination_name: Name of the destination
            
        Returns:
            List of place types to search for
        """
        destination_type = cls.classify_destination(destination_name)
        
        # Base types for all destinations
        base_types = ["tourist_attraction", "restaurant", "cafe"]
        
        # Add destination-specific types
        if destination_type == DestinationType.CULTURAL_CENTER:
            base_types.extend(["museum", "art_gallery", "theater"])
        elif destination_type == DestinationType.HISTORIC_SITE:
            base_types.extend(["museum", "tourist_attraction"])
        elif destination_type == DestinationType.NATURAL_AREA:
            base_types.extend(["park", "natural_feature"])
        elif destination_type == DestinationType.ISLAND_RESORT:
            base_types.extend(["beach", "resort", "park"])
        elif destination_type == DestinationType.BUSINESS_CENTER:
            base_types.extend(["shopping_mall", "hotel"])
        
        # Remove duplicates and return
        return list(set(base_types))
    
    @classmethod
    def get_num_search_types(cls, destination_name: str) -> int:
        """
        Get the number of search types for a destination.
        
        Args:
            destination_name: Name of the destination
            
        Returns:
            Number of search types
        """
        search_types = cls.get_search_types_for_destination(destination_name)
        return len(search_types)


class SearchConfiguration:
    """Configuration for search parameters and place types"""
    
    # Default search types for trip planning
    DEFAULT_SEARCH_TYPES: List[str] = [
        "tourist_attraction",
        "restaurant", 
        "cafe"
    ]
    
    # Extended search types for comprehensive coverage
    EXTENDED_SEARCH_TYPES: List[str] = [
        "tourist_attraction",
        "restaurant",
        "cafe",
        "museum",
        "park",
        "shopping_mall",
        "lodging"
    ]
    
    # Cultural destination search types
    CULTURAL_SEARCH_TYPES: List[str] = [
        "museum",
        "art_gallery",
        "tourist_attraction",
        "restaurant",
        "cafe",
        "theater",
        "library"
    ]
    
    # Natural destination search types
    NATURAL_SEARCH_TYPES: List[str] = [
        "park",
        "natural_feature",
        "tourist_attraction",
        "restaurant",
        "cafe",
        "lodging"
    ]
    
    # Business destination search types
    BUSINESS_SEARCH_TYPES: List[str] = [
        "restaurant",
        "cafe",
        "shopping_mall",
        "lodging",
        "tourist_attraction",
        "bank",
        "atm"
    ]
    
    @classmethod
    def get_search_types(cls, destination_name: str = None) -> List[str]:
        """
        Get search types based on destination classification.
        
        Args:
            destination_name: Name of the destination (optional)
            
        Returns:
            List of place types to search for
        """
        if not destination_name:
            return cls.DEFAULT_SEARCH_TYPES
        
        return DestinationClassification.get_search_types_for_destination(destination_name)
    
    @classmethod
    def get_num_search_types(cls, destination_name: str = None) -> int:
        """
        Get number of search types for a destination.
        
        Args:
            destination_name: Name of the destination (optional)
            
        Returns:
            Number of search types
        """
        return len(cls.get_search_types(destination_name))


# Convenience functions for backward compatibility
def get_destination_diversity_factor(destination_name: str) -> float:
    """Get diversity factor for a destination"""
    return DestinationClassification.get_diversity_factor(destination_name)

def get_search_types_for_destination(destination_name: str) -> List[str]:
    """Get search types for a destination"""
    return SearchConfiguration.get_search_types(destination_name)

def get_num_search_types_for_destination(destination_name: str) -> int:
    """Get number of search types for a destination"""
    return SearchConfiguration.get_num_search_types(destination_name)
