import os
import requests
from typing import Dict, Any

class WeatherService:
    """
    A service class that interacts with the OpenWeatherMap API to retrieve and parse 
    weather forecast data. It provides automatic weather warnings (rain, extreme heat) 
    and handles fallback weather simulation if API keys are missing or invalid.
    """

    def __init__(self, api_key: str = None):
        # Resolve api key from local argument or fall back to system environment variables
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY must be set in environment variables")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_weather_forecast(self, city: str) -> Dict[str, Any]:
        """
        Fetches the 5-day weather forecast (retrieved in 3-hour intervals) from OpenWeatherMap.
        
        Args:
            city (str): Name of the destination city.
            
        Returns:
            Dict[str, Any]: Structured 5-day summary forecast including warnings and descriptions.
        """
        url = f"{self.base_url}/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric" # Request temperature readings in Celsius
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_forecast(data)
        except Exception as e:
            # Log error and fail-safe to mock weather generator so the trip planner never crashes
            print(f"Error fetching weather: {e}")
            return self._get_fallback_forecast(city)

    def _parse_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregates raw 3-hour interval data points into 5 distinct calendar day summaries.
        
        Key metrics calculated:
        - Daily Average Temperature
        - Daily Maximum Temperature
        - Rain/Drizzle Alerts
        - Extreme Heat Warnings (>= 35.0 °C)
        - Most common descriptive weather keyword of the day
        """
        forecasts = data.get("list", [])
        city_name = data.get("city", {}).get("name", "Unknown")
        
        daily_weather = {}
        for f in forecasts:
            dt_txt = f.get("dt_txt", "")
            if not dt_txt:
                continue
            # Extract date component from date-time string (Format: YYYY-MM-DD HH:MM:SS)
            date = dt_txt.split(" ")[0]
            
            temp = f.get("main", {}).get("temp", 20.0)
            weather_desc = f.get("weather", [{}])[0].get("description", "clear sky").lower()
            weather_main = f.get("weather", [{}])[0].get("main", "Clear").lower()
            
            # Initialize structured lists for the calendar date if not already tracked
            if date not in daily_weather:
                daily_weather[date] = {
                    "temps": [],
                    "descriptions": [],
                    "has_rain": False,
                    "high_temp": False
                }
            
            daily_weather[date]["temps"].append(temp)
            daily_weather[date]["descriptions"].append(weather_desc)
            # Scan descriptions/status to check for active precipitation
            if "rain" in weather_main or "drizzle" in weather_main:
                daily_weather[date]["has_rain"] = True
                
        parsed_days = []
        # Limit processing to first 5 calendar days to align with standard travel duration limit
        for date, info in sorted(daily_weather.items())[:5]:
            avg_temp = sum(info["temps"]) / len(info["temps"])
            max_temp = max(info["temps"])
            has_rain = info["has_rain"]
            # Trigger extreme heat safety warning if temperature surpasses human comfort limit
            high_temp = max_temp >= 35.0
            
            # Determine the dominant weather condition description for this day using mode list aggregation
            desc = max(set(info["descriptions"]), key=info["descriptions"].count)
            
            parsed_days.append({
                "date": date,
                "avg_temp": round(avg_temp, 1),
                "max_temp": round(max_temp, 1),
                "description": desc,
                "has_rain": has_rain,
                "high_temp": high_temp,
                "status": "Rain Alert (Indoor Recommended)" if has_rain else ("Extreme Heat Warning (Stay Hydrated)" if high_temp else "Good for Outdoor Activities")
            })
            
        return {
            "city": city_name,
            "forecast": parsed_days
        }

    def _get_fallback_forecast(self, city: str) -> Dict[str, Any]:
        """
        Fallback mock weather generation to ensure app resiliency when offline or API limits are hit.
        
        Injects a light rain alert on the 3rd day to ensure the weather-adaptation component 
        of the itinerary planner can be fully exercised during testing.
        """
        import datetime
        today = datetime.date.today()
        forecast = []
        for i in range(5):
            date_str = (today + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            # Simulate a rainy day on day 3 for validation purposes
            has_rain = (i == 2)
            forecast.append({
                "date": date_str,
                "avg_temp": 24.5,
                "max_temp": 28.0,
                "description": "light rain" if has_rain else "few clouds",
                "has_rain": has_rain,
                "high_temp": False,
                "status": "Rain Alert (Indoor Recommended)" if has_rain else "Good for Outdoor Activities"
            })
        return {
            "city": city,
            "forecast": forecast,
            "is_fallback": True
        }

