import re
import math

def parse_travelers_from_query(query: str) -> int:
    """
    Extracts the number of travelers from user query.
    e.g. '3 people', '2 adults', 'couple' (2), 'family of 4'
    Defaults to 1 traveler.
    """
    if not query:
        return 1

    query_lower = query.lower()

    # Match "3 people", "4 adults", "2 travelers", "5 guests", "6 persons", "2 pax", "family of 4"
    people_match = re.search(
        r'(\d+)\s*(?:people|adults|travelers|guests|persons|pax|members|friends)', 
        query_lower
    )
    if people_match:
        return int(people_match.group(1))

    # Match "family of 4", "group of 5"
    group_match = re.search(
        r'(?:family|group)\s*of\s*(\d+)', 
        query_lower
    )
    if group_match:
        return int(group_match.group(1))

    # Match keyword cues
    if "couple" in query_lower or "partner" in query_lower or "husband" in query_lower or "wife" in query_lower:
        return 2

    return 1

def parse_budget_from_query(query: str) -> float:
    """
    Parses budget from user query text.

    Supports:
    - 2 lakh
    - 1.5 lakhs
    - 2L
    - ₹50000
    - under 15,000 INR
    - 15k

    Returns 0.0 if no budget found.
    """

    if not query:
        return 0.0

    query_lower = query.lower().replace(',', '')

    # Match lakh/lakhs/L
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(lakh|lakhs|l)\b', query_lower)

    if lakh_match:
        amount = float(lakh_match.group(1))
        return amount * 100000

    # Match thousand/k
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', query_lower)

    if k_match:
        amount = float(k_match.group(1))
        return amount * 1000

    # Match normal number
    number_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d{3,})', query_lower)

    if number_match:
        return float(number_match.group(1))

    return 0.0

def extract_prices(text: str) -> list[float]:
    """
    Extracts numerical prices from a text block and normalizes them to INR (Rupees).
    Converts USD ($) to INR using an approximate exchange rate of 83.
    """
    if not text:
        return []

    prices = []

    # 1. Match currency patterns with prefix: ₹15,000, Rs. 5000, INR 12000, $200, USD 100
    currency_prefix_pattern = re.compile(
        r'(₹|rs\.?|inr|\$|usd)\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 
        re.IGNORECASE
    )
    for match in currency_prefix_pattern.finditer(text):
        symbol = match.group(1).lower()
        num_str = match.group(2).replace(',', '')
        try:
            val = float(num_str)
            if symbol in ('$', 'usd'):
                val *= 83.0  # Convert USD to INR
            prices.append(val)
        except ValueError:
            pass

    # 2. Match currency patterns with suffix: 200 USD, 5000 INR, 15000 Rs
    currency_suffix_pattern = re.compile(
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(usd|inr|rs\.?|₹)', 
        re.IGNORECASE
    )
    for match in currency_suffix_pattern.finditer(text):
        num_str = match.group(1).replace(',', '')
        symbol = match.group(2).lower()
        try:
            val = float(num_str)
            if symbol == 'usd':
                val *= 83.0  # Convert USD to INR
            prices.append(val)
        except ValueError:
            pass

    # 3. If no prices found with explicit currency, look for numbers near price-related words
    if not prices:
        price_words_pattern = re.compile(
            r'(?:price|pricing|cost|fare|rate|ticket|starts? at|starts? from|around|approx\.?|estimate|budget)\s*(?:is|of|for|to)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
            re.IGNORECASE
        )
        for match in price_words_pattern.finditer(text):
            num_str = match.group(1).replace(',', '')
            try:
                val = float(num_str)
                # If the number is small (under 1000) and no currency is specified,
                # it's likely a USD amount (e.g. "price starts at 150").
                # If it's extremely small (under 10), it might be a non-price number, so ignore it.
                if 10.0 < val < 1000.0:
                    val *= 83.0  # Convert to INR assuming it's USD
                elif val <= 10.0:
                    continue  # Ignore small numbers like 1, 2, 3
                prices.append(val)
            except ValueError:
                pass

    return prices

def calculate_budget(flight_results: str, hotel_results: str, query: str) -> dict:
    """
    Calculates estimated trip cost based on flight and hotel search results
    and compares it to the user's budget extracted from the query.
    Takes into account the number of travelers to scale flight tickets and hotel rooms.
    """
    user_budget = parse_budget_from_query(query)
    num_travelers = parse_travelers_from_query(query)

    flight_prices = extract_prices(flight_results)
    hotel_prices = extract_prices(hotel_results)

    # Heuristic for flights: Multiply ticket price by number of people
    flight_per_person = min(flight_prices) if flight_prices else 0.0
    flight_cost = flight_per_person * num_travelers

    # Heuristic for hotels: Multiply by rooms needed (assume 1 room per 2 people)
    rooms_needed = math.ceil(num_travelers / 2.0)
    if hotel_prices:
        min_hotel = min(hotel_prices)
        # If it looks like a per-night rate (less than 20,000), assume 3 nights
        if min_hotel < 20000:
            hotel_cost = min_hotel * 3 * rooms_needed
        else:
            hotel_cost = min_hotel * rooms_needed
    else:
        hotel_cost = 0.0

    estimated_total = flight_cost + hotel_cost

    if user_budget <= 0 or estimated_total <= 0:
        status = "unknown"
    elif estimated_total > user_budget:
        status = "over"
    elif estimated_total == user_budget:
        status = "fits"
    else:
        status = "under"

    return {
        "user_budget": user_budget,
        "estimated_total": estimated_total if estimated_total > 0 else None,
        "status": status,
        "num_travelers": num_travelers,
        "rooms_needed": rooms_needed
    }