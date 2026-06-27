import os
import requests
from typing import Dict, Any

class WeatherService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY must be set in environment variables")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_weather_forecast(self, city: str) -> Dict[str, Any]:
        """Fetches the 5-day / 3-hour forecast for the given city."""
        url = f"{self.base_url}/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_forecast(data)
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return self._get_fallback_forecast(city)

    def _parse_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parses forecast data to identify rain, high temps, and daily summaries."""
        forecasts = data.get("list", [])
        city_name = data.get("city", {}).get("name", "Unknown")
        
        daily_weather = {}
        for f in forecasts:
            dt_txt = f.get("dt_txt", "")
            if not dt_txt:
                continue
            date = dt_txt.split(" ")[0]
            
            temp = f.get("main", {}).get("temp", 20.0)
            weather_desc = f.get("weather", [{}])[0].get("description", "clear sky").lower()
            weather_main = f.get("weather", [{}])[0].get("main", "Clear").lower()
            
            if date not in daily_weather:
                daily_weather[date] = {
                    "temps": [],
                    "descriptions": [],
                    "has_rain": False,
                    "high_temp": False
                }
            
            daily_weather[date]["temps"].append(temp)
            daily_weather[date]["descriptions"].append(weather_desc)
            if "rain" in weather_main or "drizzle" in weather_main:
                daily_weather[date]["has_rain"] = True
                
        parsed_days = []
        for date, info in sorted(daily_weather.items())[:5]:
            avg_temp = sum(info["temps"]) / len(info["temps"])
            max_temp = max(info["temps"])
            has_rain = info["has_rain"]
            high_temp = max_temp >= 35.0
            
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
        """Provides dynamic fallback forecast data if API is down or invalid."""
        import datetime
        today = datetime.date.today()
        forecast = []
        for i in range(5):
            date_str = (today + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
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
