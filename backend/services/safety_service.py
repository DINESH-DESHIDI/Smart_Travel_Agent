from typing import Dict, Any

class SafetyService:
    """
    A service class designed to assess and score the safety index of local places or hotels.
    
    This service evaluates locations based on practical security and emergency accessibility metrics
    (proximity to hospitals, police stations, and transit hubs) combined with crowd popularity indicators.
    """

    @staticmethod
    def assess_safety(
        place_name: str, 
        rating: float, 
        review_count: int, 
        dist_to_hospital: float, 
        dist_to_police: float, 
        dist_to_transit: float
    ) -> Dict[str, Any]:
        """
        Calculates a safety score percentage for a location and assigns it to a safety tier.
        
        Scoring Breakdown (Max Score: 30.0 points):
        1. Hospital proximity (Max 10.0 points): Score decays as distance to hospital increases.
        2. Police station proximity (Max 10.0 points): Score decays as distance to police station increases.
        3. Transit proximity (Max 5.0 points): Score decays as distance to nearest transit point increases.
        4. Popularity metric (Max 5.0 points): Calculated using rating and review counts (as a proxy for busy, populated streets).
        
        Args:
            place_name (str): The name of the place being assessed (e.g. Hotel name).
            rating (float): Average customer rating (0.0 to 5.0).
            review_count (int): Total number of customer reviews.
            dist_to_hospital (float): Distance to the nearest hospital in kilometers.
            dist_to_police (float): Distance to the nearest police station in kilometers.
            dist_to_transit (float): Distance to the nearest transit hub/stop in kilometers.
            
        Returns:
            Dict[str, Any]: A safety profile detailing safety scores, safety tier, and local service access details.
        """
        # Proximity score calculations: lower distance yields a higher score.
        # Score decreases linearly and is capped at 0.0 minimum.
        hospital_score = max(0.0, 10.0 - dist_to_hospital * 3.5)
        police_score = max(0.0, 10.0 - dist_to_police * 3.5)
        transit_score = max(0.0, 5.0 - dist_to_transit * 5.0)
        
        # Popularity score acts as a proxy for foot traffic & populated areas (often correlated with safety)
        popularity_score = min(5.0, (review_count / 100.0) + (rating * 0.5))
        
        # Aggregate the component scores
        total_score = hospital_score + police_score + transit_score + popularity_score
        max_possible_score = 30.0
        safety_percentage = (total_score / max_possible_score) * 100.0
        
        # Categorize the safety index into clear, user-friendly safety tiers
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

