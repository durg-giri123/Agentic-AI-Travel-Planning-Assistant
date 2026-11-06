"""
Hotel Recommendation Tool for LangChain Agent.
Searches hotels.json / database for hotels matching city, rating, budget, and amenities.
"""

import json
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.database import query_hotels


class HotelSearchInput(BaseModel):
    city: str = Field(description="Destination city name (e.g. 'Goa', 'Delhi', 'Mumbai', 'Jaipur')")
    min_stars: int = Field(default=3, description="Minimum star rating (1 to 5)")
    max_price_per_night: Optional[float] = Field(default=None, description="Maximum budget per night in INR")
    required_amenities: Optional[List[str]] = Field(default=None, description="Required amenities e.g. ['wifi', 'pool', 'breakfast', 'spa']")
    sort_by: str = Field(default="best_value", description="Sort criteria: 'best_value', 'cheapest', or 'highest_rated'")
    limit: int = Field(default=5, description="Maximum number of hotel options to return")


def run_hotel_recommendation(
    city: str,
    min_stars: int = 3,
    max_price_per_night: Optional[float] = None,
    required_amenities: Optional[List[str]] = None,
    sort_by: str = "best_value",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Execute hotel search against database."""
    return query_hotels(
        city=city,
        min_stars=min_stars,
        max_price_per_night=max_price_per_night,
        required_amenities=required_amenities,
        sort_by=sort_by,
        limit=limit
    )


@tool(args_schema=HotelSearchInput)
def hotel_recommendation_tool(
    city: str,
    min_stars: int = 3,
    max_price_per_night: Optional[float] = None,
    required_amenities: Optional[List[str]] = None,
    sort_by: str = "best_value",
    limit: int = 5
) -> str:
    """
    Search and recommend hotels in a destination city based on star ratings, price per night, and amenities.
    Returns hotel ID, name, city, stars (1-5), price per night in INR, and amenities list.
    Use this tool to find optimal accommodation for the user's stay.
    """
    try:
        results = run_hotel_recommendation(
            city=city,
            min_stars=min_stars,
            max_price_per_night=max_price_per_night,
            required_amenities=required_amenities,
            sort_by=sort_by,
            limit=limit
        )
        if not results:
            # Fallback relaxing filters if none match strict amenities
            results = run_hotel_recommendation(
                city=city,
                min_stars=max(1, min_stars - 1),
                max_price_per_night=None,
                required_amenities=None,
                sort_by="cheapest",
                limit=limit
            )

        if not results:
            return json.dumps({
                "status": "not_found",
                "message": f"No hotels found in {city} matching criteria.",
                "hotels": []
            })

        return json.dumps({
            "status": "success",
            "count": len(results),
            "hotels": results
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error searching hotels: {str(e)}"})
