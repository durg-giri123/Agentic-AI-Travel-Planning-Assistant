"""
Weather Lookup Tool for LangChain Agent.
Calls free Open-Meteo API to retrieve weather forecasts for travel dates.
"""

import json
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.utils.weather_api import fetch_weather_forecast


class WeatherLookupInput(BaseModel):
    city: str = Field(description="Destination city name (e.g. 'Goa', 'Delhi', 'Jaipur', 'Bangalore')")
    start_date: Optional[str] = Field(default=None, description="Trip start date YYYY-MM-DD")
    days: int = Field(default=3, description="Number of days for the trip (1 to 7)")


def run_weather_lookup(
    city: str,
    start_date: Optional[str] = None,
    days: int = 3
) -> List[Dict[str, Any]]:
    """Execute weather lookup and return dict representations."""
    weather_objects = fetch_weather_forecast(city=city, start_date=start_date, days=days)
    return [w.model_dump() for w in weather_objects]


@tool(args_schema=WeatherLookupInput)
def weather_lookup_tool(
    city: str,
    start_date: Optional[str] = None,
    days: int = 3
) -> str:
    """
    Lookup real-time and forecast weather conditions for a destination city.
    Calls the Open-Meteo API to retrieve daily maximum and minimum temperatures,
    sky condition (Sunny, Partly Cloudy, Light Rain), weather icons, and sightseeing recommendations.
    Use this tool to inform activity choices (outdoor vs indoor) and day-wise weather expectations.
    """
    try:
        forecast = run_weather_lookup(city=city, start_date=start_date, days=days)
        return json.dumps({
            "status": "success",
            "city": city,
            "days_forecasted": len(forecast),
            "forecast": forecast
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error fetching weather: {str(e)}"})
