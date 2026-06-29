import os
import requests
import math
from typing import Dict, Any, List

class HotelService:
    """
    A service class that queries the Google Places API to search for accommodation 
    matching budget parameters, ranks the hotels using a safety/proximity/rating score model, 
    and handles fallback search simulations.
    """

    def __init__(self, api_key: str = None):
        # Resolve the Google Places API key from parameters or server env vars
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY must be set in environment variables")
        self.base_url = "https://maps.googleapis.com/maps/api/place"

    def get_hotels(self, city: str, budget_limit: float, city_lat: float = None, city_lng: float = None) -> List[Dict[str, Any]]:
        """
        Retrieves, ranks, and filters hotels in a given city.
        
        Args:
            city (str): Destination city name.
            budget_limit (float): Max budget per night for hotels in INR.
            city_lat (float): Latitude of the city center.
            city_lng (float): Longitude of the city center.
            
        Returns:
            List[Dict[str, Any]]: Processed, sorted, and scored hotel profiles within budget constraints.
        """
        url = f"{self.base_url}/textsearch/json"
        params = {
            "query": f"hotels in {city}",
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            res_json = response.json()
            status = res_json.get("status")
            results = res_json.get("results", [])
            
            # Check for API errors or query limit constraints
            if not results or status == "REQUEST_DENIED" or status == "OVER_QUERY_LIMIT":
                print(f"Google Places API returned status {status} or empty results. Using fallback hotels.")
                return self._get_fallback_hotels(city, budget_limit, city_lat or 0.0, city_lng or 0.0)
            
            # Resolve center latitude/longitude using the first retrieved hotel location if none specified
            if not city_lat or not city_lng:
                city_lat = results[0]["geometry"]["location"]["lat"]
                city_lng = results[0]["geometry"]["location"]["lng"]
                    
            processed = self._process_and_rank_hotels(results, budget_limit, city_lat, city_lng)
            if not processed:
                print("No hotels matched budget constraint. Using fallback hotels.")
                return self._get_fallback_hotels(city, budget_limit, city_lat, city_lng)
            return processed
        except Exception as e:
            print(f"Error fetching hotels: {e}")
            return self._get_fallback_hotels(city, budget_limit, city_lat or 0.0, city_lng or 0.0)

    def _process_and_rank_hotels(self, results: List[Dict[str, Any]], budget_limit: float, city_lat: float, city_lng: float) -> List[Dict[str, Any]]:
        """
        Evaluates Places API search entries, maps budget constraints (using simulated prices), 
        computes geographical distances, and scores each option.
        """
        ranked_hotels = []
        
        for index, item in enumerate(results):
            name = item.get("name", "Unknown Hotel")
            rating = item.get("rating", 3.0)
            user_ratings_total = item.get("user_ratings_total", 10)
            address = item.get("formatted_address", "")
            
            loc = item.get("geometry", {}).get("location", {})
            lat = loc.get("lat", city_lat)
            lng = loc.get("lng", city_lng)
            
            # Calculate geodesic distance from city center to current hotel location
            distance_from_center = self._calculate_distance(city_lat, city_lng, lat, lng)
            
            # Map index and rating to a mock price fitting the budget structure (in INR)
            # Base price is ₹4,000, scaled by rating and index offset
            price_per_night = round(4000 + (rating - 3.0) * 8000 + (index % 3) * 2400, 2)
            
            # Prune hotels that exceed the user's allocated daily lodging budget
            if price_per_night > budget_limit:
                continue
                
            # Mock close-range proximity indices to essential public security services
            dist_to_transport = round(0.1 + (index % 4) * 0.2, 2)
            dist_to_hospital = round(0.5 + (index % 5) * 0.4, 2)
            dist_to_police = round(0.8 + (index % 3) * 0.6, 2)
            has_24hr_reception = (index % 2 == 0)
            
            # Scoring Algorithm:
            # Positive factors: High average ratings (+15 points/star), review depth (+1 point per 100 reviews, capped at 10)
            # Negative factors: Distance from center (-2 points/km), distance to transport (-5 points/km)
            score = (rating * 15) + (min(user_ratings_total, 1000) / 100) - (distance_from_center * 2) - (dist_to_transport * 5)
            if has_24hr_reception:
                score += 5 # Security bonus points
                
            # Accumulate clear explanations for recommendations dynamically
            reasons = []
            if rating >= 4.0:
                reasons.append("Highly rated by travelers")
            if distance_from_center <= 2.0:
                reasons.append("Very close to the city center")
            if dist_to_transport <= 0.5:
                reasons.append("Convenient access to public transit")
            if has_24hr_reception:
                reasons.append("Features a 24-hour reception")
            if dist_to_hospital <= 1.0:
                reasons.append("Close proximity to local medical services")
            if price_per_night <= budget_limit * 0.7:
                reasons.append("Excellent budget-friendly choice")
                
            reason_str = "Recommended because: " + ", ".join(reasons) if reasons else "Recommended based on overall quality and availability."
            
            ranked_hotels.append({
                "name": name,
                "rating": rating,
                "review_count": user_ratings_total,
                "price_per_night": price_per_night,
                "distance_from_center_km": round(distance_from_center, 2),
                "distance_to_transport_km": dist_to_transport,
                "distance_to_hospital_km": dist_to_hospital,
                "distance_to_police_km": dist_to_police,
                "has_24hr_reception": has_24hr_reception,
                "address": address,
                "reason": reason_str,
                "score": round(score, 2),
                "latitude": lat,
                "longitude": lng
            })
            
        # Order list by descending score rating
        ranked_hotels.sort(key=lambda x: x["score"], reverse=True)
        return ranked_hotels[:5]

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Applies the Haversine formula to compute the spherical distance between two sets 
        of latitude and longitude coordinates in kilometers.
        """
        R = 6371.0 # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _get_fallback_hotels(self, city: str, budget_limit: float, city_lat: float, city_lng: float) -> List[Dict[str, Any]]:
        """
        Produces simulated lodging options for fallback when Google Places requests fail.
        """
        mock_data = [
            {"name": f"Grand Plaza Hotel {city}", "rating": 4.5, "reviews": 320, "price": 9600.0, "lat_offset": 0.01, "lng_offset": 0.01},
            {"name": f"Budget Inn {city}", "rating": 3.8, "reviews": 90, "price": 4800.0, "lat_offset": -0.01, "lng_offset": -0.02},
            {"name": f"Transit Hub Suites {city}", "rating": 4.2, "reviews": 450, "price": 7600.0, "lat_offset": 0.02, "lng_offset": -0.01},
            {"name": f"SafeHaven Boutique Resort {city}", "rating": 4.7, "reviews": 180, "price": 14400.0, "lat_offset": -0.02, "lng_offset": 0.03}
        ]
        
        results = []
        for i, mock in enumerate(mock_data):
            if mock["price"] > budget_limit:
                continue
            lat = city_lat + mock["lat_offset"]
            lng = city_lng + mock["lng_offset"]
            dist_to_center = self._calculate_distance(city_lat, city_lng, lat, lng)
            
            reasons = ["Within budget limit"]
            if mock["rating"] >= 4.5:
                reasons.append("Excellent ratings and reviews")
            if dist_to_center < 1.5:
                reasons.append("Close to central city landmarks")
            if i % 2 == 0:
                reasons.append("Convenient public transport access")
                
            results.append({
                "name": mock["name"],
                "rating": mock["rating"],
                "review_count": mock["reviews"],
                "price_per_night": mock["price"],
                "distance_from_center_km": round(dist_to_center, 2),
                "distance_to_transport_km": round(0.2 + (i % 2) * 0.3, 2),
                "distance_to_hospital_km": round(0.6 + i * 0.5, 2),
                "distance_to_police_km": round(0.4 + i * 0.6, 2),
                "has_24hr_reception": i % 2 == 0,
                "address": f"{mock['name']} Street, {city}",
                "reason": "Recommended because: " + ", ".join(reasons),
                "score": round(mock["rating"] * 10 - dist_to_center, 2),
                "latitude": lat,
                "longitude": lng
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

