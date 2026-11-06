"""
Budget Estimation Tool for LangChain Agent.
Sums flight cost, hotel stay, and per-day local expenses (food, transport, entry fees)
to provide a complete and itemized trip cost calculation.
"""

import json
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.config import DAILY_EXPENSE_TIERS


class BudgetEstimationInput(BaseModel):
    flight_price: float = Field(description="One-way or round-trip ticket price per person in INR")
    hotel_price_per_night: float = Field(description="Price per night for the hotel room in INR")
    num_nights: int = Field(description="Number of hotel nights booked")
    num_days: int = Field(description="Total duration of the trip in days")
    daily_expense_tier: str = Field(default="moderate", description="Tier for daily food & local transit: 'budget' (₹1000/day), 'moderate' (₹1800/day), or 'luxury' (₹3500/day)")
    custom_daily_expense: Optional[float] = Field(default=None, description="Optional custom daily expense per person in INR")
    num_travelers: int = Field(default=1, description="Number of travelers")
    buffer_percentage: float = Field(default=0.0, description="Contingency buffer percentage (e.g. 0.05 for 5%)")


def run_budget_estimation(
    flight_price: float,
    hotel_price_per_night: float,
    num_nights: int,
    num_days: int,
    daily_expense_tier: str = "moderate",
    custom_daily_expense: Optional[float] = None,
    num_travelers: int = 1,
    buffer_percentage: float = 0.0
) -> Dict[str, Any]:
    """Calculate itemized budget breakdown."""
    # Flight cost for all travelers
    total_flight = flight_price * num_travelers

    # Hotel cost (assumes 1 room per 2 travelers)
    rooms_needed = max(1, (num_travelers + 1) // 2)
    total_hotel = hotel_price_per_night * num_nights * rooms_needed

    # Daily expenses (food + local travel)
    if custom_daily_expense is not None and custom_daily_expense > 0:
        per_day_per_person = custom_daily_expense
    else:
        per_day_per_person = DAILY_EXPENSE_TIERS.get(daily_expense_tier.lower(), 1800)

    total_food_travel = per_day_per_person * num_days * num_travelers

    subtotal = total_flight + total_hotel + total_food_travel
    buffer_amount = round(subtotal * buffer_percentage, 2)
    total_budget = round(subtotal + buffer_amount, 2)
    per_person = round(total_budget / num_travelers, 2)

    return {
        "flight_cost": round(total_flight, 2),
        "hotel_cost": round(total_hotel, 2),
        "food_and_travel": round(total_food_travel, 2),
        "buffer_cost": buffer_amount,
        "total_cost": total_budget,
        "per_person_cost": per_person,
        "currency": "INR",
        "breakdown_summary": (
            f"Flight: ₹{int(total_flight):,}, "
            f"Hotel ({num_nights} nights): ₹{int(total_hotel):,}, "
            f"Food & Travel ({num_days} days): ₹{int(total_food_travel):,} -> "
            f"Total: ₹{int(total_budget):,}"
        )
    }


@tool(args_schema=BudgetEstimationInput)
def budget_estimation_tool(
    flight_price: float,
    hotel_price_per_night: float,
    num_nights: int,
    num_days: int,
    daily_expense_tier: str = "moderate",
    custom_daily_expense: Optional[float] = None,
    num_travelers: int = 1,
    buffer_percentage: float = 0.0
) -> str:
    """
    Calculate the total estimated trip budget by summing flight tickets, hotel stay,
    and daily food & local transportation expenses.
    Returns an itemized breakdown with flight cost, hotel cost, food & local travel cost,
    and grand total in INR.
    Use this tool as the final step in travel planning to compute exact expenses.
    """
    try:
        breakdown = run_budget_estimation(
            flight_price=flight_price,
            hotel_price_per_night=hotel_price_per_night,
            num_nights=num_nights,
            num_days=num_days,
            daily_expense_tier=daily_expense_tier,
            custom_daily_expense=custom_daily_expense,
            num_travelers=num_travelers,
            buffer_percentage=buffer_percentage
        )
        return json.dumps({
            "status": "success",
            "budget": breakdown
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error calculating budget: {str(e)}"})
