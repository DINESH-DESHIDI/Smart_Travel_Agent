from typing import Dict, Any

class SafetyService:
    @staticmethod
    def assess_safety(place_name: str, rating: float, review_count: int, dist_to_hospital: float, dist_to_police: float, dist_to_transit: float) -> Dict[str, Any]:
        """Assesses the safety profile of a place based on proximity of public services and popularity data."""
        hospital_score = max(0.0, 10.0 - dist_to_hospital * 3.5)
        police_score = max(0.0, 10.0 - dist_to_police * 3.5)
        transit_score = max(0.0, 5.0 - dist_to_transit * 5.0)
        popularity_score = min(5.0, (review_count / 100.0) + (rating * 0.5))
        
        total_score = hospital_score + police_score + transit_score + popularity_score
        max_possible_score = 30.0
        safety_percentage = (total_score / max_possible_score) * 100.0
        
        if safety_percentage >= 80:
            safety_tier = "High Safety indicators"
            description = "Excellent access to public transport, local police stations, and major hospital units. High crowd activity."
        elif safety_percentage >= 50:
            safety_tier = "Moderate Safety indicators"
            description = "Good access to emergency services and public transit. Moderate crowd levels."
        else:
            safety_tier = "Standard Safety indicators"
            description = "Emergency services are accessible but further away. Recommended to travel during daylight hours."
            
        return {
            "place_name": place_name,
            "safety_score_percentage": round(safety_percentage, 1),
            "safety_tier": safety_tier,
            "assessment_details": description,
            "nearby_services": {
                "hospital_distance_km": dist_to_hospital,
                "police_distance_km": dist_to_police,
                "public_transit_distance_km": dist_to_transit
            },
            "disclaimer": "Recommended based on available information."
        }
