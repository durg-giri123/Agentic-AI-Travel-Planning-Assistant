"""
Configuration and constants for Agentic AI Travel Planning Assistant.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = BASE_DIR / "travel_planner.db"

# Data file locations (check data/ first, fallback to root)
FLIGHTS_FILE = DATA_DIR / "flights.json" if (DATA_DIR / "flights.json").exists() else BASE_DIR / "flights.json"
HOTELS_FILE = DATA_DIR / "hotels.json" if (DATA_DIR / "hotels.json").exists() else BASE_DIR / "hotels.json"
PLACES_FILE = DATA_DIR / "places.json" if (DATA_DIR / "places.json").exists() else BASE_DIR / "places.json"

# Supported Indian Cities with accurate Geocoding coordinates (lat, lon)
CITY_COORDINATES = {
    "Delhi": {"lat": 28.6139, "lon": 77.2090, "state": "Delhi"},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "state": "Maharashtra"},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka"},
    "Goa": {"lat": 15.2993, "lon": 74.1240, "state": "Goa"},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana"},
    "Chennai": {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu"},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal"},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan"},
}

# Weather Code Mapping (WMO weather codes from Open-Meteo)
WMO_WEATHER_CODES = {
    0: ("Clear Sky", "☀️", "Outdoor activities highly recommended"),
    1: ("Mainly Clear", "🌤️", "Great weather for sightseeing"),
    2: ("Partly Cloudy", "⛅", "Pleasant conditions for outdoor travel"),
    3: ("Overcast", "☁️", "Good for both indoor and outdoor activities"),
    45: ("Foggy", "🌫️", "Expect low visibility in early mornings"),
    48: ("Depositing Rime Fog", "🌫️", "Drive carefully in morning hours"),
    51: ("Light Drizzle", "🌦️", "Carry a light umbrella or raincoat"),
    53: ("Moderate Drizzle", "🌦️", "Light rain expected; plan mix of indoor spots"),
    55: ("Dense Drizzle", "🌧️", "Rainy day; indoor museums & shopping advised"),
    61: ("Slight Rain", "🌧️", "Occasional showers; keep rain gear handy"),
    63: ("Moderate Rain", "🌧️", "Steady rain; ideal for indoor attractions & cafes"),
    65: ("Heavy Rain", "⛈️", "Heavy rain; stay indoors or visit covered venues"),
    71: ("Slight Snowfall", "🌨️", "Cold weather gear required"),
    73: ("Moderate Snowfall", "🌨️", "Winter travel conditions"),
    75: ("Heavy Snowfall", "❄️", "Extreme cold; limit outdoor duration"),
    80: ("Slight Rain Showers", "🌦️", "Passing showers possible"),
    81: ("Moderate Rain Showers", "🌧️", "Intermittent showers"),
    82: ("Violent Rain Showers", "⛈️", "Strong downpours; stay sheltered"),
    95: ("Thunderstorm", "⛈️", "Thunderstorm alerts; avoid beaches or high forts"),
    96: ("Thunderstorm with Slight Hail", "⛈️", "Severe weather; remain indoors"),
    99: ("Thunderstorm with Heavy Hail", "⛈️", "Severe storm warning"),
}

# Default Daily Expense Estimates (INR per person per day)
DAILY_EXPENSE_TIERS = {
    "budget": 1000,      # Street food, public transit, free/low-cost monuments
    "moderate": 1800,    # Good cafes/restaurants, autos/cabs, entry tickets
    "luxury": 3500,      # Fine dining, private chauffeurs, premium experiences
}

# Supported Airlines
AIRLINES = ["IndiGo", "Air India", "SpiceJet", "Go First", "Vistara", "Akasa Air"]

# Attraction categories
ATTRACTION_TYPES = ["fort", "temple", "museum", "lake", "beach", "park", "market", "monument"]
