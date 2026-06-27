import os
import json
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.tools import budget_tool, weather_tool, hotel_tool, restaurant_tool, navigation_tool, safety_tool
from services.itinerary_service import ItineraryService

class PlannerAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=self.api_key, temperature=0.2)

    def plan_trip(
        self,
        city: str,
        days: int,
        budget: float,
        travelers: int,
        travel_type: str,
        preferred_transport: str,
        preferences: List[str]
    ) -> Dict[str, Any]:
        """Orchestrates all travel services and tools to create a personalized, weather-aware trip plan."""
        budget_data = budget_tool.invoke({"total_budget": budget, "num_travelers": travelers})
        weather_data = weather_tool.invoke({"city": city})
        
        hotel_budget_total = budget_data["allocation"]["hotel"]
        hotel_limit_per_night = hotel_budget_total / days if days > 0 else hotel_budget_total
        hotels = hotel_tool.invoke({"city": city, "budget_limit": hotel_limit_per_night})
        
        top_hotel = hotels[0] if hotels else None
        safety_data = {}
        navigation_data = {}
        
        if top_hotel:
            safety_data = safety_tool.invoke({
                "place_name": top_hotel["name"],
                "rating": top_hotel["rating"],
                "review_count": top_hotel["review_count"],
                "dist_to_hospital": top_hotel["distance_to_hospital_km"],
                "dist_to_police": top_hotel["distance_to_police_km"],
                "dist_to_transit": top_hotel["distance_to_transport_km"]
            })
            navigation_data = navigation_tool.invoke({
                "origin": top_hotel["address"],
                "destination": f"{city} Central Station",
                "mode": "transit"
            })
        else:
            top_hotel = {"name": "Central Lodge", "address": f"Downtown {city}"}
            safety_data = safety_tool.invoke({
                "place_name": top_hotel["name"],
                "rating": 4.0,
                "review_count": 120,
                "dist_to_hospital": 1.2,
                "dist_to_police": 0.9,
                "dist_to_transit": 0.4
            })
            navigation_data = navigation_tool.invoke({
                "origin": top_hotel["address"],
                "destination": f"{city} Central Station",
                "mode": "transit"
            })
            
        food_budget_total = budget_data["allocation"]["food"]
        rest_limit_per_meal = food_budget_total / (days * 2) if days > 0 else food_budget_total
        restaurants = restaurant_tool.invoke({"city": city, "budget_limit": rest_limit_per_meal})
        
        forecast = weather_data.get("forecast", [])
        itinerary = ItineraryService.build_itinerary(city, days, forecast, hotels, restaurants, preferences)
        
        user_prompt = f"""
        Generate a cohesive travel plan for:
        - City: {city}
        - Days: {days}
        - Budget: ₹{budget} (Travel Type: {travel_type}, Preferred Transport: {preferred_transport})
        - Travelers: {travelers}
        - Memory Preferences: {", ".join(preferences)}
        
        Note: All costs, budget values, and allocations provided below are in Indian Rupees (₹ / INR). Please format any monetary references in your response in Rupees (₹ / INR).
        
        Here are the outputs from our planning tools:
        1. Budget Allocations: {json.dumps(budget_data)}
        2. Weather Forecast: {json.dumps(weather_data)}
        3. Hotel Recommendations: {json.dumps(hotels)}
        4. Selected Hotel Safety Assessment: {json.dumps(safety_data)}
        5. Selected Hotel Navigation to Central Station: {json.dumps(navigation_data)}
        6. Restaurant Recommendations: {json.dumps(restaurants)}
        7. Base Itinerary: {json.dumps(itinerary)}
        
        Formulate your response as a valid JSON object. The JSON must contain a key "ai_reasoning" with the following fields:
        - "executive_summary": A summary of the trip planning.
        - "hotel_choice_reason": Detailed reasoning of why the top hotel was chosen (e.g. within budget, high rating, close to transit/services).
        - "restaurant_choice_reason": Reason for restaurant selection.
        - "weather_adaptation_reason": Explanation of how the itinerary adjusted to the weather (e.g. if rain is expected, explain why indoor attractions were chosen).
        
        The JSON should structure the overall combined trip details like this:
        {{
            "budget_summary": <budget_data>,
            "weather": <weather_data>,
            "hotels": <hotels>,
            "restaurants": <restaurants>,
            "navigation": <navigation_data>,
            "safety": <safety_data>,
            "itinerary": <itinerary>,
            "ai_reasoning": {{
                "executive_summary": "...",
                "hotel_choice_reason": "...",
                "restaurant_choice_reason": "...",
                "weather_adaptation_reason": "..."
            }}
        }}
        """
        
        try:
            response = self.llm.invoke(user_prompt)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parsed_result = json.loads(content)
            return parsed_result
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return {
                "budget_summary": budget_data,
                "weather": weather_data,
                "hotels": hotels,
                "restaurants": restaurants,
                "navigation": navigation_data,
                "safety": safety_data,
                "itinerary": itinerary,
                "ai_reasoning": {
                    "executive_summary": f"Your personalized {days}-day trip to {city}.",
                    "hotel_choice_reason": "Selected based on budget limits and rating indicators.",
                    "restaurant_choice_reason": "Selected matching budget parameters and vegetarian preferences.",
                    "weather_adaptation_reason": "Activities scheduled based on daily weather forecast indices."
                }
            }
