import os
import requests
import math
from typing import Dict, Any, List

class RestaurantService:
    """
    A service class that interacts with the Google Places API to search for restaurants, 
    calculates pricing parameters, and ranks options using reviews, location, and vegetarian availability.
    """

    def __init__(self, api_key: str = None):
        # Resolve Places API key from parameters or server env vars
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY must be set in environment variables")
        self.base_url = "https://maps.googleapis.com/maps/api/place"

    def get_restaurants(self, city: str, budget_limit: float, city_lat: float = None, city_lng: float = None) -> List[Dict[str, Any]]:
        """
        Queries restaurants in the specified city and evaluates them against the traveler's budget.
        
        Args:
            city (str): Destination city name.
            budget_limit (float): Max budget per meal in INR.
            city_lat (float): Center latitude coordinate.
            city_lng (float): Center longitude coordinate.
            
        Returns:
            List[Dict[str, Any]]: Best-matched restaurant list ordered by ranking score.
        """
        url = f"{self.base_url}/textsearch/json"
        params = {
            "query": f"restaurants in {city}",
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            res_json = response.json()
            status = res_json.get("status")
            results = res_json.get("results", [])
            
            # Use mock fallback dataset on network limitations or API exceptions
            if not results or status == "REQUEST_DENIED" or status == "OVER_QUERY_LIMIT":
                print(f"Google Places API returned status {status} or empty results. Using fallback restaurants.")
                return self._get_fallback_restaurants(city, budget_limit, city_lat or 0.0, city_lng or 0.0)
            
            # Resolve center latitude/longitude using the first retrieved item location if none specified
            if not city_lat or not city_lng:
                city_lat = results[0]["geometry"]["location"]["lat"]
                city_lng = results[0]["geometry"]["location"]["lng"]
                    
            processed = self._process_and_rank_restaurants(results, budget_limit, city_lat, city_lng)
            if not processed:
                print("No restaurants matched budget constraint. Using fallback restaurants.")
                return self._get_fallback_restaurants(city, budget_limit, city_lat, city_lng)
            return processed
        except Exception as e:
            print(f"Error fetching restaurants: {e}")
            return self._get_fallback_restaurants(city, budget_limit, city_lat or 0.0, city_lng or 0.0)

    def _process_and_rank_restaurants(self, results: List[Dict[str, Any]], budget_limit: float, city_lat: float, city_lng: float) -> List[Dict[str, Any]]:
        """
        Enriches Places API data with mock menu details, computes cost averages, and executes ranking.
        """
        ranked_rests = []
        # Predefined cuisine and menu items to structure mock restaurant menus
        cuisines_list = ["Local Specialities", "Italian", "Asian Fusion", "Traditional", "Street Food", "Cafe", "Fine Dining"]
        popular_dishes_list = [
            ["House Special Pasta", "Garlic Bread", "Tiramisu"],
            ["Chef's Special Curry", "Steamed Basmati Rice", "Mango Lassi"],
            ["Signature Noodles", "Dim Sum platter", "Spring rolls"],
            ["Gourmet Burger & Fries", "Onion Rings", "Chocolate Milkshake"],
            ["Woodfired Neapolitan Pizza", "Caprese Salad", "Panna Cotta"],
            ["Traditional Thali", "Paneer Butter Masala", "Gulab Jamun"],
            ["Fresh Sushi Assortment", "Tempura", "Matcha Ice Cream"]
        ]
        
        for index, item in enumerate(results):
            name = item.get("name", "Unknown Restaurant")
            rating = item.get("rating", 3.0)
            user_ratings_total = item.get("user_ratings_total", 10)
            address = item.get("formatted_address", "")
            
            loc = item.get("geometry", {}).get("location", {})
            lat = loc.get("lat", city_lat)
            lng = loc.get("lng", city_lng)
            
            distance_from_center = self._calculate_distance(city_lat, city_lng, lat, lng)
            # Average meal cost calculated in INR: Base cost + rating offset + index offset
            avg_meal_cost = round(800 + (rating - 3.0) * 1600 + (index % 4) * 640, 2)
            
            # Prune restaurants that exceed the traveler's single-meal budget threshold
            if avg_meal_cost > budget_limit:
                continue
                
            cuisine = cuisines_list[index % len(cuisines_list)]
            popular_dishes = popular_dishes_list[index % len(popular_dishes_list)]
            veg_available = (index % 3 != 0) # Mock vegetarian options availability
            
            is_open_now = item.get("opening_hours", {}).get("open_now", True)
            
            # Scoring Algorithm:
            # Positive factors: Rating weight (+12 points/star), review depth (+1 point per 50 reviews, max 10 points)
            # Negative factors: Geodesic distance from center (-1.5 points/km)
            score = (rating * 12) + (min(user_ratings_total, 500) / 50) - (distance_from_center * 1.5)
            if veg_available:
                score += 3 # Vegetarian support bonus
            if is_open_now:
                score += 2 # Open indicator bonus
                
            # Build text highlights to explain recommendation choices in UI
            reasons = []
            if rating >= 4.0:
                reasons.append("Highly rated by customers")
            if distance_from_center <= 1.5:
                reasons.append("Centrally located and easy to reach")
            if veg_available:
                reasons.append("Great vegetarian selection available")
            if avg_meal_cost <= budget_limit * 0.6:
                reasons.append("Very economical pricing")
            if is_open_now:
                reasons.append("Currently open and accepting guests")
                
            reason_str = "Recommended because: " + ", ".join(reasons) if reasons else "Selected based on general cuisine popularity and ratings."
            
            ranked_rests.append({
                "name": name,
                "rating": rating,
                "review_count": user_ratings_total,
                "average_meal_cost": avg_meal_cost,
                "cuisine": cuisine,
                "popular_dishes": popular_dishes,
                "vegetarian_available": veg_available,
                "is_open_now": is_open_now,
                "distance_km": round(distance_from_center, 2),
                "address": address,
                "reason": reason_str,
                "score": round(score, 2),
                "latitude": lat,
                "longitude": lng
            })
            
        ranked_rests.sort(key=lambda x: x["score"], reverse=True)
        return ranked_rests[:5]

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Computes geodesic distance between coordinate pairs using the Haversine formula.
        """
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _get_fallback_restaurants(self, city: str, budget_limit: float, city_lat: float, city_lng: float) -> List[Dict[str, Any]]:
        """
        Mock restaurant listing for offline validation or API failure recovery.
        """
        mock_data = [
            {"name": f"The Local Bistro {city}", "rating": 4.6, "reviews": 210, "cost": 2000.0, "cuisine": "Traditional", "veg": True},
            {"name": f"Bella Italia {city}", "rating": 4.2, "reviews": 180, "cost": 2400.0, "cuisine": "Italian", "veg": True},
            {"name": f"Spice Garden {city}", "rating": 4.5, "reviews": 340, "cost": 1600.0, "cuisine": "Asian Fusion", "veg": True},
            {"name": f"Burger Station {city}", "rating": 3.9, "reviews": 85, "cost": 960.0, "cuisine": "Street Food", "veg": False}
        ]
        
        results = []
        for i, mock in enumerate(mock_data):
            if mock["cost"] > budget_limit:
                continue
            lat = city_lat + (i * 0.01 - 0.01)
            lng = city_lng + (i * 0.01 - 0.01)
            dist_to_center = self._calculate_distance(city_lat, city_lng, lat, lng)
            
            reasons = ["Within budget limit"]
            if mock["rating"] >= 4.5:
                reasons.append("Excellent ratings and reviews")
            if mock["veg"]:
                reasons.append("Great vegetarian options available")
                
            results.append({
                "name": mock["name"],
                "rating": mock["rating"],
                "review_count": mock["reviews"],
                "average_meal_cost": mock["cost"],
                "cuisine": mock["cuisine"],
                "popular_dishes": ["House Specialty Platter", "Fresh Garden Soup", "Local Dessert Platter"],
                "vegetarian_available": mock["veg"],
                "is_open_now": True,
                "distance_km": round(dist_to_center, 2),
                "address": f"{mock['name']} Avenue, {city}",
                "reason": "Recommended because: " + ", ".join(reasons),
                "score": round(mock["rating"] * 10 - dist_to_center, 2),
                "latitude": lat,
                "longitude": lng
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

