"""
Data preparation script:
Takes the original flights.json, hotels.json, places.json and enriches them
to ensure complete coverage for all 8 Indian cities (Delhi, Mumbai, Bangalore, Goa,
Hyderabad, Chennai, Kolkata, Jaipur) while preserving all original entries.
"""

import json
from pathlib import Path
import random

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CITIES = ["Delhi", "Mumbai", "Bangalore", "Goa", "Hyderabad", "Chennai", "Kolkata", "Jaipur"]

def enrich_data():
    # 1. Flights
    with open(BASE_DIR / "flights.json", "r", encoding="utf-8") as f:
        flights = json.load(f)
    
    existing_pairs = set((f["from"], f["to"]) for f in flights)
    airlines = ["IndiGo", "Air India", "SpiceJet", "Vistara", "Akasa Air"]
    
    # Ensure all city pairs have at least 2 flights
    flight_idx = 31
    for origin in CITIES:
        for dest in CITIES:
            if origin == dest:
                continue
            pair_count = sum(1 for f in flights if f["from"] == origin and f["to"] == dest)
            needed = max(0, 2 - pair_count)
            for _ in range(needed):
                airline = random.choice(airlines)
                # random departure between 06:00 and 21:00
                dep_hour = random.randint(6, 21)
                dep_min = random.choice([0, 15, 30, 45])
                dur_hours = random.choice([1, 2, 3])
                arr_hour = (dep_hour + dur_hours) % 24
                price = random.randint(2800, 7500)
                
                flights.append({
                    "flight_id": f"FL{flight_idx:04d}",
                    "airline": airline,
                    "from": origin,
                    "to": dest,
                    "departure_time": f"2025-02-12T{dep_hour:02d}:{dep_min:02d}:00",
                    "arrival_time": f"2025-02-12T{arr_hour:02d}:{dep_min:02d}:00",
                    "price": price
                })
                flight_idx += 1

    # Also add the exact flight mentioned in example in doc: IndiGo (₹4800) – Departs Delhi at 14:00 to Goa
    has_example_flight = any(f["from"] == "Delhi" and f["to"] == "Goa" and f["airline"] == "IndiGo" for f in flights)
    if not has_example_flight:
        flights.append({
            "flight_id": f"FL{flight_idx:04d}",
            "airline": "IndiGo",
            "from": "Delhi",
            "to": "Goa",
            "departure_time": "2025-02-12T14:00:00",
            "arrival_time": "2025-02-12T16:30:00",
            "price": 4800
        })
        flight_idx += 1

    # 2. Hotels
    with open(BASE_DIR / "hotels.json", "r", encoding="utf-8") as f:
        hotels = json.load(f)

    # Famous authentic hotels for each city
    extra_hotels = [
        {"name": "Sea View Resort", "city": "Goa", "stars": 4, "price_per_night": 3200, "amenities": ["wifi", "pool", "breakfast", "beachfront"]},
        {"name": "Taj Fort Aguada Resort", "city": "Goa", "stars": 5, "price_per_night": 7500, "amenities": ["wifi", "pool", "spa", "gym", "breakfast", "parking"]},
        {"name": "Zostel Goa", "city": "Goa", "stars": 3, "price_per_night": 1200, "amenities": ["wifi", "breakfast", "cafe"]},
        {"name": "The Leela Palace", "city": "Delhi", "stars": 5, "price_per_night": 8500, "amenities": ["wifi", "pool", "spa", "gym", "breakfast", "parking"]},
        {"name": "Bloomrooms @ Janpath", "city": "Delhi", "stars": 3, "price_per_night": 2800, "amenities": ["wifi", "breakfast"]},
        {"name": "Taj Mahal Palace", "city": "Mumbai", "stars": 5, "price_per_night": 9500, "amenities": ["wifi", "pool", "spa", "gym", "breakfast", "parking"]},
        {"name": "Residency Hotel Fort", "city": "Mumbai", "stars": 3, "price_per_night": 3100, "amenities": ["wifi", "breakfast", "gym"]},
        {"name": "The Oberoi", "city": "Bangalore", "stars": 5, "price_per_night": 7800, "amenities": ["wifi", "pool", "spa", "gym", "breakfast"]},
        {"name": "St. Mark's Hotel", "city": "Bangalore", "stars": 4, "price_per_night": 3400, "amenities": ["wifi", "gym", "breakfast"]},
        {"name": "ITC Grand Chola", "city": "Chennai", "stars": 5, "price_per_night": 7200, "amenities": ["wifi", "pool", "spa", "gym", "breakfast", "parking"]},
        {"name": "The Park", "city": "Chennai", "stars": 4, "price_per_night": 3100, "amenities": ["wifi", "pool", "gym", "breakfast"]},
        {"name": "Taj Falaknuma Palace", "city": "Hyderabad", "stars": 5, "price_per_night": 9000, "amenities": ["wifi", "pool", "spa", "gym", "breakfast"]},
        {"name": "Marigold Hotel", "city": "Hyderabad", "stars": 4, "price_per_night": 3300, "amenities": ["wifi", "pool", "gym", "breakfast"]},
        {"name": "The Oberoi Grand", "city": "Kolkata", "stars": 5, "price_per_night": 6800, "amenities": ["wifi", "pool", "spa", "gym", "breakfast"]},
        {"name": "Kenilworth Hotel", "city": "Kolkata", "stars": 4, "price_per_night": 3500, "amenities": ["wifi", "gym", "breakfast", "spa"]},
        {"name": "Rambagh Palace", "city": "Jaipur", "stars": 5, "price_per_night": 9200, "amenities": ["wifi", "pool", "spa", "gym", "breakfast", "parking"]},
        {"name": "Alsisar Haveli", "city": "Jaipur", "stars": 4, "price_per_night": 3600, "amenities": ["wifi", "pool", "breakfast"]},
    ]
    hotel_idx = len(hotels) + 1
    for eh in extra_hotels:
        # Check if hotel with same name & city already exists
        if not any(h["name"].lower() == eh["name"].lower() and h["city"] == eh["city"] for h in hotels):
            hotels.append({
                "hotel_id": f"HOT{hotel_idx:04d}",
                "name": eh["name"],
                "city": eh["city"],
                "stars": eh["stars"],
                "price_per_night": eh["price_per_night"],
                "amenities": eh["amenities"]
            })
            hotel_idx += 1

    # 3. Places
    with open(BASE_DIR / "places.json", "r", encoding="utf-8") as f:
        places = json.load(f)

    # Real iconic spots for each destination
    iconic_places = [
        # Goa
        {"name": "Baga Beach", "city": "Goa", "type": "beach", "rating": 4.7},
        {"name": "Candolim Market", "city": "Goa", "type": "market", "rating": 4.4},
        {"name": "Basilica of Bom Jesus", "city": "Goa", "type": "monument", "rating": 4.8},
        {"name": "Old Goa Heritage Walk", "city": "Goa", "type": "monument", "rating": 4.6},
        {"name": "Calangute Beach Water Sports", "city": "Goa", "type": "beach", "rating": 4.6},
        {"name": "Fort Aguada", "city": "Goa", "type": "fort", "rating": 4.7},
        {"name": "Dudhsagar Waterfalls", "city": "Goa", "type": "lake", "rating": 4.8},
        {"name": "Anjuna Flea Market", "city": "Goa", "type": "market", "rating": 4.3},
        {"name": "Chapora Fort", "city": "Goa", "type": "fort", "rating": 4.5},
        # Delhi
        {"name": "Red Fort", "city": "Delhi", "type": "fort", "rating": 4.7},
        {"name": "Qutub Minar", "city": "Delhi", "type": "monument", "rating": 4.8},
        {"name": "India Gate & Kartavya Path", "city": "Delhi", "type": "monument", "rating": 4.7},
        {"name": "Lotus Temple", "city": "Delhi", "type": "temple", "rating": 4.6},
        {"name": "Humayun's Tomb", "city": "Delhi", "type": "monument", "rating": 4.7},
        {"name": "Akshardham Temple", "city": "Delhi", "type": "temple", "rating": 4.9},
        {"name": "Chandni Chowk Street Food Walk", "city": "Delhi", "type": "market", "rating": 4.6},
        {"name": "National Museum", "city": "Delhi", "type": "museum", "rating": 4.5},
        # Mumbai
        {"name": "Gateway of India", "city": "Mumbai", "type": "monument", "rating": 4.8},
        {"name": "Marine Drive Promenade", "city": "Mumbai", "type": "beach", "rating": 4.8},
        {"name": "Elephanta Caves", "city": "Mumbai", "type": "monument", "rating": 4.6},
        {"name": "Chhatrapati Shivaji Maharaj Vastu Museum", "city": "Mumbai", "type": "museum", "rating": 4.7},
        {"name": "Juhu Beach", "city": "Mumbai", "type": "beach", "rating": 4.3},
        {"name": "Colaba Causeway Market", "city": "Mumbai", "type": "market", "rating": 4.4},
        {"name": "Bandra Bandstand & Fort", "city": "Mumbai", "type": "fort", "rating": 4.5},
        # Bangalore
        {"name": "Lalbagh Botanical Garden", "city": "Bangalore", "type": "park", "rating": 4.7},
        {"name": "Bangalore Palace", "city": "Bangalore", "type": "fort", "rating": 4.6},
        {"name": "Cubbon Park", "city": "Bangalore", "type": "park", "rating": 4.6},
        {"name": "Visvesvaraya Industrial & Tech Museum", "city": "Bangalore", "type": "museum", "rating": 4.7},
        {"name": "Commercial Street Shopping", "city": "Bangalore", "type": "market", "rating": 4.4},
        {"name": "Bannerghatta National Park", "city": "Bangalore", "type": "park", "rating": 4.5},
        {"name": "ISKCON Temple Bangalore", "city": "Bangalore", "type": "temple", "rating": 4.8},
        # Jaipur
        {"name": "Amber Fort & Palace", "city": "Jaipur", "type": "fort", "rating": 4.8},
        {"name": "Hawa Mahal", "city": "Jaipur", "city_tag": "Jaipur", "type": "monument", "rating": 4.7},
        {"name": "City Palace Jaipur", "city": "Jaipur", "type": "fort", "rating": 4.7},
        {"name": "Jantar Mantar Observatory", "city": "Jaipur", "type": "monument", "rating": 4.6},
        {"name": "Nahargarh Fort Sunset Point", "city": "Jaipur", "type": "fort", "rating": 4.7},
        {"name": "Johari Bazaar & Bapu Bazaar", "city": "Jaipur", "type": "market", "rating": 4.5},
        {"name": "Albert Hall Museum", "city": "Jaipur", "type": "museum", "rating": 4.6},
        # Hyderabad
        {"name": "Charminar & Laad Bazaar", "city": "Hyderabad", "type": "monument", "rating": 4.7},
        {"name": "Golconda Fort Sound & Light Show", "city": "Hyderabad", "type": "fort", "rating": 4.8},
        {"name": "Hussain Sagar Lake & Buddha Statue", "city": "Hyderabad", "type": "lake", "rating": 4.5},
        {"name": "Salar Jung Museum", "city": "Hyderabad", "type": "museum", "rating": 4.8},
        {"name": "Ramoji Film City", "city": "Hyderabad", "type": "park", "rating": 4.6},
        {"name": "Chowmahalla Palace", "city": "Hyderabad", "type": "monument", "rating": 4.7},
        # Chennai
        {"name": "Marina Beach", "city": "Chennai", "type": "beach", "rating": 4.6},
        {"name": "Kapaleeshwarar Temple", "city": "Chennai", "type": "temple", "rating": 4.8},
        {"name": "San Thome Cathedral Basilica", "city": "Chennai", "type": "monument", "rating": 4.6},
        {"name": "Fort St. George & Museum", "city": "Chennai", "type": "fort", "rating": 4.4},
        {"name": "Government Museum Chennai", "city": "Chennai", "type": "museum", "rating": 4.5},
        {"name": "T. Nagar Ranganathan Street", "city": "Chennai", "type": "market", "rating": 4.3},
        # Kolkata
        {"name": "Victoria Memorial Hall", "city": "Kolkata", "type": "monument", "rating": 4.9},
        {"name": "Howrah Bridge", "city": "Kolkata", "type": "monument", "rating": 4.7},
        {"name": "Dakshineswar Kali Temple", "city": "Kolkata", "type": "temple", "rating": 4.8},
        {"name": "Indian Museum Kolkata", "city": "Kolkata", "type": "museum", "rating": 4.7},
        {"name": "Eco Park & New Town", "city": "Kolkata", "type": "park", "rating": 4.6},
        {"name": "Park Street Dining Walk", "city": "Kolkata", "type": "market", "rating": 4.7},
    ]
    place_idx = len(places) + 1
    for ep in iconic_places:
        if not any(p["name"].lower() == ep["name"].lower() and p["city"] == ep["city"] for p in places):
            places.append({
                "place_id": f"PLC{place_idx:04d}",
                "name": ep["name"],
                "city": ep["city"],
                "type": ep["type"],
                "rating": ep["rating"]
            })
            place_idx += 1

    # Save to data/
    with open(DATA_DIR / "flights.json", "w", encoding="utf-8") as f:
        json.dump(flights, f, indent=4, ensure_ascii=False)
    with open(DATA_DIR / "hotels.json", "w", encoding="utf-8") as f:
        json.dump(hotels, f, indent=4, ensure_ascii=False)
    with open(DATA_DIR / "places.json", "w", encoding="utf-8") as f:
        json.dump(places, f, indent=4, ensure_ascii=False)

    print(f"Data successfully enriched and saved to {DATA_DIR}:")
    print(f"  Flights: {len(flights)}")
    print(f"  Hotels:  {len(hotels)}")
    print(f"  Places:  {len(places)}")

if __name__ == "__main__":
    enrich_data()
