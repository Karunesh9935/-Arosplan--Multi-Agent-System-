import re

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
    Extracts numerical prices from a text block.
    Looks for currency signs first, then numbers near price words.
    """
    if not text:
        return []

    # Match currency patterns: ₹15,000, Rs. 5000, INR 12000, $200
    currency_pattern = re.compile(
        r'(?:₹|rs\.?|inr|usd|\$)\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 
        re.IGNORECASE
    )
    prices = []
    for match in currency_pattern.finditer(text):
        num_str = match.group(1).replace(',', '')
        try:
            prices.append(float(num_str))
        except ValueError:
            pass

    # If no prices found with currency, look for numbers near price-related words
    if not prices:
        price_words_pattern = re.compile(
            r'(?:price|pricing|cost|fare|rate|ticket|starts? at|starts? from|around|approx\.?|estimate|budget)\s*(?:is|of|for|to)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
            re.IGNORECASE
        )
        for match in price_words_pattern.finditer(text):
            num_str = match.group(1).replace(',', '')
            try:
                prices.append(float(num_str))
            except ValueError:
                pass

    return prices

def calculate_budget(flight_results: str, hotel_results: str, query: str) -> dict:
    """
    Calculates estimated trip cost based on flight and hotel search results
    and compares it to the user's budget extracted from the query.
    """
    user_budget = parse_budget_from_query(query)

    flight_prices = extract_prices(flight_results)
    hotel_prices = extract_prices(hotel_results)

    # Heuristic for flight cost (use minimum of found prices, or 0.0)
    flight_cost = min(flight_prices) if flight_prices else 0.0

    # Heuristic for hotel cost (assume a 3-night stay if it looks like a per-night rate)
    if hotel_prices:
        min_hotel = min(hotel_prices)
        if min_hotel < 20000:
            hotel_cost = min_hotel * 3
        else:
            hotel_cost = min_hotel
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
        "status": status
    }