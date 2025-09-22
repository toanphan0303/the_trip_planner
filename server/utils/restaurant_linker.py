"""
Restaurant linking service to connect Google Places restaurants with Yelp data
"""

from typing import Optional, Dict, List, Tuple
from service_api.google_api import GoogleAPI
from service_api.yelp_api import YelpAPI
from service_api.fourquare_api import FoursquareAPI
from models.point_of_interest_models import PointOfInterest, Source
from models.yelp_model import YelpPointOfInterest
from utils.radius import haversine_m
from utils.restaurant_utils import is_restaurant, normalize_restaurant_name
import re


class RestaurantLinker:
    """
    Service to link Google Places restaurants with corresponding Yelp businesses
    """
    
    def __init__(self):
        self.google_api = GoogleAPI()
        self.yelp_api = YelpAPI()
        
        # Initialize Foursquare API only if API key is available
        try:
            self.foursquare_api = FoursquareAPI()
        except ValueError:
            print("⚠️  Foursquare API key not available, Foursquare features disabled")
            self.foursquare_api = None
    
    def find_yelp_business_for_google_place(
        self, 
        google_place: PointOfInterest,
        search_radius_m: int = 500,
        name_similarity_threshold: float = 0.6
    ) -> Optional[PointOfInterest]:
        """
        Find the corresponding Yelp business for a Google Place restaurant.
        Uses a two-step approach: first business_matches, then business_details.
        
        Args:
            google_place: Google Place POI object
            search_radius_m: Search radius in meters around the Google Place
            name_similarity_threshold: Minimum name similarity score (0-1)
            
        Returns:
            Yelp business POI object if found, None otherwise
        """
        if not is_restaurant(google_place):
            return None
        
        try:
            # Step 1: Try business_matches API first for exact matching
            from service_api.yelp_api import yelp_business_matches, yelp_business_details
            
            # Extract address components for business_matches
            address_components = self._extract_address_components(google_place)
            if address_components:
                matches = yelp_business_matches(
                    name=google_place.name,
                    address1=address_components.get('address1', ''),
                    city=address_components.get('city', ''),
                    state=address_components.get('state', ''),
                    country=address_components.get('country', 'JP'),  # Default to Japan for Tokyo
                    latitude=google_place.location.latitude,
                    longitude=google_place.location.longitude,
                    limit=3,
                    match_threshold="none"  # Use 'none' for more permissive matching
                )
                
                if matches:
                    # Find the best match from the business_matches results
                    best_match = self._find_best_match_from_matches(google_place, matches, name_similarity_threshold)
                    
                    if best_match:
                        # Step 2: Get detailed information for the best match
                        detailed_business = yelp_business_details(best_match.id)
                        
                        # Enhance the Yelp business with Google Place data
                        enhanced_yelp = self._enhance_yelp_with_google_data(google_place, detailed_business)
                        return enhanced_yelp
            
            # Fallback: Use traditional business_search if business_matches fails
            location_str = self._format_location_for_yelp(google_place)
            if not location_str:
                return None
            
            from service_api.yelp_api import yelp_business_search
            
            yelp_results = yelp_business_search(
                location=location_str,
                radius=search_radius_m,
                limit=50
            )
            
            # Find the best match
            best_match = self._find_best_match(
                google_place, 
                yelp_results, 
                name_similarity_threshold
            )
            
            if best_match:
                # Enhance the Yelp business with Google Place data
                enhanced_yelp = self._enhance_yelp_with_google_data(google_place, best_match)
                return enhanced_yelp
            
            return None
            
        except Exception as e:
            print(f"Error linking Google Place to Yelp: {e}")
            return None
    
    
    def _format_location_for_yelp(self, place: PointOfInterest) -> Optional[str]:
        """Format location string for Yelp API"""
        if place.location.latitude and place.location.longitude:
            return f"{place.location.latitude},{place.location.longitude}"
        
        # Fall back to address if coordinates not available
        if place.address:
            return place.address
        
        return None
    
    def _extract_address_components(self, place: PointOfInterest) -> Optional[Dict[str, str]]:
        """
        Extract address components from Google Place for business_matches API.
        
        Args:
            place: Google Place POI object
            
        Returns:
            Dictionary with address components or None if parsing fails
        """
        if not place.address:
            return None
        
        try:
            # Parse address components from Google Place address
            # Real Google Places formats:
            # "Japan, 〒160-0021 Tokyo, Shinjuku City, Kabukichō"
            # "1 Chome-1 Kabukicho, Shinjuku City, Tokyo 160-0021, Japan"
            # "Shinjuku, Tokyo, Japan"
            
            address_parts = [part.strip() for part in place.address.split(',')]
            
            if len(address_parts) < 2:
                return None
            
            components = {}
            
            # Handle different address formats
            if len(address_parts) >= 4:
                # Format: "1 Chome-1 Kabukicho, Shinjuku City, Tokyo 160-0021, Japan"
                # or: "Japan, 〒160-0021 Tokyo, Shinjuku City, Kabukichō"
                
                # Check if first part is "Japan" (reversed format)
                if address_parts[0] == 'Japan':
                    # Format: "Japan, 〒160-0021 Tokyo, Shinjuku City, Kabukichō"
                    components['address1'] = ''
                    components['city'] = address_parts[2]  # Shinjuku City
                    components['state'] = '13'  # Tokyo prefecture
                    components['country'] = 'JP'
                else:
                    # Format: "1 Chome-1 Kabukicho, Shinjuku City, Tokyo 160-0021, Japan"
                    components['address1'] = address_parts[0]
                    components['city'] = address_parts[1]
                    components['state'] = '13'  # Tokyo prefecture
                    components['country'] = 'JP'
                    
            elif len(address_parts) == 3:
                # Format: "Shinjuku, Tokyo, Japan"
                components['address1'] = ''
                components['city'] = address_parts[0]
                components['state'] = '13'  # Tokyo prefecture
                components['country'] = 'JP'
                
            elif len(address_parts) == 2:
                # Format: "Shinjuku, Tokyo"
                components['address1'] = ''
                components['city'] = address_parts[0]
                components['state'] = '13'  # Tokyo prefecture
                components['country'] = 'JP'
            else:
                return None
            
            # Clean up city name - remove postal codes and extra info
            if components['city']:
                # Remove postal codes like "〒160-0021 Tokyo" -> "Tokyo"
                city = components['city']
                if '〒' in city:
                    # Extract city name after postal code
                    parts = city.split(' ', 1)
                    if len(parts) > 1:
                        components['city'] = parts[1]
                    else:
                        components['city'] = city
                
                # Remove "City" suffix for cleaner city names
                if components['city'].endswith(' City'):
                    components['city'] = components['city'][:-5]
            
            # Clean up address1 - remove postal codes
            if components['address1'] and '〒' in components['address1']:
                # Remove postal codes from address1
                parts = components['address1'].split(' ', 1)
                if len(parts) > 1:
                    components['address1'] = parts[1]
                else:
                    components['address1'] = ''
            
            return components
            
        except Exception as e:
            print(f"Error parsing address components: {e}")
            return None
    
    def _find_best_match_from_matches(
        self, 
        google_place: PointOfInterest, 
        yelp_matches: List[YelpPointOfInterest],
        similarity_threshold: float
    ) -> Optional[YelpPointOfInterest]:
        """
        Find the best matching Yelp business from business_matches results.
        This is more lenient than the regular _find_best_match since business_matches
        already pre-filtered the results.
        
        Args:
            google_place: Google Place to match
            yelp_matches: List of Yelp businesses from business_matches API
            similarity_threshold: Minimum similarity score required
            
        Returns:
            Best matching Yelp business or None
        """
        best_match = None
        best_score = 0.0
        
        for yelp_business in yelp_matches:
            # For business_matches, we primarily care about name similarity
            # since location and category are already pre-filtered
            name_score = self._calculate_name_similarity(google_place.name, yelp_business.name)
            
            if name_score > best_score and name_score >= similarity_threshold:
                best_score = name_score
                best_match = yelp_business
        
        return best_match
    
    def _find_best_match(
        self, 
        google_place: PointOfInterest, 
        yelp_businesses: List[YelpPointOfInterest],
        similarity_threshold: float
    ) -> Optional[YelpPointOfInterest]:
        """
        Find the best matching Yelp business for a Google Place.
        
        Args:
            google_place: Google Place to match
            yelp_businesses: List of Yelp businesses to search through
            similarity_threshold: Minimum similarity score required
            
        Returns:
            Best matching Yelp business or None
        """
        best_match = None
        best_score = 0.0
        
        for yelp_business in yelp_businesses:
            score = self._calculate_match_score(google_place, yelp_business)
            
            if score > best_score and score >= similarity_threshold:
                best_score = score
                best_match = yelp_business
        
        return best_match
    
    def _calculate_match_score(
        self, 
        google_place: PointOfInterest, 
        yelp_business: YelpPointOfInterest
    ) -> float:
        """
        Calculate a match score between a Google Place and Yelp business.
        
        Args:
            google_place: Google Place
            yelp_business: Yelp business
            
        Returns:
            Match score between 0 and 1
        """
        scores = []
        
        # 1. Name similarity (40% weight)
        name_score = self._calculate_name_similarity(
            google_place.name, 
            yelp_business.name
        )
        scores.append(('name', name_score, 0.4))
        
        # 2. Distance similarity (30% weight)
        distance_score = self._calculate_distance_similarity(
            google_place, 
            yelp_business
        )
        scores.append(('distance', distance_score, 0.3))
        
        # 3. Category similarity (20% weight)
        category_score = self._calculate_category_similarity(
            google_place, 
            yelp_business
        )
        scores.append(('category', category_score, 0.2))
        
        # 4. Address similarity (10% weight)
        yelp_address = ", ".join(yelp_business.location.display_address) if yelp_business.location.display_address else ""
        address_score = self._calculate_address_similarity(
            google_place.address, 
            yelp_address
        )
        scores.append(('address', address_score, 0.1))
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in scores)
        
        return total_score
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two business names"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = normalize_restaurant_name(name1)
        norm2 = normalize_restaurant_name(name2)
        
        # Check for exact match
        if norm1 == norm2:
            return 1.0
        
        # Check for substring matches
        if norm1 in norm2 or norm2 in norm1:
            return 0.8
        
        # Calculate Jaccard similarity on words
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    
    def _calculate_distance_similarity(
        self, 
        place1: PointOfInterest, 
        place2: YelpPointOfInterest
    ) -> float:
        """Calculate distance-based similarity (closer = higher score)"""
        if (not place1.location.latitude or not place1.location.longitude or
            not place2.coordinates.latitude or not place2.coordinates.longitude):
            return 0.0
        
        distance_m = haversine_m(
            place1.location.latitude, place1.location.longitude,
            place2.coordinates.latitude, place2.coordinates.longitude
        )
        
        # Convert distance to similarity score
        # 0m = 1.0, 50m = 0.8, 100m = 0.6, 200m = 0.4, 500m = 0.1
        if distance_m <= 50:
            return 1.0
        elif distance_m <= 100:
            return 0.8
        elif distance_m <= 200:
            return 0.6
        elif distance_m <= 500:
            return 0.4
        else:
            # Exponential decay for larger distances
            return max(0.0, 0.1 * (1.0 / (distance_m / 1000.0)))
    
    def _calculate_category_similarity(
        self, 
        place1: PointOfInterest, 
        place2: YelpPointOfInterest
    ) -> float:
        """Calculate category similarity"""
        if not place1.category or not place2.get_primary_category():
            return 0.0
        
        cat1 = place1.category.lower()
        cat2 = place2.get_primary_category().lower()
        
        # Exact match
        if cat1 == cat2:
            return 1.0
        
        # Check for common restaurant categories
        restaurant_categories = [
            'restaurant', 'food', 'dining', 'cafe', 'coffee', 'bar', 'pub',
            'bistro', 'eatery', 'diner', 'grill', 'kitchen'
        ]
        
        cat1_is_restaurant = any(cat in cat1 for cat in restaurant_categories)
        cat2_is_restaurant = any(cat in cat2 for cat in restaurant_categories)
        
        if cat1_is_restaurant and cat2_is_restaurant:
            return 0.7  # Both are restaurants
        
        return 0.0
    
    def _calculate_address_similarity(self, address1: str, address2: str) -> float:
        """Calculate address similarity"""
        if not address1 or not address2:
            return 0.0
        
        # Extract street numbers and names
        street1 = self._extract_street_info(address1)
        street2 = self._extract_street_info(address2)
        
        if not street1 or not street2:
            return 0.0
        
        # Check for street number match
        if street1['number'] == street2['number'] and street1['number']:
            return 0.8
        
        # Check for street name similarity
        if street1['name'] and street2['name']:
            name_sim = self._calculate_name_similarity(street1['name'], street2['name'])
            return name_sim * 0.5
        
        return 0.0
    
    def _extract_street_info(self, address: str) -> Dict[str, str]:
        """Extract street number and name from address"""
        if not address:
            return {'number': '', 'name': ''}
        
        # Simple regex to extract street number and name
        # Matches patterns like "123 Main St" or "123 Main Street"
        match = re.match(r'^(\d+)\s+(.+)', address.strip())
        
        if match:
            return {
                'number': match.group(1),
                'name': match.group(2).split(',')[0].strip()  # Take first part before comma
            }
        
        return {'number': '', 'name': address.split(',')[0].strip()}
    
    def _enhance_yelp_with_google_data(
        self, 
        google_place: PointOfInterest, 
        yelp_business: YelpPointOfInterest
    ) -> PointOfInterest:
        """
        Enhance Google Place with Yelp business data.
        
        Args:
            google_place: Google Place to enhance
            yelp_business: Yelp business data to add
            
        Returns:
            Enhanced Google Place POI with yelp_data
        """
        # Create a copy of the Google Place
        enhanced_data = google_place.model_dump()
        
        # Add Yelp data
        enhanced_data['yelp_data'] = yelp_business
        
        # Add Google Place data to raw_data for reference
        if 'linked_google_place' not in enhanced_data['raw_data']:
            enhanced_data['raw_data']['linked_google_place'] = google_place.raw_data
        
        # Use Yelp data to fill in missing Google Place information
        if not enhanced_data.get('website') and yelp_business.url:
            enhanced_data['website'] = yelp_business.url
        
        if enhanced_data.get('is_open') is None and yelp_business.is_currently_open() is not None:
            enhanced_data['is_open'] = yelp_business.is_currently_open()
        
        # Add Yelp categories to tags
        yelp_categories = yelp_business.get_all_categories()
        combined_tags = list(set(enhanced_data.get('tags', []) + yelp_categories))
        enhanced_data['tags'] = combined_tags
        
        # Mark that this data has been enhanced by Yelp
        enhanced_by = enhanced_data.get('enhanced_by', [])
        if Source.yelp not in enhanced_by:
            enhanced_by.append(Source.yelp)
        enhanced_data['enhanced_by'] = enhanced_by
        
        # Create enhanced POI
        enhanced_poi = PointOfInterest(**enhanced_data)
        
        return enhanced_poi
    
    def link_restaurants_batch(
        self, 
        google_places: List[PointOfInterest],
        search_radius_m: int = 500,
        name_similarity_threshold: float = 0.6
    ) -> List[Tuple[PointOfInterest, Optional[PointOfInterest]]]:
        """
        Link multiple Google Places restaurants with Yelp businesses.
        
        Args:
            google_places: List of Google Places
            search_radius_m: Search radius in meters
            name_similarity_threshold: Minimum name similarity threshold
            
        Returns:
            List of tuples (google_place, linked_yelp_business)
        """
        results = []
        
        for google_place in google_places:
            linked_yelp = self.find_yelp_business_for_google_place(
                google_place, 
                search_radius_m, 
                name_similarity_threshold
            )
            results.append((google_place, linked_yelp))
        
        return results

    # ------------------------------ Foursquare Linking ------------------------------
    def find_foursquare_venue_for_google_place(
        self,
        google_place: PointOfInterest,
        search_radius_m: int = 500,
        name_similarity_threshold: float = 0.6
    ) -> Optional[PointOfInterest]:
        """
        Find the corresponding Foursquare venue for a Google Place.
        Returns the matched Foursquare POI (as PointOfInterest) if found.
        """
        
        try:
            # Prefer coordinates for precise search
            if not (google_place.location.latitude and google_place.location.longitude):
                return None
            
            ll = f"{google_place.location.latitude},{google_place.location.longitude}"
            # Use the Google name as the query (fallback to generic 'place')
            fsq_results = self.foursquare_api.venue_search(
                query=google_place.name or "place",
                ll=ll,
                radius=search_radius_m,
                limit=20,
                open_now=None,
                sort="DISTANCE"
            )
            
            best_match = self._find_best_match(
                google_place,
                fsq_results.items,
                name_similarity_threshold
            )
            
            return best_match
        except Exception as e:
            print(f"Error linking Google Place to Foursquare: {e}")
            return None

    def enhance_google_place_with_foursquare(
        self,
        google_place: PointOfInterest,
        search_radius_m: int = 500,
        name_similarity_threshold: float = 0.6
    ) -> PointOfInterest:
        """
        Try to find a matching Foursquare venue and attach its data to the Google POI.
        Returns the updated Google POI (original if no match).
        """
        fsq_match = self.find_foursquare_venue_for_google_place(
            google_place,
            search_radius_m=search_radius_m,
            name_similarity_threshold=name_similarity_threshold,
        )
        if not fsq_match:
            return google_place
        
        # Merge: keep Google as primary, attach Foursquare details and enrich missing fields
        poi_data = google_place.model_dump()
        
        # Attach raw linked data
        if 'linked_foursquare' not in poi_data['raw_data']:
            poi_data['raw_data']['linked_foursquare'] = fsq_match.raw_data
        
        # Attach structured foursquare_data
        poi_data['foursquare_data'] = fsq_match.foursquare_data or fsq_match.raw_data
        
        # Fill missing fields from Foursquare
        if not poi_data.get('website') and fsq_match.get_foursquare_website():
            poi_data['website'] = fsq_match.get_foursquare_website()
        if not poi_data.get('image_url') and fsq_match.get_foursquare_photo_url():
            poi_data['image_url'] = fsq_match.get_foursquare_photo_url()
        if poi_data.get('is_open') is None and fsq_match.is_foursquare_venue_open() is not None:
            poi_data['is_open'] = fsq_match.is_foursquare_venue_open()
        if not poi_data.get('price_level') and fsq_match.get_foursquare_price_level():
            poi_data['price_level'] = fsq_match.get_foursquare_price_level()
        
        # Merge tags/categories
        poi_data['tags'] = list(set(poi_data.get('tags', []) + fsq_match.get_foursquare_categories()))
        
        # Mark enhancement source
        enhanced_by = poi_data.get('enhanced_by', [])
        if Source.foursquare not in enhanced_by:
            enhanced_by.append(Source.foursquare)
        poi_data['enhanced_by'] = enhanced_by
        
        return PointOfInterest(**poi_data)


