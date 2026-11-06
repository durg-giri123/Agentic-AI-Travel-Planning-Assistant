"""
Flight Search Tool for LangChain Agent.
Searches flights.json / database for flights matching origin and destination,
with sorting by cheapest or fastest and budget filtering.
"""

import json
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.database import query_flights


class FlightSearchInput(BaseModel):
    origin: str = Field(description="Departure / origin city name (e.g. 'Delhi', 'Bangalore', 'Mumbai')")
    destination: str = Field(description="Destination city name (e.g. 'Goa', 'Kolkata', 'Hyderabad')")
    sort_by: str = Field(default="cheapest", description="Sort order: 'cheapest' (lowest price), 'fastest' (least travel time), or 'earliest'")
    max_price: Optional[float] = Field(default=None, description="Maximum flight ticket price in INR")
    preferred_airline: Optional[str] = Field(default=None, description="Preferred airline filter e.g. 'IndiGo', 'Air India'")
    limit: int = Field(default=5, description="Maximum number of flight options to return")


def run_flight_search(
    origin: str,
    destination: str,
    sort_by: str = "cheapest",
    max_price: Optional[float] = None,
    preferred_airline: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Execute flight search against database."""
    return query_flights(
        origin=origin,
        destination=destination,
        max_price=max_price,
        preferred_airline=preferred_airline,
        sort_by=sort_by,
        limit=limit
    )


@tool(args_schema=FlightSearchInput)
def search_flights_tool(
    origin: str,
    destination: str,
    sort_by: str = "cheapest",
    max_price: Optional[float] = None,
    preferred_airline: Optional[str] = None,
    limit: int = 5
) -> str:
    """
    Search available flights from an origin city to a destination city.
    Returns flight options including flight ID, airline, departure time, arrival time, duration, and price in INR.
    Use this tool whenever you need to select the best flight for a trip.
    """
    try:
        results = run_flight_search(
            origin=origin,
            destination=destination,
            sort_by=sort_by,
            max_price=max_price,
            preferred_airline=preferred_airline,
            limit=limit
        )
        if not results:
            return json.dumps({
                "status": "not_found",
                "message": f"No direct flights found from {origin} to {destination} with current filters.",
                "flights": []
            })
        return json.dumps({
            "status": "success",
            "count": len(results),
            "flights": results
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error searching flights: {str(e)}"})
