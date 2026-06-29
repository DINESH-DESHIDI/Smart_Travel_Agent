from typing import Dict, Any, List

class ItineraryService:
    """
    A service class dedicated to building structured, day-by-day itineraries.
    
    The service intelligently schedules indoor activities on rainy days and outdoor 
    activities on clear days, while integrating hotel detail bindings and matching meal recommendations.
    """

    @staticmethod
    def build_itinerary(
        city: str,
        days: int,
        weather_forecast: List[Dict[str, Any]],
        hotels: List[Dict[str, Any]],
        restaurants: List[Dict[str, Any]],
        preferences: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes traveler constraints, weather alerts, lodging location, and dining options
        into a finalized day-by-day travel timeline.
        
        Args:
            city (str): Target destination.
            days (int): Total number of trip days requested.
            weather_forecast (List[Dict]): Parsed daily weather data points.
            hotels (List[Dict]): Selected hotel options.
            restaurants (List[Dict]): Selected local restaurants options.
            preferences (List[str]): User interests or food options (e.g. "vegetarian", "museums").
            
        Returns:
            List[Dict[str, Any]]: Day-by-day timeline listing activities, dining locations, and lodging base.
        """
        itinerary = []
        # Fallback hotel template if no recommendations are found
        hotel = hotels[0] if hotels else {"name": "Standard Accommodation", "address": "Central City"}
        
        # Predefined database of indoor activities for rainy/extreme weather conditions
        indoor_activities = [
            "Visit the National History Museum and indoor exhibits",
            "Explore the local Botanical Greenhouse and Art Gallery",
            "Tour the historic cathedral and underground heritage catacombs",
            "Spend the afternoon at the central Science center and planetarium",
            "Explore the covered Grand Bazaar and indoor souvenir markets"
        ]
        
        # Predefined database of outdoor activities for sunny/pleasant weather conditions
        outdoor_activities = [
            "Take a walking tour of the botanical gardens and city lakes",
            "Go sightseeing at the historic outdoor landmarks and towers",
            "Take a scenic boat tour along the central canals/river",
            "Visit the outdoor ancient ruins and open-air heritage site",
            "Hike up to the panoramic mountain lookout and nature trail"
        ]
        
        # Walk through the timeline limits (days, matched to weather forecast length)
        for i in range(min(days, len(weather_forecast))):
            day_forecast = weather_forecast[i]
            day_num = i + 1
            has_rain = day_forecast.get("has_rain", False)
            
            reasoning = []
            # Actively swap activity options depending on the weather conditions
            if has_rain:
                morning_activity = indoor_activities[(i * 2) % len(indoor_activities)]
                afternoon_activity = indoor_activities[(i * 2 + 1) % len(indoor_activities)]
                reasoning.append("Selected indoor activities because rain is expected.")
            else:
                morning_activity = outdoor_activities[(i * 2) % len(outdoor_activities)]
                afternoon_activity = outdoor_activities[(i * 2 + 1) % len(outdoor_activities)]
                reasoning.append("Selected outdoor activities because clear skies are expected.")
                
            # Distribute restaurants options across days for lunch and dinner
            # Modulus logic ensures we recycle suggestions gracefully if fewer places are loaded
            lunch_rest = restaurants[(i * 2) % len(restaurants)] if restaurants else {"name": f"Local Cafe {i}"}
            dinner_rest = restaurants[(i * 2 + 1) % len(restaurants)] if restaurants else {"name": f"Central Diner {i}"}
            
            itinerary.append({
                "day": day_num,
                "date": day_forecast.get("date", ""),
                "weather": {
                    "avg_temp": day_forecast.get("avg_temp"),
                    "description": day_forecast.get("description"),
                    "status": day_forecast.get("status")
                },
                "activities": {
                    "morning": morning_activity,
                    "afternoon": afternoon_activity
                },
                "meals": {
                    "lunch": lunch_rest,
                    "dinner": dinner_rest
                },
                "hotel": hotel,
                "weather_adjustment_reason": " ".join(reasoning)
            })
            
        return itinerary

