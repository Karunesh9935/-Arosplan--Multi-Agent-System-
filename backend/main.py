# ============================================================
# AI Travel Planning System - backend/main.py
# Multi-Agent System using LangGraph + Groq + PostgreSQL
# ============================================================

# ── Standard Library ────────────────────────────────────────
import os
import sys
import re
import uuid
import operator
from typing import TypedDict, Annotated

# Force UTF-8 encoding for standard output and error to support emojis on Windows
if sys.stdout and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ── LangGraph ───────────────────────────────────────────────
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

# ── LangChain ───────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

# ── Database ─────────────────────────────────────────────────
import psycopg
from psycopg_pool import ConnectionPool

# ── Tools ────────────────────────────────────────────────────
from tools.flight_tool import search_flights
from tools.tavily_tool import tavily_search
from tools.budget_tool import calculate_budget, parse_budget_from_query

# ── Environment Variables ────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
print(groq_api_key)  # Debug

# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError(
        "DATABASE_URL is missing. Add it to your .env file.\n"
        "Example: postgresql://postgres:password@localhost:5432/langgraph_memory"
    )

# LLM - Groq with Llama 3.3 70B
llm = ChatGroq(model="llama-3.3-70b-versatile")


# ============================================================
# STATE DEFINITION
# Shared memory that all agents read from and write to
# ============================================================

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # chat history
    user_query: str        # original user input
    flight_results: str    # output from flight agent
    hotel_results: str     # output from hotel agent
    itinerary: str         # output from itinerary agent
    budget_analysis: str   # output from budget agent
    budget: float          # extracted budget amount (0 = not specified)
    llm_calls: int         # tracks how many LLM calls were made


# ============================================================
# UTILITY FUNCTION
# Extract budget amount from natural language
# Example: "trip under 2 lakhs" → 200000.0
# ============================================================

def extract_budget(query: str) -> float:
    """
    Extracts budget from user query text.
    Handles: '2 lakhs', '1.5 lakh', 'under 50000', '₹1L'
    Returns 0.0 if no budget is mentioned.
    """
    query_lower = query.lower()

    # Match "2 lakh", "1.5 lakhs", "2L"
    lakh_match = re.search(
        r'(\d+\.?\d*)\s*(lakh|lakhs|l\b)', query_lower
    )
    # Match "under 50000", "₹50000"
    number_match = re.search(
        r'under\s*₹?(\d+)', query_lower
    )

    if lakh_match:
        return float(lakh_match.group(1)) * 100000
    elif number_match:
        return float(number_match.group(1))

    return 0.0


# ============================================================
# AGENT 1: FLIGHT AGENT
# Searches for flights based on user query
# Falls back gracefully if API fails
# ============================================================

def flight_agent(state: TravelState) -> dict:
    try:
        flight_data = search_flights(state["user_query"])

        # Handle empty result from API
        if not flight_data or len(flight_data.strip()) == 0:
            flight_data = (
                "No flights found for this route. "
                "Try different dates or nearby airports."
            )

    except Exception as e:
        # Any API crash — return safe fallback message
        flight_data = "Flight search temporarily unavailable."

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content=f"Flight search completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# ============================================================
# AGENT 2: HOTEL AGENT
# Searches for hotels using Tavily web search
# Falls back gracefully if search fails
# ============================================================

def hotel_agent(state: TravelState) -> dict:
    try:
        query = f"Best hotels for {state['user_query']}"
        hotel_results = tavily_search(query)

        # Handle empty result
        if not hotel_results or len(hotel_results.strip()) == 0:
            hotel_results = (
                "No hotel results found. "
                "Try Booking.com or MakeMyTrip directly."
            )

    except Exception as e:
        hotel_results = "Hotel search temporarily unavailable."

    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel search completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# ============================================================
# AGENT 3: ITINERARY AGENT
# Creates a day-by-day travel plan using flight + hotel data
# ============================================================

