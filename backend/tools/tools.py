from langchain_core.tools import tool
from services.budget_service import BudgetService
from services.weather_service import WeatherService
from services.hotel_service import HotelService
from services.restaurant_service import RestaurantService
from services.navigation_service import NavigationService
from services.safety_service import SafetyService

@tool
def budget_tool(total_budget: float, num_travelers: int) -> dict:
    """
    Calculates standard budget allocations for hotel, food, activities, transport, and emergencies.
    
    Args:
        total_budget (float): Total trip budget.
        num_travelers (int): Number of people traveling.
        
    Returns:
        dict: Calculated allocations and per-person cost share.
    """
    return BudgetService.calculate_allocation(total_budget, num_travelers)

@tool
def weather_tool(city: str) -> dict:
    """
    Fetches current conditions and 5-day weather forecasts for a city to identify alerts like rain or high heat.
    
    Args:
        city (str): Name of the destination city.
        
    Returns:
        dict: Weather summaries and warnings.
    """
    service = WeatherService()
    return service.get_weather_forecast(city)

@tool
def hotel_tool(city: str, budget_limit: float, city_lat: float = None, city_lng: float = None) -> list:
    """
    Finds and ranks hotels in the city based on rating, distance, reviews, transport, safety, and price constraint.
    
    Args:
        city (str): City to search for hotels.
        budget_limit (float): Maximum allowed budget limit per night.
        city_lat (float, optional): Center latitude.
        city_lng (float, optional): Center longitude.
        
    Returns:
        list: Scored hotel dictionary entries within budget limits.
    """
    service = HotelService()
    return service.get_hotels(city, budget_limit, city_lat, city_lng)

@tool
def restaurant_tool(city: str, budget_limit: float, city_lat: float = None, city_lng: float = None) -> list:
    """
    Finds and ranks restaurants matching budget, rating, review counts, cuisine, vegetarian availability.
    
    Args:
        city (str): City to search.
        budget_limit (float): Maximum average dining cost threshold.
        city_lat (float, optional): Center latitude.
        city_lng (float, optional): Center longitude.
        
    Returns:
        list: Recommended dining destinations sorted by score.
    """
    service = RestaurantService()
    return service.get_restaurants(city, budget_limit, city_lat, city_lng)

@tool
def navigation_tool(origin: str, destination: str, mode: str = "transit") -> dict:
    """
    Gets distance, duration, walking steps, transit details, and cab estimates between two points.
    
    Args:
        origin (str): Address or coordinates of the starting point.
        destination (str): Address or coordinates of the ending point.
        mode (str): Mode of travel ("transit", "walking", etc).
        
    Returns:
        dict: Travel metrics, routes description list, and cab estimates.
    """
    service = NavigationService()
    return service.get_route(origin, destination, mode)

@tool
def safety_tool(place_name: str, rating: float, review_count: int, dist_to_hospital: float, dist_to_police: float, dist_to_transit: float) -> dict:
    """
    Scores safety indicators for a location based on reviews, hospital proximity, police station closeness, and transit availability.
    
    Args:
        place_name (str): Name of the location.
        rating (float): Average rating.
        review_count (int): Review count.
        dist_to_hospital (float): Geodesic distance in km to nearest hospital.
        dist_to_police (float): Geodesic distance in km to nearest police unit.
        dist_to_transit (float): Geodesic distance in km to transit.
        
    Returns:
        dict: Calculated safety percentage score, tier classification, and disclaimer details.
    """
    return SafetyService.assess_safety(place_name, rating, review_count, dist_to_hospital, dist_to_police, dist_to_transit)

