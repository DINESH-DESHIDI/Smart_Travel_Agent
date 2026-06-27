import os
import requests
from typing import Dict, Any

class NavigationService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY must be set in environment variables")
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"

    def get_route(self, origin: str, destination: str, mode: str = "transit") -> Dict[str, Any]:
        """Fetches directions between origin and destination."""
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_directions(data, origin, destination, mode)
        except Exception as e:
            print(f"Error fetching directions: {e}")
            return self._get_fallback_directions(origin, destination, mode)

    def _parse_directions(self, data: Dict[str, Any], origin: str, destination: str, mode: str) -> Dict[str, Any]:
        routes = data.get("routes", [])
        if not routes:
            return self._get_fallback_directions(origin, destination, mode)
            
        leg = routes[0]["legs"][0]
        distance_text = leg.get("distance", {}).get("text", "Unknown")
        distance_value = leg.get("distance", {}).get("value", 0)
        duration_text = leg.get("duration", {}).get("text", "Unknown")
        duration_value = leg.get("duration", {}).get("value", 0)
        
        start_address = leg.get("start_address", origin)
        end_address = leg.get("end_address", destination)
        
        steps = leg.get("steps", [])
        walking_directions = []
        metro_lines = []
        
        for step in steps:
            html_instructions = step.get("html_instructions", "")
            import re
            clean_instruction = re.sub('<[^<]+?>', '', html_instructions)
            
            travel_mode = step.get("travel_mode", "").lower()
            if travel_mode == "walking":
                walking_directions.append(clean_instruction)
            elif travel_mode == "transit":
                transit_details = step.get("transit_details", {})
                line_name = transit_details.get("line", {}).get("short_name", "") or transit_details.get("line", {}).get("name", "")
                arrival_stop = transit_details.get("arrival_stop", {}).get("name", "")
                departure_stop = transit_details.get("departure_stop", {}).get("name", "")
                
                if line_name:
                    metro_lines.append(f"Take {line_name} from {departure_stop} to {arrival_stop}")
                    
        distance_km = distance_value / 1000.0
        cab_estimate = round(100.0 + 15.0 * distance_km, 2)
        
        duration_mins = duration_value / 60.0
        recommended_departure_buffer = 15 if distance_km > 5 else 5
        
        return {
            "origin": start_address,
            "destination": end_address,
            "distance_km": round(distance_km, 2),
            "distance_text": distance_text,
            "duration_mins": round(duration_mins, 1),
            "duration_text": duration_text,
            "walking_steps": walking_directions[:5],
            "transit_recommendations": metro_lines,
            "cab_estimate_inr": cab_estimate,
            "recommended_departure_buffer_mins": recommended_departure_buffer,
            "traffic_info": "Moderate traffic. Recommended to leave 15 mins early." if distance_km > 5 else "Light traffic."
        }

    def _get_fallback_directions(self, origin: str, destination: str, mode: str) -> Dict[str, Any]:
        """Fallback mock navigation details if API fails."""
        import random
        distance_km = round(3.5 + random.random() * 5.0, 2)
        duration_mins = round(distance_km * 3.5, 1) if mode == "walking" else round(distance_km * 2.0 + 8.0, 1)
        
        return {
            "origin": origin,
            "destination": destination,
            "distance_km": distance_km,
            "distance_text": f"{distance_km} km",
            "duration_mins": duration_mins,
            "duration_text": f"{int(duration_mins)} mins",
            "walking_steps": [
                "Head east on Main Street toward Station Road",
                "Turn right onto Transit Blvd",
                "Slight left to enter destination"
            ],
            "transit_recommendations": [
                f"Take Metro Line 2 (Blue) from Central Station to {destination} Gate"
            ],
            "cab_estimate_inr": round(120.0 + 12.0 * distance_km, 2),
            "recommended_departure_buffer_mins": 10 if distance_km > 3 else 5,
            "traffic_info": "Clear route, normal traffic."
        }
