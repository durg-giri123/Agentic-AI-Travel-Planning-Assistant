"""
Places Discovery Tool for LangChain Agent.
Discovers and recommends attractions and points of interest (POIs) from places.json / database.
"""

import json
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.database import query_places


class PlacesSearchInput(BaseModel):
    city: str = Field(description="Destination city (e.g. 'Goa', 'Delhi', 'Jaipur', 'Mumbai')")
    categories: Optional[List[str]] = Field(default=None, description="Attraction types e.g. ['fort', 'beach', 'temple', 'museum', 'lake', 'park', 'market', 'monument']")
    min_rating: float = Field(default=3.5, description="Minimum visitor rating (out of 5.0)")
    limit: int = Field(default=12, description="Maximum number of attractions to return")


def run_places_discovery(
    city: str,
    categories: Optional[List[str]] = None,
    min_rating: float = 3.5,
    limit: int = 12
) -> List[Dict[str, Any]]:
    """Execute places discovery query."""
    return query_places(
        city=city,
        types=categories,
        min_rating=min_rating,
        limit=limit
    )


@tool(args_schema=PlacesSearchInput)
def places_discovery_tool(
    city: str,
    categories: Optional[List[str]] = None,
    min_rating: float = 3.5,
    limit: int = 12
) -> str:
    """
    Discover tourist attractions and sights in a destination city.
    Filters by categories such as 'fort', 'beach', 'temple', 'museum', 'lake', 'park', 'market', 'monument',
    and sorts by visitor rating.
    Use this tool to plan day-by-day sightseeing itineraries.
    """
    try:
        results = run_places_discovery(
            city=city,
            categories=categories,
            min_rating=min_rating,
            limit=limit
        )
        if not results:
            # Fallback without category filter
            results = run_places_discovery(
                city=city,
                categories=None,
                min_rating=3.0,
                limit=limit
            )

        if not results:
            return json.dumps({
                "status": "not_found",
                "message": f"No places found for {city}.",
                "places": []
            })

        return json.dumps({
            "status": "success",
            "count": len(results),
            "places": results
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error discovering places: {str(e)}"})
