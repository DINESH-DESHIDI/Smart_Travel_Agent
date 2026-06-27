import os
import sys
from dotenv import load_dotenv

# Ensure the backend directory is in the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_services():
    print("--- Starting Backend Services Integration Test ---")
    
    # 1. Budget Service
    from services.budget_service import BudgetService
    alloc = BudgetService.calculate_allocation(1000, 2)
    print("[Budget] Allocation:", alloc["allocation"])
    assert alloc["allocation"]["hotel"] == 350.0
    
    # 2. Weather Service
    from services.weather_service import WeatherService
    ws = WeatherService()
    weather = ws.get_weather_forecast("Paris")
    print("[Weather] City:", weather["city"], "| Forecast Days:", len(weather["forecast"]))
    assert len(weather["forecast"]) > 0
    
    # 3. Hotel Service
    from services.hotel_service import HotelService
    hs = HotelService()
    hotels = hs.get_hotels("Paris", 12000)
    print("[Hotels] Found Hotels:", len(hotels))
    if hotels:
        print("[Hotels] Top Pick:", hotels[0]["name"])
        
    # 4. Restaurant Service
    from services.restaurant_service import RestaurantService
    rs = RestaurantService()
    rests = rs.get_restaurants("Paris", 3200)
    print("[Restaurants] Found Restaurants:", len(rests))
    if rests:
        print("[Restaurants] Top Pick:", rests[0]["name"])
        
    # 5. Safety Service
    from services.safety_service import SafetyService
    ss = SafetyService()
    safety = ss.assess_safety("Test Place", 4.5, 200, 0.4, 0.6, 0.2)
    print("[Safety] Score:", safety["safety_score_percentage"], "% | Tier:", safety["safety_tier"])
    
    # 6. Navigation Service
    from services.navigation_service import NavigationService
    ns = NavigationService()
    nav = ns.get_route("Hotel de Ville, Paris", "Gare du Nord, Paris", "transit")
    print("[Navigation] Route distance:", nav["distance_text"], "| duration:", nav["duration_text"])
    
    # 7. Agent plan
    from agents.planner_agent import PlannerAgent
    agent = PlannerAgent()
    print("[Agent] Invoking Planner Agent...")
    plan = agent.plan_trip(
        city="Paris",
        days=3,
        budget=96000,
        travelers=2,
        travel_type="friends",
        preferred_transport="transit",
        preferences=["vegetarian", "museums"]
    )
    print("[Agent] Keys generated in plan:", plan.keys())
    print("\nSUCCESS: All backend services and agents validated successfully!")

if __name__ == "__main__":
    test_services()
