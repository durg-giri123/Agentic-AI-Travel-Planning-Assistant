"""
Command-Line Interface (CLI) for Agentic AI Travel Planning Assistant.
Run interactively or with command-line arguments.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

from src.agent import TravelPlannerAgent
from src.config import CITY_COORDINATES
from src.database import init_db, save_itinerary_to_db
from src.models import TravelQuery
from src.utils.formatting import format_itinerary_standard_text, format_itinerary_rich_markdown, export_itinerary_json


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Agentic AI Travel Planning Assistant (LangChain & Autonomous Multi-Tool ReAct Agent)"
    )
    parser.add_argument("--origin", type=str, help="Source / departure city (e.g., Delhi, Mumbai, Bangalore)")
    parser.add_argument("--destination", type=str, help="Destination city (e.g., Goa, Jaipur, Kolkata)")
    parser.add_argument("--days", type=int, default=3, help="Duration of trip in days (3-7, default: 3)")
    parser.add_argument("--travelers", type=int, default=1, help="Number of travelers (default: 1)")
    parser.add_argument("--start-date", type=str, help="Start date YYYY-MM-DD (default: 7 days from today)")
    parser.add_argument("--budget-tier", type=str, choices=["budget", "moderate", "luxury"], default="budget", help="Budget tier")
    parser.add_argument("--hotel-stars", type=int, choices=[1, 2, 3, 4, 5], default=3, help="Minimum hotel star rating")
    parser.add_argument("--flight-pref", type=str, choices=["cheapest", "fastest", "earliest"], default="cheapest", help="Flight sorting priority")
    parser.add_argument("--llm-provider", type=str, choices=["autonomous", "openai", "gemini", "groq"], default="autonomous", help="Agent execution engine")
    parser.add_argument("--api-key", type=str, help="Optional LLM API key")
    parser.add_argument("--save", action="store_true", help="Save the generated itinerary to SQLite database")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    parser.add_argument("--rich", action="store_true", help="Output rich detailed Markdown format")
    return parser.parse_args()


def interactive_prompt():
    """Interactive console wizard for user inputs."""
    print("=" * 60)
    print("  🌍 Welcome to Agentic AI Travel Planning Assistant")
    print("  Powered by LangChain, Multi-Tool Reasoning & Open-Meteo")
    print("=" * 60)

    cities = list(CITY_COORDINATES.keys())
    print(f"\nSupported Major Hubs: {', '.join(cities)}\n")

    origin = input("Enter departure city (Origin) [Default: Delhi]: ").strip() or "Delhi"
    destination = input("Enter destination city [Default: Goa]: ").strip() or "Goa"
    
    days_str = input("Trip duration in days (3 to 7) [Default: 3]: ").strip() or "3"
    try:
        days = max(1, min(14, int(days_str)))
    except ValueError:
        days = 3

    travelers_str = input("Number of travelers [Default: 1]: ").strip() or "1"
    try:
        travelers = max(1, int(travelers_str))
    except ValueError:
        travelers = 1

    default_start = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    start_date = input(f"Trip start date (YYYY-MM-DD) [Default: {default_start}]: ").strip() or default_start

    print("\nBudget Tiers: 1. Budget  2. Moderate  3. Luxury")
    tier_choice = input("Select tier (1/2/3) [Default: 1]: ").strip()
    tier_map = {"1": "budget", "2": "moderate", "3": "luxury"}
    budget_tier = tier_map.get(tier_choice, "budget")

    stars_str = input("Minimum Hotel Star Rating (1 to 5) [Default: 4]: ").strip() or "4"
    try:
        hotel_stars = max(1, min(5, int(stars_str)))
    except ValueError:
        hotel_stars = 4

    print("\nFlight Priority: 1. Cheapest  2. Fastest  3. Earliest")
    flight_choice = input("Select priority (1/2/3) [Default: 1]: ").strip()
    flight_map = {"1": "cheapest", "2": "fastest", "3": "earliest"}
    flight_pref = flight_map.get(flight_choice, "cheapest")

    save_choice = input("\nSave itinerary to SQLite database? (y/n) [Default: y]: ").strip().lower()
    save_db = save_choice != "n"

    return {
        "origin": origin,
        "destination": destination,
        "days": days,
        "travelers": travelers,
        "start_date": start_date,
        "budget_tier": budget_tier,
        "hotel_stars": hotel_stars,
        "flight_pref": flight_pref,
        "llm_provider": "autonomous",
        "api_key": None,
        "save": save_db,
        "json": False,
        "rich": False
    }


def main():
    # Ensure UTF-8 output encoding for terminals
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    init_db()

    args = parse_arguments()

    if not args.origin or not args.destination:
        params = interactive_prompt()
    else:
        params = {
            "origin": args.origin,
            "destination": args.destination,
            "days": args.days,
            "travelers": args.travelers,
            "start_date": args.start_date or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "budget_tier": args.budget_tier,
            "hotel_stars": args.hotel_stars,
            "flight_pref": args.flight_pref,
            "llm_provider": args.llm_provider,
            "api_key": args.api_key,
            "save": args.save,
            "json": args.json,
            "rich": args.rich
        }

    print("\n⏳ Agent initializing and gathering intelligence...")
    print(f"📍 Route: {params['origin']} ➔ {params['destination']} | {params['days']} Days | {params['travelers']} Traveler(s)")

    query = TravelQuery(
        origin=params["origin"],
        destination=params["destination"],
        start_date=params["start_date"],
        days=params["days"],
        travelers=params["travelers"],
        budget_tier=params["budget_tier"],
        min_hotel_stars=params["hotel_stars"],
        flight_preference=params["flight_pref"]
    )

    agent = TravelPlannerAgent(
        llm_provider=params["llm_provider"],
        api_key=params["api_key"]
    )

    itinerary, steps = agent.plan_trip(query)

    print("\n" + "=" * 50)
    print("  🧠 AGENT REASONING TRACE")
    print("=" * 50)
    for s in steps:
        print(f"  {s}")

    print("\n" + "=" * 50)
    print("  📋 FINAL GENERATED ITINERARY")
    print("=" * 50 + "\n")

    if params["json"]:
        print(export_itinerary_json(itinerary))
    elif params["rich"]:
        print(format_itinerary_rich_markdown(itinerary))
    else:
        print(format_itinerary_standard_text(itinerary))

    if params["save"]:
        new_id = save_itinerary_to_db(itinerary.model_dump())
        print(f"\n💾 Itinerary successfully saved to database (ID: #{new_id})")


if __name__ == "__main__":
    main()
