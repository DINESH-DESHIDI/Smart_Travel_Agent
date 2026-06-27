import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from agents.planner_agent import PlannerAgent
from services.itinerary_service import ItineraryService
from services.weather_service import WeatherService
from services.hotel_service import HotelService
from services.restaurant_service import RestaurantService

app = FastAPI(title="AI Smart Travel Companion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    city: str
    days: int
    budget: float
    travelers: int
    travel_type: str
    preferred_transport: str
    preferences: List[str]

class RegenerateRequest(BaseModel):
    city: str
    days: int
    budget: float
    travelers: int
    travel_type: str
    preferred_transport: str
    preferences: List[str]
    change_type: str
    current_plan: Dict[str, Any]

plan_cache = {}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "AI Smart Travel Companion API is running."}

@app.post("/api/plan")
def generate_plan(request: PlanRequest):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured on the server.")
        
    cache_key = f"{request.city.lower()}_{request.days}_{request.budget}_{request.travelers}_{request.travel_type}"
    if cache_key in plan_cache:
        return plan_cache[cache_key]
        
    try:
        agent = PlannerAgent()
        plan = agent.plan_trip(
            city=request.city,
            days=request.days,
            budget=request.budget,
            travelers=request.travelers,
            travel_type=request.travel_type,
            preferred_transport=request.preferred_transport,
            preferences=request.preferences
        )
        plan_cache[cache_key] = plan
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/regenerate")
def regenerate_plan(request: RegenerateRequest):
    try:
        current_plan = request.current_plan
        change_type = request.change_type.lower()
        
        if change_type == "budget":
            from tools.tools import budget_tool, hotel_tool, restaurant_tool
            
            budget_data = budget_tool.invoke({"total_budget": request.budget, "num_travelers": request.travelers})
            hotel_budget_total = budget_data["allocation"]["hotel"]
            hotel_limit_per_night = hotel_budget_total / request.days if request.days > 0 else hotel_budget_total
            
            hotels = hotel_tool.invoke({"city": request.city, "budget_limit": hotel_limit_per_night})
            
            food_budget_total = budget_data["allocation"]["food"]
            rest_limit_per_meal = food_budget_total / (request.days * 2) if request.days > 0 else food_budget_total
            restaurants = restaurant_tool.invoke({"city": request.city, "budget_limit": rest_limit_per_meal})
            
            current_plan["budget_summary"] = budget_data
            current_plan["hotels"] = hotels
            current_plan["restaurants"] = restaurants
            current_plan["itinerary"] = ItineraryService.build_itinerary(
                request.city, request.days, current_plan["weather"]["forecast"], hotels, restaurants, request.preferences
            )
            current_plan["ai_reasoning"]["executive_summary"] = f"Plan updated successfully with new budget ₹{request.budget}."
            
        elif change_type == "weather":
            forecast = current_plan["weather"]["forecast"]
            if forecast:
                forecast[0]["has_rain"] = not forecast[0]["has_rain"]
                forecast[0]["description"] = "heavy rain" if forecast[0]["has_rain"] else "clear sky"
                forecast[0]["status"] = "Rain Alert (Indoor Recommended)" if forecast[0]["has_rain"] else "Good for Outdoor Activities"
                
            current_plan["weather"]["forecast"] = forecast
            current_plan["itinerary"] = ItineraryService.build_itinerary(
                request.city, request.days, forecast, current_plan["hotels"], current_plan["restaurants"], request.preferences
            )
            current_plan["ai_reasoning"]["weather_adaptation_reason"] = "Itinerary dynamically adjusted to simulated rain changes."
            
        elif change_type == "hotel":
            hotels = current_plan.get("hotels", [])
            if len(hotels) > 1:
                first = hotels.pop(0)
                hotels.append(first)
                current_plan["hotels"] = hotels
                current_plan["itinerary"] = ItineraryService.build_itinerary(
                    request.city, request.days, current_plan["weather"]["forecast"], hotels, current_plan["restaurants"], request.preferences
                )
                
                from tools.tools import safety_tool, navigation_tool
                top_hotel = hotels[0]
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
                    "destination": f"{request.city} Central Station",
                    "mode": "transit"
                })
                current_plan["safety"] = safety_data
                current_plan["navigation"] = navigation_data
                current_plan["ai_reasoning"]["hotel_choice_reason"] = f"Hotel rotated to {top_hotel['name']} based on user selection."
                
        return current_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