def itinerary_agent(state: TravelState) -> dict:
    prompt = f"""
    Create a detailed day-by-day travel itinerary.

    User Query: {state['user_query']}

    Available Flights:
    {state['flight_results']}

    Available Hotels:
    {state['hotel_results']}

    Include:
    - Day-by-day schedule
    - Sightseeing and activities
    - Travel time between locations
    - Food recommendations
    """

    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# ============================================================
# AGENT 4: BUDGET AGENT (ownership feature)
# Estimates total trip cost and checks against user budget
# Uses budget_tool for calculation, LLM for interpretation
# ============================================================

def budget_agent(state: TravelState) -> dict:
    # Step 1: Use tool for actual number extraction
    budget_data = calculate_budget(
        flight_results=state["flight_results"],
        hotel_results=state["hotel_results"],
        query=state["user_query"]
    )

    # Step 2: LLM interprets and explains in human-readable format
    prompt = f"""
    User Query: {state['user_query']}
    User Budget: ₹{budget_data['user_budget']} (0 = not specified)
    Estimated Cost from results: {budget_data['estimated_total'] or 'Could not extract from results'}
    Budget Status: {budget_data['status']}

    Based on this data:
    1. Give a clear budget summary
    2. If OVER budget — suggest 3 specific cost-cutting options
    3. If FITS or UNDER budget — suggest useful upgrades or extras
    4. If UNKNOWN — give a realistic cost estimate for this trip type

    Respond in this exact format:
    ESTIMATED COST: [amount in ₹]
    BUDGET STATUS: [fits/over/under/unknown]
    RECOMMENDATION: [your specific advice]
    """

    response = llm.invoke([
        SystemMessage(content="You are a travel budget expert."),
        HumanMessage(content=prompt)
    ])

    return {
        "budget_analysis": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# ============================================================
# AGENT 5: FINAL RESPONSE AGENT
# Combines all outputs into one clean travel plan
# ============================================================

def final_agent(state: TravelState) -> dict:
    prompt = f"""
    Create a complete, well-formatted travel plan combining all information below.

    User Request: {state['user_query']}

    Flight Options:
    {state['flight_results']}

    Hotel Options:
    {state['hotel_results']}

    Travel Itinerary:
    {state['itinerary']}

    Budget Analysis:
    {state['budget_analysis']}

    Format the response clearly with sections:
    1. Trip Summary
    2. Flights
    3. Hotels
    4. Day-by-Day Itinerary
    5. Budget Summary
    6. Important Tips

    Total LLM calls used in this session: {state['llm_calls']}
    """

    response = llm.invoke([
        SystemMessage(content="You are a professional travel consultant."),
        HumanMessage(content=prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# ============================================================
# FALLBACK NODES
# These run when flight or hotel search returns no results
# Agents reroute here instead of crashing
# ============================================================

def no_flight_fallback(state: TravelState) -> dict:
    """Runs when flight agent finds no results."""
    response = llm.invoke([
        SystemMessage(content="You are a travel expert."),
        HumanMessage(content=(
            f"Flights not found for: {state['user_query']}. "
            f"Suggest 3 alternative travel options — "
            f"different dates, nearby airports, or train/bus options."
        ))
    ])
    return {
        "flight_results": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def no_hotel_fallback(state: TravelState) -> dict:
    """Runs when hotel agent finds no results."""
    response = llm.invoke([
        SystemMessage(content="You are a travel expert."),
        HumanMessage(content=(
            f"Hotels not found for: {state['user_query']}. "
            f"Suggest accommodation types available — "
            f"hostels, guesthouses, Airbnb options."
        ))
    ])
    return {
        "hotel_results": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


# ============================================================
# ROUTING FUNCTIONS
# Decide which node to go to next based on agent output
# This is what makes it a real multi-agent system
# ============================================================

def route_after_flights(state: TravelState) -> str:
    """
    After flight agent runs:
    - If flights found → go to hotel agent
    - If no flights → go to fallback node
    """
    flight_data = state.get("flight_results", "")

    if (
        "unavailable" in flight_data.lower() or
        "no flights" in flight_data.lower()
    ):
        return "no_flight_fallback"

    return "hotel_agent"


def route_after_hotels(state: TravelState) -> str:
    """
    After hotel agent runs:
    - If hotels found → go to itinerary agent
    - If no hotels → go to fallback node
    """
    hotel_data = state.get("hotel_results", "")

    if (
        "unavailable" in hotel_data.lower() or
        "no hotel" in hotel_data.lower()
    ):
        return "no_hotel_fallback"

    return "itinerary_agent"


# ============================================================
# GRAPH DEFINITION
# Wires all agents together into one system
# Flow: Flight → Hotel → Itinerary → Budget → Final
# ============================================================

graph = StateGraph(TravelState)

# ── Register all nodes ──────────────────────────────────────
graph.add_node("flight_agent",       flight_agent)
graph.add_node("hotel_agent",        hotel_agent)
graph.add_node("itinerary_agent",    itinerary_agent)
graph.add_node("budget_agent",       budget_agent)
graph.add_node("final_agent",        final_agent)
graph.add_node("no_flight_fallback", no_flight_fallback)
graph.add_node("no_hotel_fallback",  no_hotel_fallback)

# ── Define edges (flow between agents) ──────────────────────

# Start → Flight Agent
graph.add_edge(START, "flight_agent")

# Flight Agent → conditional: found flights or fallback
graph.add_conditional_edges(
    "flight_agent",
    route_after_flights,
    {
        "hotel_agent":        "hotel_agent",
        "no_flight_fallback": "no_flight_fallback"
    }
)

# Flight fallback rejoins main flow at hotel agent
graph.add_edge("no_flight_fallback", "hotel_agent")

# Hotel Agent → conditional: found hotels or fallback
graph.add_conditional_edges(
    "hotel_agent",
    route_after_hotels,
    {
        "itinerary_agent":   "itinerary_agent",
        "no_hotel_fallback": "no_hotel_fallback"
    }
)

# Hotel fallback rejoins main flow at itinerary agent
graph.add_edge("no_hotel_fallback", "itinerary_agent")

# Itinerary → Budget → Final → End
graph.add_edge("itinerary_agent", "budget_agent")
graph.add_edge("budget_agent",    "final_agent")
graph.add_edge("final_agent",     END)


# ============================================================
# DATABASE + MEMORY SETUP
# PostgreSQL stores conversation history across sessions
# ConnectionPool handles multiple users safely
# ============================================================

# Execute DB migrations with autocommit=True (avoids transaction block index creation error)
try:
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        migration_checkpointer = PostgresSaver(conn)
        migration_checkpointer.setup()
except Exception as e:
    print(f"⚡ Database migration setup warning: {e}")

# Normal ConnectionPool for the running app
pool = ConnectionPool(DATABASE_URL)
checkpointer = PostgresSaver(pool)

# Compile graph with memory
app = graph.compile(checkpointer=checkpointer)


# ============================================================
# ENTRY POINT - Terminal interface
# ============================================================

if __name__ == "__main__":
    print("\n🌍 AI Travel Planning System")
    print("=" * 40)

    user_input = input("Enter your travel request: ").strip()

    if not user_input:
        print("No input provided. Exiting.")
        exit()

    # Extract budget from natural language
    budget = extract_budget(user_input)

    if budget > 0:
        print(f"💰 Budget detected: ₹{budget:,.0f}")
    else:
        print("💰 No budget specified — open plan.")

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    print("\n⏳ Planning your trip...\n")

    result = app.invoke(
        {
            "messages":       [HumanMessage(content=user_input)],
            "user_query":     user_input,
            "flight_results": "",
            "hotel_results":  "",
            "itinerary":      "",
            "budget_analysis": "",
            "budget":         budget,
            "llm_calls":      0
        },
        config=config
    )

    print("\n" + "=" * 40)
    print("✈️  TRAVEL PLAN")
    print("=" * 40 + "\n")

    final_messages = result.get("messages", [])
    if final_messages:
        print(final_messages[-1].content)

    print(f"\n📊 Total LLM calls: {result.get('llm_calls', 0)}")

    # Cleanly close database connection pool
    try:
        pool.close()
    except Exception:
        pass
