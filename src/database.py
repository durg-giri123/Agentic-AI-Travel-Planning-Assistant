"""
SQLite Database Layer for Agentic AI Travel Planner.
Handles normalization, indexing, querying, and persistent trip itinerary storage.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import DATABASE_PATH, FLIGHTS_FILE, HOTELS_FILE, PLACES_FILE


def get_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Create and return a database connection with dict-like row access."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DATABASE_PATH, force_reload: bool = False) -> None:
    """
    Initialize SQLite database schema, create normalized tables,
    indexes for fast querying, and seed with flight, hotel, and places data.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Flights Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id TEXT UNIQUE NOT NULL,
            airline TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Indexes on flights for origin-destination search and price ordering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flights_route ON flights(origin, destination)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flights_price ON flights(price)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flights_duration ON flights(duration_minutes)")

    # 2. Hotels Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            stars INTEGER NOT NULL,
            price_per_night REAL NOT NULL,
            amenities TEXT NOT NULL
        )
    """)

    # Indexes on hotels for city, star ratings, and price
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotels_city ON hotels(city)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotels_city_stars ON hotels(city, stars)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hotels_price ON hotels(price_per_night)")

    # 3. Places Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            type TEXT NOT NULL,
            rating REAL NOT NULL,
            description TEXT
        )
    """)

    # Indexes on places for city, type, and rating
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_city ON places(city)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_city_type ON places(city, type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_places_rating ON places(rating)")

    # 4. Saved Trip Itineraries Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_itineraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trip_title TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days INTEGER NOT NULL,
            travelers INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            flight_info TEXT,
            hotel_info TEXT,
            itinerary_json TEXT NOT NULL,
            summary TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_dest ON saved_itineraries(destination)")

    conn.commit()

    # Seed data if tables are empty or force_reload is True
    cursor.execute("SELECT COUNT(*) FROM flights")
    flights_count = cursor.fetchone()[0]

    if flights_count == 0 or force_reload:
        _seed_data(conn, cursor)

    conn.close()


def _compute_duration_minutes(departure_time: str, arrival_time: str) -> int:
    """Calculate flight duration in minutes handling date cross-over."""
    try:
        fmt = "%Y-%m-%dT%H:%M:%S"
        dep = datetime.strptime(departure_time, fmt)
        arr = datetime.strptime(arrival_time, fmt)
        diff = int((arr - dep).total_seconds() / 60)
        return diff if diff > 0 else diff + 1440
    except Exception:
        return 120  # default 2 hours


def _seed_data(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """Seed data from JSON files into normalized tables."""
    # Seed Flights
    if FLIGHTS_FILE.exists():
        with open(FLIGHTS_FILE, "r", encoding="utf-8") as f:
            flights = json.load(f)
            for fl in flights:
                dur = _compute_duration_minutes(fl["departure_time"], fl["arrival_time"])
                cursor.execute("""
                    INSERT OR REPLACE INTO flights 
                    (flight_id, airline, origin, destination, departure_time, arrival_time, duration_minutes, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fl["flight_id"],
                    fl["airline"],
                    fl["from"],
                    fl["to"],
                    fl["departure_time"],
                    fl["arrival_time"],
                    dur,
                    float(fl["price"])
                ))

    # Seed Hotels
    if HOTELS_FILE.exists():
        with open(HOTELS_FILE, "r", encoding="utf-8") as f:
            hotels = json.load(f)
            for ht in hotels:
                amenities_str = json.dumps(ht.get("amenities", []))
                cursor.execute("""
                    INSERT OR REPLACE INTO hotels 
                    (hotel_id, name, city, stars, price_per_night, amenities)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ht["hotel_id"],
                    ht["name"],
                    ht["city"],
                    int(ht["stars"]),
                    float(ht["price_per_night"]),
                    amenities_str
                ))

    # Seed Places
    if PLACES_FILE.exists():
        with open(PLACES_FILE, "r", encoding="utf-8") as f:
            places = json.load(f)
            for pl in places:
                cursor.execute("""
                    INSERT OR REPLACE INTO places 
                    (place_id, name, city, type, rating, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pl["place_id"],
                    pl["name"],
                    pl["city"],
                    pl["type"],
                    float(pl["rating"]),
                    pl.get("description", f"Popular {pl['type']} in {pl['city']}")
                ))

    conn.commit()


# ==========================================
# Query Functions
# ==========================================

def query_flights(
    origin: str,
    destination: str,
    max_price: Optional[float] = None,
    preferred_airline: Optional[str] = None,
    sort_by: str = "cheapest",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Query flights between origin and destination with optional filters.
    sort_by: 'cheapest' (lowest price), 'fastest' (shortest duration), 'earliest' (departure time).
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT flight_id, airline, origin, destination, departure_time, arrival_time, duration_minutes, price
        FROM flights
        WHERE LOWER(origin) = LOWER(?) AND LOWER(destination) = LOWER(?)
    """
    params = [origin.strip(), destination.strip()]

    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    if preferred_airline:
        query += " AND LOWER(airline) LIKE LOWER(?)"
        params.append(f"%{preferred_airline.strip()}%")

    if sort_by == "cheapest":
        query += " ORDER BY price ASC, duration_minutes ASC"
    elif sort_by == "fastest":
        query += " ORDER BY duration_minutes ASC, price ASC"
    elif sort_by == "earliest":
        query += " ORDER BY time(departure_time) ASC, price ASC"
    else:
        query += " ORDER BY price ASC"

    query += f" LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        hours = r["duration_minutes"] // 60
        mins = r["duration_minutes"] % 60
        dur_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        results.append({
            "flight_id": r["flight_id"],
            "airline": r["airline"],
            "origin": r["origin"],
            "destination": r["destination"],
            "departure_time": r["departure_time"],
            "arrival_time": r["arrival_time"],
            "duration": dur_str,
            "duration_minutes": r["duration_minutes"],
            "price": r["price"],
        })
    return results


def query_hotels(
    city: str,
    min_stars: int = 1,
    max_price_per_night: Optional[float] = None,
    required_amenities: Optional[List[str]] = None,
    sort_by: str = "best_value",
    limit: int = 6
) -> List[Dict[str, Any]]:
    """
    Query hotels for a city with rating, price, and amenity filters.
    sort_by: 'best_value' (rating/price ratio), 'cheapest' (price asc), 'highest_rated' (stars desc).
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT hotel_id, name, city, stars, price_per_night, amenities
        FROM hotels
        WHERE LOWER(city) = LOWER(?) AND stars >= ?
    """
    params = [city.strip(), min_stars]

    if max_price_per_night is not None:
        query += " AND price_per_night <= ?"
        params.append(max_price_per_night)

    if sort_by == "cheapest":
        query += " ORDER BY price_per_night ASC, stars DESC"
    elif sort_by == "highest_rated":
        query += " ORDER BY stars DESC, price_per_night ASC"
    else:  # best_value: prefer higher stars with moderate price
        query += " ORDER BY stars DESC, price_per_night ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    req_amenities_lower = [a.lower().strip() for a in (required_amenities or [])]

    for r in rows:
        try:
            amenities = json.loads(r["amenities"])
        except Exception:
            amenities = []

        amenities_lower = [a.lower() for a in amenities]

        # Check amenity match if requested
        if req_amenities_lower:
            if not all(any(req in a for a in amenities_lower) for req in req_amenities_lower):
                continue

        results.append({
            "hotel_id": r["hotel_id"],
            "name": r["name"],
            "city": r["city"],
            "stars": r["stars"],
            "price_per_night": r["price_per_night"],
            "amenities": amenities,
        })
        if len(results) >= limit:
            break

    return results


def query_places(
    city: str,
    types: Optional[List[str]] = None,
    min_rating: float = 3.5,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Query attractions in a city, filtered by type and rating.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT place_id, name, city, type, rating, description
        FROM places
        WHERE LOWER(city) = LOWER(?) AND rating >= ?
    """
    params = [city.strip(), min_rating]

    if types:
        placeholders = ",".join(["?"] * len(types))
        query += f" AND LOWER(type) IN ({placeholders})"
        params.extend([t.lower().strip() for t in types])

    query += " ORDER BY rating DESC, name ASC"
    query += f" LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "place_id": r["place_id"],
            "name": r["name"],
            "city": r["city"],
            "type": r["type"],
            "rating": r["rating"],
            "description": r["description"] or f"Must-visit {r['type']} in {r['city']}"
        })
    return results


# ==========================================
# Itinerary Persistence Functions
# ==========================================

def save_itinerary_to_db(itinerary_data: Dict[str, Any]) -> int:
    """Save a planned itinerary into SQLite database."""
    conn = get_connection()
    cursor = conn.cursor()

    flight_info = json.dumps(itinerary_data.get("flight_selected", {}))
    hotel_info = json.dumps(itinerary_data.get("hotel_booked", {}))
    itinerary_json = json.dumps(itinerary_data, ensure_ascii=False)

    cursor.execute("""
        INSERT INTO saved_itineraries 
        (trip_title, origin, destination, start_date, end_date, days, travelers, total_cost, flight_info, hotel_info, itinerary_json, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        itinerary_data.get("trip_title", "Custom Trip"),
        itinerary_data.get("origin", ""),
        itinerary_data.get("destination", ""),
        itinerary_data.get("start_date", ""),
        itinerary_data.get("end_date", ""),
        itinerary_data.get("days", 3),
        itinerary_data.get("travelers", 1),
        itinerary_data.get("estimated_total_budget", {}).get("total_cost", 0.0),
        flight_info,
        hotel_info,
        itinerary_json,
        itinerary_data.get("decision_reasoning", "")
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_saved_itineraries() -> List[Dict[str, Any]]:
    """Retrieve all saved itineraries ordered by creation date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, created_at, trip_title, origin, destination, start_date, end_date, days, travelers, total_cost, summary
        FROM saved_itineraries
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_itinerary_by_id(itinerary_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single saved itinerary by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT itinerary_json FROM saved_itineraries WHERE id = ?", (itinerary_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row["itinerary_json"])
    return None


def delete_itinerary_by_id(itinerary_id: int) -> bool:
    """Delete a saved itinerary by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_itineraries WHERE id = ?", (itinerary_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
