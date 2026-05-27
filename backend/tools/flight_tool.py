import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def search_flights(query: str) -> str:
    """
    Searches for flights based on the user query.
    Uses Tavily Search to find the best flight options, routes, and airlines.
    """
    if not TAVILY_API_KEY:
        return "Flight search is unavailable (TAVILY_API_KEY is not set)."
    
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        search_query = f"flights airlines routes tickets and pricing for {query}"
        response = tavily_client.search(query=search_query, max_results=3)
        
        results = []
        for i, r in enumerate(response.get("results", []), 1):
            title = r.get("title", "Flight Info")
            url = r.get("url", "")
            content = r.get("content", "").strip()
            if len(content) > 250:
                content = content[:250] + "..."
            results.append(f"{i}. **{title}**\n   URL: {url}\n   {content}")
            
        if not results:
            return "No flight routes found. Try searching for major nearby airports."
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error searching flights: {str(e)}"
