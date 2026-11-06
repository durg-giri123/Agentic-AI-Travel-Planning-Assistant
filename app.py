"""
Streamlit Web Application: Agentic AI-Based Travel Planning Assistant Using LangChain.
"""

import json
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

from src.agent import TravelPlannerAgent
from src.config import CITY_COORDINATES, ATTRACTION_TYPES
from src.database import (
    get_connection,
    init_db,
    save_itinerary_to_db,
    get_saved_itineraries,
    get_itinerary_by_id,
    delete_itinerary_by_id,
    query_flights,
    query_hotels,
    query_places
)
from src.models import TravelQuery, TripItinerary
from src.utils.formatting import (
    format_itinerary_standard_text,
    format_itinerary_rich_markdown,
    export_itinerary_json
)

# -------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="Agentic AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on app startup
init_db()

# -------------------------------------------------------------
# Custom Styling
# -------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1E88E5, #00897B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #555;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 5px;
    }
    .badge-primary { background: #e0f2fe; color: #0369a1; }
    .badge-success { background: #dcfce7; color: #15803d; }
    .badge-warning { background: #fef9c3; color: #854d0e; }
    .badge-purple { background: #f3e8ff; color: #7e22ce; }
    .itinerary-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Sidebar: Settings & Configuration
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=600&q=80", use_container_width=True)
    st.markdown("### ⚙️ Agent Engine Configuration")

    provider = st.selectbox(
        "AI Reasoning Engine",
        options=["Autonomous Multi-Tool Agent", "OpenAI (GPT-4o)", "Google Gemini", "Groq (Llama-3.3)"],
        index=0,
        help="Select reasoning engine. Autonomous Agent works 100% out-of-the-box with no API keys required!"
    )

    api_key = None
    model_name = None

    if provider == "Autonomous Multi-Tool Agent":
        llm_mode = "autonomous"
        st.success("🟢 Ready to run! No external API key needed.")
    elif provider == "OpenAI (GPT-4o)":
        llm_mode = "openai"
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])
    elif provider == "Google Gemini":
        llm_mode = "gemini"
        api_key = st.text_input("Google AI Gemini API Key", type="password", placeholder="AIzaSy...")
        model_name = st.selectbox("Model", ["gemini-1.5-flash", "gemini-2.0-flash"])
    else:
        llm_mode = "groq"
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
        model_name = st.selectbox("Model", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])

    st.markdown("---")
    st.markdown("### ℹ️ Dataset & API Stats")
    st.markdown("""
    - **Flights:** 112 routes connecting 8 hubs
    - **Hotels:** 57 verified properties
    - **POIs:** 96 iconic attractions
    - **Weather:** Real-time Open-Meteo API
    - **Storage:** SQLite Database with Indexes
    """)

    if st.button("🔄 Reload & Reseed Database"):
        init_db(force_reload=True)
        st.success("Database reloaded successfully!")

# -------------------------------------------------------------
# Main Application Header
# -------------------------------------------------------------
st.markdown('<div class="main-header">✈️ Agentic AI Travel Planning Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous multi-tool decision agent powered by LangChain, Open-Meteo real-time weather & SQLite</div>', unsafe_allow_html=True)

# Main Navigation Tabs
tab_plan, tab_saved, tab_explorer, tab_docs = st.tabs([
    "🎯 Plan My Trip",
    "💾 Saved Itineraries",
    "📊 Dataset Explorer",
    "📘 Architecture & Rubric"
])

# =============================================================
# TAB 1: PLAN MY TRIP
# =============================================================
with tab_plan:
    st.markdown("#### 🧭 Customize Your Travel Preferences")

    cities_list = list(CITY_COORDINATES.keys())

    col_form1, col_form2 = st.columns(2)

    with col_form1:
        origin_city = st.selectbox("🛫 Departure City (From)", cities_list, index=0)  # Delhi
        dest_index = 3 if len(cities_list) > 3 else 1  # Goa
        destination_city = st.selectbox("🛬 Destination City (To)", cities_list, index=dest_index)

        default_start_date = datetime.now() + timedelta(days=7)
        travel_date = st.date_input("📅 Trip Start Date", value=default_start_date)

        trip_days = st.slider("⏱️ Trip Duration (Days)", min_value=3, max_value=7, value=3, step=1)

    with col_form2:
        num_travelers = st.number_input("👥 Number of Travelers", min_value=1, max_value=8, value=1)
        budget_tier = st.selectbox("💵 Budget Tier", ["budget", "moderate", "luxury"], index=0)

        flight_preference = st.selectbox(
            "✈️ Flight Priority",
            options=["cheapest", "fastest", "earliest"],
            index=0,
            format_func=lambda x: f"{x.capitalize()} Flight"
        )

        min_stars = st.select_slider("⭐ Minimum Hotel Stars", options=[1, 2, 3, 4, 5], value=3)

    attraction_prefs = st.multiselect(
        "🏛️ Preferred Attraction Types (Optional)",
        options=ATTRACTION_TYPES,
        default=["fort", "beach", "monument"] if destination_city == "Goa" else ["fort", "monument", "market"]
    )

    if origin_city == destination_city:
        st.warning("⚠️ Origin and Destination cities cannot be the same. Please choose different cities.")

    submit_btn = st.button("🚀 Generate Optimized Itinerary", type="primary", use_container_width=True)

    if submit_btn and origin_city != destination_city:
        query = TravelQuery(
            origin=origin_city,
            destination=destination_city,
            start_date=travel_date.strftime("%Y-%m-%d"),
            days=trip_days,
            travelers=num_travelers,
            budget_tier=budget_tier,
            preferred_types=attraction_prefs if attraction_prefs else None,
            flight_preference=flight_preference,
            min_hotel_stars=min_stars
        )

        agent = TravelPlannerAgent(
            llm_provider=llm_mode,
            api_key=api_key,
            model_name=model_name
        )

        with st.status("🤖 Agent actively reasoning and coordinating tools...", expanded=True) as status_box:
            itinerary, steps_log = agent.plan_trip(query)
            for step in steps_log:
                st.write(step)
            status_box.update(label="✅ Travel plan generated successfully!", state="complete", expanded=False)

        # Store in session state for downloading/saving
        st.session_state["current_itinerary"] = itinerary

    # Display Current Itinerary if available
    if "current_itinerary" in st.session_state:
        itinerary: TripItinerary = st.session_state["current_itinerary"]
        b = itinerary.estimated_total_budget
        fl = itinerary.flight_selected
        ht = itinerary.hotel_booked

        st.markdown("---")
        st.markdown(f"### 📍 {itinerary.trip_title}")

        # Top Metric Cards Row
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Total Budget", f"₹{int(b.total_cost):,}", f"₹{int(b.per_person_cost):,}/person")
        with m_col2:
            st.metric("Flight Fare", f"₹{int(fl.price):,}", fl.airline)
        with m_col3:
            st.metric("Hotel Rate", f"₹{int(ht.price_per_night):,}/night", f"{ht.stars}★ Property")
        with m_col4:
            avg_temp = round(sum(w.temp_max for w in itinerary.weather_forecast) / len(itinerary.weather_forecast), 1)
            first_w = itinerary.weather_forecast[0]
            st.metric("Weather Expectation", f"{avg_temp}°C Avg", f"{first_w.icon} {first_w.condition}")

        # Standard Specification Format Block (Copyable)
        st.markdown("#### 📋 Standard Output Format (Project Specification)")
        standard_text = format_itinerary_standard_text(itinerary)
        st.code(standard_text, language="markdown")

        # Detailed Cards: Flight & Hotel
        c_fl, c_ht = st.columns(2)
        with c_fl:
            st.markdown("#### 🛫 Flight Details")
            st.markdown(f"""
            <div class="itinerary-box">
                <span class="badge badge-primary">{fl.airline}</span>
                <span class="badge badge-success">ID: {fl.flight_id}</span>
                <span class="badge badge-warning">₹{int(fl.price):,}</span>
                <br><br>
                <b>Route:</b> {fl.origin} ➔ {fl.destination}<br>
                <b>Departure:</b> {fl.departure_time}<br>
                <b>Arrival:</b> {fl.arrival_time} ({fl.duration or 'Direct'})<br>
                <small style="color: #64748b;"><i>{fl.selection_reason}</i></small>
            </div>
            """, unsafe_allow_html=True)

        with c_ht:
            st.markdown("#### 🏨 Hotel Accommodation")
            amenities_badges = " ".join([f'<span class="badge badge-purple">{a}</span>' for a in ht.amenities])
            st.markdown(f"""
            <div class="itinerary-box">
                <span class="badge badge-primary">{ht.name}</span>
                <span class="badge badge-warning">{'⭐' * ht.stars} ({ht.stars}-star)</span>
                <span class="badge badge-success">₹{int(ht.price_per_night):,}/night</span>
                <br><br>
                <b>City:</b> {ht.city}<br>
                <b>Amenities:</b> {amenities_badges if amenities_badges else 'Standard'}<br>
                <small style="color: #64748b;"><i>{ht.selection_reason}</i></small>
            </div>
            """, unsafe_allow_html=True)

        # Weather Forecast Cards
        st.markdown("#### ⛅ Live Weather Forecast (Open-Meteo API)")
        w_cols = st.columns(len(itinerary.weather_forecast))
        for idx, w in enumerate(itinerary.weather_forecast):
            with w_cols[idx]:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 1.8rem;">{w.icon}</div>
                    <div style="font-weight: 700; margin-top: 5px;">Day {w.day}</div>
                    <div style="font-size: 0.85rem; color: #475569;">{w.date or ''}</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #0284c7; margin: 4px 0;">{w.temp_max}°C</div>
                    <div style="font-size: 0.8rem; color: #64748b;">Min: {w.temp_min}°C</div>
                    <div style="font-size: 0.85rem; font-weight: 500; margin-top: 4px;">{w.condition}</div>
                </div>
                """, unsafe_allow_html=True)

        # Day-by-Day Itinerary Accordion
        st.markdown("#### 🗓️ Day-wise Itinerary & Sightseeing Plan")
        for dp in itinerary.itinerary:
            with st.expander(f"📍 Day {dp.day} ({dp.date or ''}): {dp.theme}", expanded=True):
                col_d1, col_d2 = st.columns([2, 1])
                with col_d1:
                    st.markdown(f"**🌅 Morning (09:00 - 12:30):** {dp.morning_activity}")
                    st.markdown(f"**☀️ Afternoon (14:00 - 17:30):** {dp.afternoon_activity}")
                    st.markdown(f"**🌆 Evening (18:30 - 21:00):** {dp.evening_activity}")
                    st.info(f"💡 **Advisory:** {dp.meals_and_tips}")
                with col_d2:
                    st.markdown("**Featured Places:**")
                    for pl in dp.places:
                        st.markdown(f"- **{pl.name}** ({pl.type.capitalize()} • ⭐ {pl.rating})")

        # Budget Breakdown Chart & Summary
        st.markdown("#### 💰 Cost Breakdown")
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            budget_df = pd.DataFrame({
                "Component": ["Flight Tickets", "Hotel Accommodation", "Food & Local Travel"],
                "Amount (INR)": [b.flight_cost, b.hotel_cost, b.food_and_travel]
            })
            st.bar_chart(budget_df.set_index("Component"), use_container_width=True)

        with col_b2:
            st.markdown(f"""
            <div class="itinerary-box" style="margin-top: 15px;">
                <h4 style="margin-top:0;">Budget Summary</h4>
                <ul style="list-style: none; padding-left: 0; line-height: 2;">
                    <li>✈️ <b>Flights:</b> ₹{int(b.flight_cost):,}</li>
                    <li>🏨 <b>Hotels ({itinerary.days - 1} nights):</b> ₹{int(b.hotel_cost):,}</li>
                    <li>🍽️ <b>Food & Local Travel:</b> ₹{int(b.food_and_travel):,}</li>
                    <li style="border-top: 1px dashed #cbd5e1; margin-top: 8px; padding-top: 8px;">
                        <b>Grand Total:</b> <span style="font-size: 1.3rem; color: #16a34a; font-weight: 700;">₹{int(b.total_cost):,}</span>
                    </li>
                    <li><i>Cost per traveler: ₹{int(b.per_person_cost):,}</i></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # Reasoning
        st.markdown("#### 🧠 Decision Reasoning & Optimization")
        st.info(itinerary.decision_reasoning)

        # Export & Save Actions
        col_act1, col_act2, col_act3 = st.columns(3)
        with col_act1:
            if st.button("💾 Save Itinerary to Database", use_container_width=True):
                new_id = save_itinerary_to_db(itinerary.model_dump())
                st.success(f"Trip saved to database with ID #{new_id}!")
        with col_act2:
            st.download_button(
                "📥 Download Markdown Itinerary",
                data=format_itinerary_rich_markdown(itinerary),
                file_name=f"itinerary_{itinerary.destination.lower()}_{itinerary.days}days.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_act3:
            st.download_button(
                "📄 Export Structured JSON",
                data=export_itinerary_json(itinerary),
                file_name=f"itinerary_{itinerary.destination.lower()}_{itinerary.days}days.json",
                mime="application/json",
                use_container_width=True
            )

# =============================================================
# TAB 2: SAVED TRIPS
# =============================================================
with tab_saved:
    st.markdown("### 💾 Saved Itineraries (SQLite Database)")
    saved_list = get_saved_itineraries()

    if not saved_list:
        st.info("No saved itineraries found in database yet. Plan a trip in 'Plan My Trip' and click 'Save Itinerary'!")
    else:
        st.write(f"Total saved trips: **{len(saved_list)}**")
        for s in saved_list:
            with st.container():
                s_col1, s_col2, s_col3, s_col4 = st.columns([3, 2, 2, 2])
                with s_col1:
                    st.markdown(f"**#{s['id']} {s['trip_title']}**")
                    st.caption(f"Created: {s['created_at']}")
                with s_col2:
                    st.markdown(f"**Route:** {s['origin']} ➔ {s['destination']}")
                    st.caption(f"{s['days']} Days • {s['travelers']} Traveler(s)")
                with s_col3:
                    st.markdown(f"**Total Budget:** ₹{int(s['total_cost']):,}")
                with s_col4:
                    col_b_view, col_b_del = st.columns(2)
                    with col_b_view:
                        if st.button("View", key=f"view_{s['id']}"):
                            full_trip = get_itinerary_by_id(s["id"])
                            if full_trip:
                                st.session_state["current_itinerary"] = TripItinerary(**full_trip)
                                st.rerun()
                    with col_b_del:
                        if st.button("Delete", key=f"del_{s['id']}"):
                            delete_itinerary_by_id(s["id"])
                            st.rerun()
                st.divider()

# =============================================================
# TAB 3: DATASET EXPLORER
# =============================================================
with tab_explorer:
    st.markdown("### 📊 Dataset Explorer (Normalized SQLite Tables)")

    data_view = st.radio("Select Dataset to Inspect", ["Flights (flights.json)", "Hotels (hotels.json)", "Places (places.json)"], horizontal=True)

    filter_city = st.selectbox("Filter by City", ["All"] + cities_list)

    if data_view.startswith("Flights"):
        if filter_city == "All":
            conn = get_connection()
            df = pd.read_sql_query("SELECT flight_id, airline, origin, destination, departure_time, arrival_time, duration_minutes, price FROM flights LIMIT 100", conn)
            conn.close()
        else:
            conn = get_connection()
            df = pd.read_sql_query("SELECT flight_id, airline, origin, destination, departure_time, arrival_time, duration_minutes, price FROM flights WHERE origin = ? OR destination = ?", conn, params=[filter_city, filter_city])
            conn.close()

        st.dataframe(df, use_container_width=True)
        st.caption(f"Showing {len(df)} flight records.")

    elif data_view.startswith("Hotels"):
        conn = get_connection()
        if filter_city == "All":
            df = pd.read_sql_query("SELECT hotel_id, name, city, stars, price_per_night, amenities FROM hotels", conn)
        else:
            df = pd.read_sql_query("SELECT hotel_id, name, city, stars, price_per_night, amenities FROM hotels WHERE city = ?", conn, params=[filter_city])
        conn.close()

        st.dataframe(df, use_container_width=True)
        st.caption(f"Showing {len(df)} hotel records.")

    else:
        conn = get_connection()
        if filter_city == "All":
            df = pd.read_sql_query("SELECT place_id, name, city, type, rating, description FROM places", conn)
        else:
            df = pd.read_sql_query("SELECT place_id, name, city, type, rating, description FROM places WHERE city = ?", conn, params=[filter_city])
        conn.close()

        st.dataframe(df, use_container_width=True)
        st.caption(f"Showing {len(df)} attractions.")

# =============================================================
# TAB 4: ARCHITECTURE & RUBRIC
# =============================================================
with tab_docs:
    st.markdown("### 📘 System Architecture & Rubric Alignment")
    st.markdown("""
    #### 🏗️ Agentic Workflow Overview
    ```
    +-----------------------------------------------------------------------------------+
    |                              User Travel Query                                    |
    |  (Origin: Delhi, Destination: Goa, Duration: 3 Days, Budget Tier: Budget)        |
    +-----------------------------------------+-----------------------------------------+
                                              |
                                              v
    +-----------------------------------------------------------------------------------+
    |                   Agentic AI Orchestrator (LangChain / ReAct)                    |
    +-----+--------------------+--------------------+--------------------+--------------+
          |                    |                    |                    |
          v                    v                    v                    v
    +-----------+        +-----------+        +-----------+        +-----------+
    |  Flight   |        |   Hotel   |        |  Weather  |        |  Places   |
    |  Search   |        |  Recom.   |        |  Lookup   |        | Discovery |
    |   Tool    |        |   Tool    |        |   Tool    |        |   Tool    |
    +-----+-----+        +-----+-----+        +-----+-----+        +-----+-----+
          |                    |                    |                    |
          +--------------------+--------------------+--------------------+
                                              |
                                              v
                               +-----------------------------+
                               |   Budget Estimation Tool    |
                               | (Flight + Hotel + Expenses) |
                               +--------------+--------------+
                                              |
                                              v
                               +-----------------------------+
                               |     Structured Itinerary    |
                               |   & Decision Justification  |
                               +-----------------------------+
    ```

    #### 🎯 Project Objectives Addressed
    1. **Agentic AI System Using LangChain:** Autonomous multi-tool decision reasoning with LangChain tool decorators and LangGraph ReAct agent.
    2. **5 Core Tools Integrated:**
       - Flight Search Tool (reads flights dataset, filters by route/budget, sorts cheapest/fastest).
       - Hotel Recommendation Tool (reads hotels dataset, filters by stars/price/amenities).
       - Places Discovery Tool (reads places dataset, categorizes and ranks POIs).
       - Weather Lookup Tool (calls free Open-Meteo live API, maps WMO weather codes).
       - Budget Estimation Tool (computes itemized budget breakdown).
    3. **SQL Database Practices:** SQLite database with indexed queries on routes, city ratings, and saved itineraries.
    4. **Output Conformity:** Generates exact formatted output requested in project specification document.
    5. **Streamlit UI:** Responsive layout, interactive controls, live reasoning logs, and data export.
    """)
