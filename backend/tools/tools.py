from langchain_core.tools import tool
from services.budget_service import BudgetService
from services.weather_service import WeatherService
from services.hotel_service import HotelService
from services.restaurant_service import RestaurantService
from services.navigation_service import NavigationService
from services.safety_service import SafetyService

@tool
def budget_tool(total_budget: float, num_travelers: int) -> dict:
    """Calculates standard budget allocations for hotel, food, activities, transport, and emergencies."""
    return BudgetService.calculate_allocation(total_budget, num_travelers)

@tool
def weather_tool(city: str) -> dict:
    """Fetches current conditions and 5-day weather forecasts to identify alerts like rain or high heat."""
    service = WeatherService()
    return service.get_weather_forecast(city)

@tool
def hotel_tool(city: str, budget_limit: float, city_lat: float = None, city_lng: float = None) -> list:
    """Finds and ranks hotels in the city based on rating, distance, reviews, transport, safety, and price constraint."""
    service = HotelService()
    return service.get_hotels(city, budget_limit, city_lat, city_lng)

@tool
def restaurant_tool(city: str, budget_limit: float, city_lat: float = None, city_lng: float = None) -> list:
    """Finds and ranks restaurants matching budget, rating, review counts, cuisine, vegetarian availability."""
    service = RestaurantService()
    return service.get_restaurants(city, budget_limit, city_lat, city_lng)

@tool
def navigation_tool(origin: str, destination: str, mode: str = "transit") -> dict:
    """Gets distance, duration, walking steps, transit details, and cab estimates between two points."""
    service = NavigationService()
    return service.get_route(origin, destination, mode)

@tool
def safety_tool(place_name: str, rating: float, review_count: int, dist_to_hospital: float, dist_to_police: float, dist_to_transit: float) -> dict:
    """Scores safety indicators for a location based on reviews, hospital proximity, police station closeness, and transit availability. Never gives absolute guarantees."""
    return SafetyService.assess_safety(place_name, rating, review_count, dist_to_hospital, dist_to_police, dist_to_transit)
