import os
from dotenv import load_dotenv
from tavily import TavilyClient, TavilyError

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Validate API key at startup - fail early with clear message
if not TAVILY_API_KEY:
    raise EnvironmentError(
        "TAVILY_API_KEY is missing. "
        "Add it to your .env file. Get one at https://tavily.com"
    )

client = TavilyClient(api_key=TAVILY_API_KEY)


def tavily_search(query: str) -> str:
    """
    Search the web using Tavily API.
    Used by Hotel Agent to find hotel and accommodation options.
    Returns formatted results or a fallback message.
    """
    try:
        response = client.search(
            query=query,
            max_results=5
        )

        results_data = response.get("results", [])

        # No results found
        if not results_data:
            return (
                f"No results found for: '{query}'. "
                f"Try searching on Booking.com, MakeMyTrip, or Airbnb directly."
            )

        results = []
        for i, r in enumerate(results_data, 1):
            title   = r.get("title", "Unknown")
            url     = r.get("url", "")
            snippet = r.get("content", "").strip()

            # Keep first 300 chars to avoid wall of text
            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

            results.append(
                f"{i}. {title}\n"
                f"   Link: {url}\n"
                f"   {snippet}"
            )

        header = f"Search results for: '{query}'\n" + "-" * 40 + "\n"
        return header + "\n\n".join(results)

    except TavilyError as e:
        return (
            f"Hotel search failed: Tavily API error — {str(e)}. "
            f"Please check your API key or try again later."
        )

    except Exception as e:
        return (
            f"Hotel search encountered an unexpected error: {str(e)}"
        )
    results = []

    for i, r in enumerate(response["results"], 1):
        title   = r.get("title", "Unknown")
        url     = r.get("url", "")
        snippet = r.get("content", "").strip()
        # Keep only the first 300 characters to avoid wall-of-text
        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        results.append(f"{i}. **{title}**\n   {url}\n   {snippet}")

    return "\n\n".join(results)
    
    
    