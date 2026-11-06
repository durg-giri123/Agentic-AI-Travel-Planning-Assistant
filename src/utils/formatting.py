"""
Formatting and presentation helpers for Trip Itineraries.
Generates human-readable text, structured Markdown, and exportable JSON.
"""

import json
from datetime import datetime
from typing import Dict, Any
from src.models import TripItinerary


def format_itinerary_standard_text(itinerary: TripItinerary) -> str:
    """
    Format the itinerary into the exact human-readable format required by project specifications.
    """
    # 1. Title
    title = itinerary.trip_title

    # 2. Flight Selected
    fl = itinerary.flight_selected
    dep_time_str = fl.departure_time
    try:
        dt = datetime.strptime(fl.departure_time, "%Y-%m-%dT%H:%M:%S")
        dep_time_str = dt.strftime("%H:%M")
    except Exception:
        pass
    flight_line = f"- {fl.airline} (₹{int(fl.price):,}) – Departs {fl.origin} at {dep_time_str}"

    # 3. Hotel Booked
    ht = itinerary.hotel_booked
    hotel_line = f"- {ht.name} (₹{int(ht.price_per_night):,}/night, {ht.stars}-star)"

    # 4. Weather
    weather_lines = []
    for w in itinerary.weather_forecast:
        weather_lines.append(f"- Day {w.day}: {w.condition} ({int(w.temp_max)}°C)")
    weather_block = "\n".join(weather_lines)

    # 5. Itinerary
    day_lines = []
    for dp in itinerary.itinerary:
        # Collect attraction names
        place_names = [p.name for p in dp.places]
        if not place_names:
            place_names = [dp.morning_activity, dp.afternoon_activity]
        places_str = ", ".join(place_names)
        day_lines.append(f"Day {dp.day}: {places_str}")
    itinerary_block = "\n".join(day_lines)

    # 6. Budget
    b = itinerary.estimated_total_budget
    budget_block = (
        f"- Flight: ₹{int(b.flight_cost):,}\n"
        f"- Hotel: ₹{int(b.hotel_cost):,}\n"
        f"- Food & Travel: ₹{int(b.food_and_travel):,}\n"
        f"-------------------------------------\n"
        f"Total Cost: ₹{int(b.total_cost):,}"
    )

    # 7. Reasoning
    reasoning_block = ""
    if itinerary.decision_reasoning:
        reasoning_block = f"\n\nReasoning:\n{itinerary.decision_reasoning}"

    output = (
        f"{title}\n\n"
        f"Flight Selected:\n{flight_line}\n\n"
        f"Hotel Booked:\n{hotel_line}\n\n"
        f"Weather:\n{weather_block}\n\n"
        f"Itinerary:\n{itinerary_block}\n\n"
        f"Estimated Total Budget:\n{budget_block}"
        f"{reasoning_block}"
    )
    return output


def format_itinerary_rich_markdown(itinerary: TripItinerary) -> str:
    """Format rich detailed markdown with badges, table summaries, and day timelines."""
    fl = itinerary.flight_selected
    ht = itinerary.hotel_booked
    b = itinerary.estimated_total_budget

    md = f"""# ✈️ {itinerary.trip_title}

### 📋 Overview
- **Route:** {itinerary.origin} ➔ {itinerary.destination}
- **Travel Dates:** {itinerary.start_date} to {itinerary.end_date} ({itinerary.days} Days)
- **Travelers:** {itinerary.travelers} Person(s)
- **Total Estimated Budget:** **₹{int(b.total_cost):,}** (₹{int(b.per_person_cost):,}/person)

---

### 🛫 Flight Selected
- **Airline:** `{fl.airline}` | **Flight ID:** `{fl.flight_id}`
- **Route:** {fl.origin} ➔ {fl.destination}
- **Departure:** {fl.departure_time} | **Arrival:** {fl.arrival_time} ({fl.duration or 'Direct'})
- **Ticket Price:** **₹{int(fl.price):,}** per person
*Why selected:* {fl.selection_reason or 'Best value and schedule match.'}

---

### 🏨 Hotel Booked
- **Property:** **{ht.name}** ({ht.stars} ⭐)
- **Location:** {ht.city}
- **Nightly Rate:** **₹{int(ht.price_per_night):,}**/night
- **Amenities:** {', '.join(ht.amenities) if ht.amenities else 'Standard amenities'}
*Why selected:* {ht.selection_reason or 'High star rating and convenient location.'}

---

### ⛅ Live Weather Forecast
| Day | Date | Condition | Temperature | Advisory |
| :--- | :--- | :--- | :--- | :--- |
"""
    for w in itinerary.weather_forecast:
        md += f"| Day {w.day} | {w.date or '-'} | {w.icon} {w.condition} | {w.temp_min}°C – {w.temp_max}°C | {w.tip or 'Pleasant'} |\n"

    md += """
---

### 🗓️ Day-wise Itinerary
"""
    for dp in itinerary.itinerary:
        md += f"""#### 📍 Day {dp.day}: {dp.theme or f'Exploring {itinerary.destination}'}
- **Morning (09:00 - 12:30):** {dp.morning_activity}
- **Afternoon (14:00 - 17:30):** {dp.afternoon_activity}
- **Evening (18:30 - 21:00):** {dp.evening_activity}
- 💡 **Local Tip:** {dp.meals_and_tips or 'Enjoy local delicacies and convenient public transit.'}

"""

    md += f"""---

### 💰 Estimated Budget Breakdown
| Component | Cost (INR) | Details |
| :--- | :--- | :--- |
| **Flights** | ₹{int(b.flight_cost):,} | {itinerary.travelers} traveler(s) |
| **Accommodation** | ₹{int(b.hotel_cost):,} | {itinerary.days - 1} night(s) at {ht.name} |
| **Food & Local Travel** | ₹{int(b.food_and_travel):,} | {itinerary.days} day(s) meals & transit |
| **Contingency Buffer** | ₹{int(b.buffer_cost):,} | Safety cushion |
| **TOTAL TRIP COST** | **₹{int(b.total_cost):,}** | **₹{int(b.per_person_cost):,} per person** |

---

### 🧠 Decision Reasoning & Optimization
{itinerary.decision_reasoning or 'This itinerary balances cost efficiency with top attractions and weather compatibility.'}
"""
    return md


def export_itinerary_json(itinerary: TripItinerary) -> str:
    """Export complete itinerary as clean JSON."""
    return json.dumps(itinerary.model_dump(), indent=2, ensure_ascii=False)
