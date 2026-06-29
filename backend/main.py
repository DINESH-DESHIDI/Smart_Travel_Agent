import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load server environment configurations (.env) relative to this directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Import agents, services and mock tools
from agents.planner_agent import PlannerAgent
from services.itinerary_service import ItineraryService
from services.weather_service import WeatherService
from services.hotel_service import HotelService
from services.restaurant_service import RestaurantService

# Initialize the main FastAPI application server
app = FastAPI(title="AI Smart Travel Companion API")

# Enable Cross-Origin Resource Sharing (CORS) to allow requests from the React frontend running locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows connections from any origin; restrict in production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Request Validation Models ---

class PlanRequest(BaseModel):
    """
    Validation schema representing user inputs for creating a new travel plan.
    """
    city: str
    days: int
    budget: float
    travelers: int
    travel_type: str
    preferred_transport: str
    preferences: List[str]

class RegenerateRequest(BaseModel):
    """
    Validation schema representing user inputs for updating an existing travel plan dynamically.
    """
    city: str
    days: int
    budget: float
    travelers: int
    travel_type: str
    preferred_transport: str
    preferences: List[str]
    change_type: str
    current_plan: Dict[str, Any]

# In-memory dictionary acting as an API query cache for faster execution
plan_cache = {}

# --- FastAPI Router Endpoints ---

@app.get("/api/health")
def health_check():
    """
    Simple server health diagnostics check endpoint.
    """
    return {"status": "healthy", "message": "AI Smart Travel Companion API is running."}

@app.post("/api/plan")
def generate_plan(request: PlanRequest):
    """
    Main endpoint for creating a personalized, weather-adapted travel plan.
    Uses in-memory caching to avoid redundant LLM invocations for identical trip parameters.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured on the server.")
        
    # Generate cache key using key demographic parameters
    cache_key = f"{request.city.lower()}_{request.days}_{request.budget}_{request.travelers}_{request.travel_type}"
    if cache_key in plan_cache:
        return plan_cache[cache_key]
        
    try:
        # Instantiate the planning agent to coordinate backend tools and LLM
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
    """
    Fine-tuning endpoint for adjusting specific subsets of the active plan (Budget, Weather simulation, Hotel selection).
    Runs calculations and invokes specific mock tools to recalculate allocations and routes.
    """
    try:
        current_plan = request.current_plan
        change_type = request.change_type.lower()
        
        # Scenario A: User adjusts total budget bounds
        if change_type == "budget":
            from tools.tools import budget_tool, hotel_tool, restaurant_tool
            
            # Recalculate allocations based on updated budget limits
            budget_data = budget_tool.invoke({"total_budget": request.budget, "num_travelers": request.travelers})
            hotel_budget_total = budget_data["allocation"]["hotel"]
            hotel_limit_per_night = hotel_budget_total / request.days if request.days > 0 else hotel_budget_total
            
            # Re-fetch hotels within new pricing limits
            hotels = hotel_tool.invoke({"city": city_resolved := request.city, "budget_limit": hotel_limit_per_night})
            
            # Re-fetch restaurants within new dining limits
            food_budget_total = budget_data["allocation"]["food"]
            rest_limit_per_meal = food_budget_total / (request.days * 2) if request.days > 0 else food_budget_total
            restaurants = restaurant_tool.invoke({"city": request.city, "budget_limit": rest_limit_per_meal})
            
            # Update the plan dictionary fields
            current_plan["budget_summary"] = budget_data
            current_plan["hotels"] = hotels
            current_plan["restaurants"] = restaurants
            current_plan["itinerary"] = ItineraryService.build_itinerary(
                request.city, request.days, current_plan["weather"]["forecast"], hotels, restaurants, request.preferences
            )
            current_plan["ai_reasoning"]["executive_summary"] = f"Plan updated successfully with new budget ₹{request.budget}."
            
        # Scenario B: Simulate weather forecast alterations (e.g. rain/clear simulation trigger)
        elif change_type == "weather":
            forecast = current_plan["weather"]["forecast"]
            if forecast:
                # Invert rain indicators to simulate changing conditions
                forecast[0]["has_rain"] = not forecast[0]["has_rain"]
                forecast[0]["description"] = "heavy rain" if forecast[0]["has_rain"] else "clear sky"
                forecast[0]["status"] = "Rain Alert (Indoor Recommended)" if forecast[0]["has_rain"] else "Good for Outdoor Activities"
                
            current_plan["weather"]["forecast"] = forecast
            # Regenerate day-by-day schedules (morning/afternoon choices will shift between indoor and outdoor lists)
            current_plan["itinerary"] = ItineraryService.build_itinerary(
                request.city, request.days, forecast, current_plan["hotels"], current_plan["restaurants"], request.preferences
            )
            current_plan["ai_reasoning"]["weather_adaptation_reason"] = "Itinerary dynamically adjusted to simulated rain changes."
            
        # Scenario C: Rotate selected hotels list selection
        elif change_type == "hotel":
            hotels = current_plan.get("hotels", [])
            if len(hotels) > 1:
                # Shift lodging selections queue to cycle pick recommendations
                first = hotels.pop(0)
                hotels.append(first)
                current_plan["hotels"] = hotels
                current_plan["itinerary"] = ItineraryService.build_itinerary(
                    request.city, request.days, current_plan["weather"]["forecast"], hotels, current_plan["restaurants"], request.preferences
                )
                
                # Fetch navigation route and safety index metrics for the newly selected pick option
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

# Entrypoint runtime runner
if __name__ == "__main__":
    import uvicorn
    # Startup the app server on localhost, port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)

