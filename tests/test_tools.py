"""
Unit tests for the 5 LangChain Travel Tools.
"""

import json
import pytest
from src.tools import (
    search_flights_tool,
    hotel_recommendation_tool,
    places_discovery_tool,
    weather_lookup_tool,
    budget_estimation_tool,
    run_flight_search,
    run_hotel_recommendation,
    run_places_discovery,
    run_weather_lookup,
    run_budget_estimation
)


def test_flight_tool_basic():
    """Test flight search returns valid flights between major cities."""
    results = run_flight_search("Delhi", "Goa", sort_by="cheapest", limit=3)
    assert len(results) > 0
    assert results[0]["origin"].lower() == "delhi"
    assert results[0]["destination"].lower() == "goa"
    assert results[0]["price"] > 0
    assert "duration" in results[0]


def test_flight_tool_tool_invoke():
    """Test LangChain flight search tool invocation returns valid JSON."""
    raw = search_flights_tool.invoke({"origin": "Mumbai", "destination": "Bangalore", "sort_by": "fastest"})
    data = json.loads(raw)
    assert data["status"] == "success"
    assert "flights" in data
    assert len(data["flights"]) > 0


def test_hotel_tool_basic():
    """Test hotel recommendations with star rating filters."""
    results = run_hotel_recommendation("Goa", min_stars=4, limit=5)
    assert len(results) > 0
    for h in results:
        assert h["stars"] >= 4
        assert h["city"].lower() == "goa"


def test_hotel_tool_tool_invoke():
    """Test LangChain hotel tool invocation returns valid JSON."""
    raw = hotel_recommendation_tool.invoke({"city": "Delhi", "min_stars": 3})
    data = json.loads(raw)
    assert data["status"] == "success"
    assert len(data["hotels"]) > 0


def test_places_tool_basic():
    """Test places discovery for specific city and categories."""
    results = run_places_discovery("Jaipur", categories=["fort"], limit=5)
    assert len(results) > 0
    for p in results:
        assert p["city"].lower() == "jaipur"
        assert p["type"].lower() == "fort"
        assert p["rating"] >= 3.5


def test_places_tool_tool_invoke():
    """Test LangChain places tool invocation returns valid JSON."""
    raw = places_discovery_tool.invoke({"city": "Goa", "categories": ["beach"]})
    data = json.loads(raw)
    assert data["status"] == "success"
    assert len(data["places"]) > 0


def test_weather_tool():
    """Test weather lookup returns forecast days."""
    results = run_weather_lookup("Goa", days=3)
    assert len(results) == 3
    for w in results:
        assert "condition" in w
        assert "temp_max" in w
        assert "temp_min" in w
        assert w["temp_max"] >= w["temp_min"]


def test_weather_tool_tool_invoke():
    """Test LangChain weather tool invocation returns valid JSON."""
    raw = weather_lookup_tool.invoke({"city": "Mumbai", "days": 3})
    data = json.loads(raw)
    assert data["status"] == "success"
    assert "forecast" in data
    assert len(data["forecast"]) == 3


def test_budget_tool():
    """Test budget calculation math matches expectation."""
    # 1 traveler, 3 days, 2 nights
    # flight: 4800, hotel: 3200 * 2 = 6400, food & travel: 2500 -> total: 13,700
    res = run_budget_estimation(
        flight_price=4800.0,
        hotel_price_per_night=3200.0,
        num_nights=2,
        num_days=3,
        daily_expense_tier="budget",
        custom_daily_expense=833.3333333333334,
        num_travelers=1
    )
    assert res["flight_cost"] == 4800.0
    assert res["hotel_cost"] == 6400.0
    assert round(res["food_and_travel"]) == 2500
    assert round(res["total_cost"]) == 13700


def test_budget_tool_tool_invoke():
    """Test LangChain budget tool invocation returns valid JSON."""
    raw = budget_estimation_tool.invoke({
        "flight_price": 5000,
        "hotel_price_per_night": 3000,
        "num_nights": 3,
        "num_days": 4,
        "daily_expense_tier": "moderate",
        "num_travelers": 2
    })
    data = json.loads(raw)
    assert data["status"] == "success"
    b = data["budget"]
    assert b["flight_cost"] == 10000.0  # 5000 * 2 travelers
    assert b["hotel_cost"] == 9000.0   # 3000 * 3 nights * 1 room
    assert b["total_cost"] > 0
