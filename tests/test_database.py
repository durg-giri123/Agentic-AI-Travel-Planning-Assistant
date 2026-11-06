"""
Unit tests for Database Operations (SQLite).
"""

import os
from pathlib import Path
import pytest
from src.database import (
    init_db,
    query_flights,
    query_hotels,
    query_places,
    save_itinerary_to_db,
    get_saved_itineraries,
    get_itinerary_by_id,
    delete_itinerary_by_id
)

TEST_DB_PATH = Path("test_travel_planner.db")


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Create test database fixture."""
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)
    init_db(db_path=TEST_DB_PATH, force_reload=True)
    yield
    if TEST_DB_PATH.exists():
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass


def test_database_flights_query():
    flights = query_flights("Bangalore", "Delhi", limit=5)
    assert len(flights) > 0
    for fl in flights:
        assert fl["origin"].lower() == "bangalore"
        assert fl["destination"].lower() == "delhi"


def test_database_hotels_query():
    hotels = query_hotels("Delhi", min_stars=2, limit=5)
    assert len(hotels) > 0
    for h in hotels:
        assert h["city"].lower() == "delhi"
        assert h["stars"] >= 2


def test_database_places_query():
    places = query_places("Mumbai", min_rating=3.5, limit=5)
    assert len(places) > 0
    for p in places:
        assert p["city"].lower() == "mumbai"
        assert p["rating"] >= 3.5


def test_database_itinerary_crud():
    sample_itinerary = {
        "trip_title": "Test 3-Day Trip to Jaipur",
        "origin": "Delhi",
        "destination": "Jaipur",
        "start_date": "2025-03-01",
        "end_date": "2025-03-03",
        "days": 3,
        "travelers": 1,
        "flight_selected": {"airline": "IndiGo", "price": 3500},
        "hotel_booked": {"name": "Test Haveli", "stars": 4, "price_per_night": 2800},
        "estimated_total_budget": {"total_cost": 12500.0},
        "decision_reasoning": "Test reasoning"
    }

    # Save
    itinerary_id = save_itinerary_to_db(sample_itinerary)
    assert itinerary_id is not None
    assert itinerary_id > 0

    # Retrieve
    saved = get_saved_itineraries()
    assert len(saved) > 0
    assert any(s["id"] == itinerary_id for s in saved)

    single = get_itinerary_by_id(itinerary_id)
    assert single is not None
    assert single["trip_title"] == "Test 3-Day Trip to Jaipur"

    # Delete
    deleted = delete_itinerary_by_id(itinerary_id)
    assert deleted is True
    assert get_itinerary_by_id(itinerary_id) is None