# Convenience functions
_restaurant_linker = RestaurantLinker()

def link_google_place_to_yelp(
    google_place: PointOfInterest,
    search_radius_m: int = 100,
    name_similarity_threshold: float = 0.7
) -> Optional[PointOfInterest]:
    """Convenience function to link a single Google Place to Yelp"""
    return _restaurant_linker.find_yelp_business_for_google_place(
        google_place, search_radius_m, name_similarity_threshold
    )

def link_restaurants_batch(
    google_places: List[PointOfInterest],
    search_radius_m: int = 100,
    name_similarity_threshold: float = 0.7
) -> List[Tuple[PointOfInterest, Optional[PointOfInterest]]]:
    """Convenience function to link multiple Google Places to Yelp"""
    return _restaurant_linker.link_restaurants_batch(
        google_places, search_radius_m, name_similarity_threshold
    )

def link_google_place_to_foursquare(
    google_place: PointOfInterest,
    search_radius_m: int = 100,
    name_similarity_threshold: float = 0.7
) -> Optional[PointOfInterest]:
    """Find a matching Foursquare venue for a Google Place (returns Foursquare POI or None)."""
    return _restaurant_linker.find_foursquare_venue_for_google_place(
        google_place, search_radius_m, name_similarity_threshold
    )

def enhance_google_place_with_foursquare(
    google_place: PointOfInterest,
    search_radius_m: int = 100,
    name_similarity_threshold: float = 0.7
) -> PointOfInterest:
    """Attach Foursquare data onto the given Google POI if a match is found."""
    return _restaurant_linker.enhance_google_place_with_foursquare(
        google_place, search_radius_m, name_similarity_threshold
    )
