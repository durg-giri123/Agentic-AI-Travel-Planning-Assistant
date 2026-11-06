"""
Integration tests for TravelPlannerAgent and Formatting.
"""

import pytest
from src.agent import TravelPlannerAgent
from src.models import TravelQuery, TripItinerary
from src.utils.formatting import (
    format_itinerary_standard_text,
    format_itinerary_rich_markdown,
    export_itinerary_json
)


def test_agent_plan_trip_basic():
    """Verify autonomous agent plans a valid trip."""
    agent = TravelPlannerAgent(llm_provider="autonomous")
    query = TravelQuery(
        origin="Delhi",
        destination="Goa",
        start_date="2025-02-12",
        days=3,
        travelers=1,
        budget_tier="budget",
        flight_preference="cheapest",
        min_hotel_stars=4
    )

    itinerary, steps = agent.plan_trip(query)

    assert isinstance(itinerary, TripItinerary)
    assert itinerary.origin == "Delhi"
    assert itinerary.destination == "Goa"
    assert itinerary.days == 3
    assert len(itinerary.itinerary) == 3
    assert len(itinerary.weather_forecast) == 3
    assert itinerary.flight_selected is not None
    assert itinerary.flight_selected.price > 0
    assert itinerary.hotel_booked is not None
    assert itinerary.hotel_booked.stars >= 4
    assert itinerary.estimated_total_budget.total_cost > 0
    assert len(steps) >= 5


def test_format_itinerary_standard_text():
    """Verify standard text matches the format expected by the project rubric."""
    agent = TravelPlannerAgent(llm_provider="autonomous")
    query = TravelQuery(
        origin="Delhi",
        destination="Goa",
        start_date="2025-02-12",
        days=3,
        travelers=1,
        budget_tier="budget"
    )

    itinerary, _ = agent.plan_trip(query)
    text = format_itinerary_standard_text(itinerary)

    assert "Your 3-Day Trip to Goa" in text
    assert "Flight Selected:" in text
    assert "Hotel Booked:" in text
    assert "Weather:" in text
    assert "Itinerary:" in text
    assert "Day 1:" in text
    assert "Day 2:" in text
    assert "Day 3:" in text
    assert "Estimated Total Budget:" in text
    assert "Total Cost: ₹" in text


def test_rich_markdown_and_json():
    """Verify markdown formatting and JSON export."""
    agent = TravelPlannerAgent(llm_provider="autonomous")
    query = TravelQuery(
        origin="Mumbai",
        destination="Jaipur",
        start_date="2025-04-10",
        days=4,
        travelers=2,
        budget_tier="moderate"
    )

    itinerary, _ = agent.plan_trip(query)
    md = format_itinerary_rich_markdown(itinerary)
    assert "# ✈️" in md
    assert "Estimated Budget Breakdown" in md

    json_str = export_itinerary_json(itinerary)
    assert '"trip_title"' in json_str
    assert '"flight_selected"' in json_str
