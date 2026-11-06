"""
Weather API Integration using Open-Meteo (Free, no API key required).
Provides live forecasts, weather code mapping, and seasonal fallbacks.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests

from src.config import CITY_COORDINATES, WMO_WEATHER_CODES
from src.models import DayWeather


def geocode_city(city_name: str) -> Optional[Dict[str, float]]:
    """
    Look up latitude and longitude for a city.
    First checks local configured coordinates; if missing, calls Open-Meteo Geocoding API.
    """
    clean_name = city_name.strip().title()
    if clean_name in CITY_COORDINATES:
        return {
            "lat": CITY_COORDINATES[clean_name]["lat"],
            "lon": CITY_COORDINATES[clean_name]["lon"]
        }

    # Fallback to Open-Meteo free geocoding
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name.strip()}&count=1&language=en&format=json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                return {
                    "lat": float(results[0]["latitude"]),
                    "lon": float(results[0]["longitude"])
                }
    except Exception:
        pass

    # Default to center of India if totally unknown
    return {"lat": 20.5937, "lon": 78.9629}


def fetch_weather_forecast(
    city: str,
    start_date: Optional[str] = None,
    days: int = 3
) -> List[DayWeather]:
    """
    Fetch weather forecast for a destination city from Open-Meteo API.
    Returns a list of DayWeather objects for each day of the trip.
    """
    coords = geocode_city(city)
    lat = coords["lat"]
    lon = coords["lon"]

    # Clamp days between 1 and 7 (standard free forecast window)
    forecast_days = max(1, min(days, 7))

    api_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max&"
        f"forecast_days={forecast_days}&timezone=auto"
    )

    try:
        response = requests.get(api_url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            times = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            weather_codes = daily.get("weathercode", [])
            rain_probs = daily.get("precipitation_probability_max", [])

            results: List[DayWeather] = []
            for i in range(min(days, len(times))):
                code = weather_codes[i] if i < len(weather_codes) else 0
                cond_name, icon, default_tip = WMO_WEATHER_CODES.get(
                    code, ("Pleasant Weather", "🌤️", "Good day for sightseeing")
                )
                
                max_t = round(float(max_temps[i]), 1) if i < len(max_temps) else 30.0
                min_t = round(float(min_temps[i]), 1) if i < len(min_temps) else 20.0
                rain_prob = rain_probs[i] if i < len(rain_probs) else 0

                tip = default_tip
                if rain_prob and rain_prob > 40:
                    tip = f"Rain chance {rain_prob}%; consider indoor spots in afternoon"

                results.append(DayWeather(
                    day=i + 1,
                    date=times[i],
                    condition=cond_name,
                    icon=icon,
                    temp_max=max_t,
                    temp_min=min_t,
                    tip=tip
                ))

            if results:
                return results

    except Exception as err:
        # Graceful fallback on network/timeout error
        pass

    # Fallback to realistic estimates if offline or API blocked
    return _generate_fallback_weather(city, start_date, days)


def _generate_fallback_weather(city: str, start_date: Optional[str], days: int) -> List[DayWeather]:
    """Generate realistic seasonal weather estimates if live API is temporarily unavailable."""
    clean_city = city.strip().title()
    # Baseline climate profiles
    city_profiles = {
        "Goa": (31.5, 23.0, "Sunny", "☀️", "Warm & sunny beach weather; carry sunscreen"),
        "Delhi": (26.0, 14.5, "Partly Cloudy", "⛅", "Pleasant daytime, cooler evenings"),
        "Mumbai": (32.0, 24.0, "Sunny with Sea Breeze", "🌤️", "Humid and sunny; stay hydrated"),
        "Bangalore": (28.0, 18.0, "Pleasant & Breezy", "⛅", "Ideal sightseeing conditions"),
        "Chennai": (33.0, 25.0, "Warm & Humid", "☀️", "Tropical weather; wear light cottons"),
        "Hyderabad": (30.0, 20.0, "Mainly Clear", "🌤️", "Great weather for heritage walks"),
        "Kolkata": (29.0, 21.0, "Clear Sky", "☀️", "Sunny and comfortable for exploring"),
        "Jaipur": (27.5, 15.0, "Sunny & Dry", "☀️", "Warm sunny days; perfect for visiting forts"),
    }

    base_max, base_min, cond, icon, tip = city_profiles.get(
        clean_city, (29.0, 20.0, "Pleasant", "🌤️", "Good day for sightseeing")
    )

    results = []
    base_date = datetime.now()
    if start_date:
        try:
            base_date = datetime.strptime(start_date, "%Y-%m-%d")
        except Exception:
            pass

    variations = [
        (0.0, cond, icon),
        (+1.2, "Partly Cloudy", "⛅"),
        (-0.8, "Light Breeze", "🌤️"),
        (+0.5, "Sunny", "☀️"),
        (-1.0, "Mainly Clear", "🌤️"),
        (+1.5, "Warm & Pleasant", "☀️"),
        (-0.5, "Partly Cloudy", "⛅"),
    ]

    for d in range(1, days + 1):
        dt = base_date + timedelta(days=d - 1)
        var_temp, day_cond, day_icon = variations[(d - 1) % len(variations)]
        results.append(DayWeather(
            day=d,
            date=dt.strftime("%Y-%m-%d"),
            condition=day_cond,
            icon=day_icon,
            temp_max=round(base_max + var_temp, 1),
            temp_min=round(base_min + (var_temp * 0.5), 1),
            tip=tip
        ))

    return results
