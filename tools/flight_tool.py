import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

def extract_airport_code(query: str) -> dict:
    """
    Extract rough origin/destination from query text.
    Maps common city names to IATA codes.
    """
    city_to_iata = {
        "delhi": "DEL",
        "mumbai": "BOM",
        "bangalore": "BLR",
        "chennai": "MAA",
        "kolkata": "CCU",
        "hyderabad": "HYD",
        "tokyo": "NRT",
        "japan": "NRT",
        "dubai": "DXB",
        "london": "LHR",
        "new york": "JFK",
        "paris": "CDG",
        "singapore": "SIN",
        "bangkok": "BKK",
        "bali": "DPS",
    }

    query_lower = query.lower()
    found = []
    for city, code in city_to_iata.items():
        if city in query_lower:
            found.append(code)

    return {
        "dep_iata": found[0] if len(found) > 0 else None,
        "arr_iata": found[1] if len(found) > 1 else None
    }


def search_flights(query: str) -> str:
    """
    Search flights based on user query.
    Extracts origin/destination from query text.
    """

    if not API_KEY:
        return "Flight search unavailable: API key not configured."

    # Extract airport codes from query
    airports = extract_airport_code(query)

    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": API_KEY,
        "limit": 5
    }

    # Add filters only if found in query
    # Note: dep_iata/arr_iata filtering requires paid AviationStack plan
    # On free plan we fetch live flights and filter manually
    if airports["dep_iata"]:
        params["dep_iata"] = airports["dep_iata"]

    try:
        response = requests.get(url, params=params, timeout=10)

        # Check HTTP errors
        if response.status_code == 401:
            return "Flight search failed: Invalid API key. Check your AVIATIONSTACK_API_KEY."

        if response.status_code == 429:
            return "Flight search failed: API rate limit reached. Try again later."

        if response.status_code != 200:
            return f"Flight search failed: API returned status {response.status_code}."

        data = response.json()

        # AviationStack returns error inside JSON on free plan violations
        if "error" in data:
            error_msg = data["error"].get("info", "Unknown API error")
            return f"Flight search unavailable: {error_msg}"

        if "data" not in data or len(data["data"]) == 0:
            return (
                f"No live flights found"
                f"{' from ' + airports['dep_iata'] if airports['dep_iata'] else ''}. "
                f"For trip planning purposes, consider checking MakeMyTrip or Google Flights "
                f"for routes matching your query: {query}"
            )

        # Build flight results
        flights = []
        for flight in data["data"][:5]:
            airline   = flight.get("airline", {}).get("name", "Unknown Airline")
            dep_airport = flight.get("departure", {}).get("airport", "Unknown")
            dep_time    = flight.get("departure", {}).get("scheduled", "N/A")
            arr_airport = flight.get("arrival", {}).get("airport", "Unknown")
            arr_time    = flight.get("arrival", {}).get("scheduled", "N/A")
            status      = flight.get("flight_status", "Unknown")
            flight_num  = flight.get("flight", {}).get("iata", "N/A")

            flights.append(
                f"Flight: {flight_num} | Airline: {airline}\n"
                f"  From: {dep_airport} at {dep_time}\n"
                f"  To:   {arr_airport} at {arr_time}\n"
                f"  Status: {status}"
            )

        header = f"Flights found for query: '{query}'\n"
        if airports["dep_iata"]:
            header += f"Filtered by departure: {airports['dep_iata']}\n"
        header += "-" * 40 + "\n"

        return header + "\n\n".join(flights)

    except requests.exceptions.Timeout:
        return "Flight search timed out. The API took too long to respond."

    except requests.exceptions.ConnectionError:
        return "Flight search failed: No internet connection or API unreachable."

    except Exception as e:
        return f"Flight search encountered an unexpected error: {str(e)}"