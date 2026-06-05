import os
import json
import uuid
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from main import app, db_manager, extract_budget, TravelState

# Initialize FastAPI
api_app = FastAPI(title="AI Travel Planner API")

# Enable CORS for frontend
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    user_query: str
    thread_id: Optional[str] = None
    user_id: Optional[str] = None

@api_app.post("/api/plan")
async def generate_plan(request: PlanRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    user_query = request.user_query
    user_id = request.user_id
    budget = extract_budget(user_query)

    # Record user session mapping
    if user_id:
        db_manager.record_user_thread(user_id, thread_id)

    # SSE Event Generator
    def event_stream():
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        try:
            # Yield startup state
            yield f"event: start\ndata: {json.dumps({'thread_id': thread_id, 'budget': budget})}\n\n"
            
            # Track cumulative llm_calls across all nodes
            # (stream_mode="updates" sends per-node diffs, not full accumulated state)
            total_llm_calls = 0

            # Run LangGraph streaming
            for chunk in app.stream(
                {
                    "messages": [HumanMessage(content=user_query)],
                    "user_query": user_query,
                    "flight_results": "",
                    "hotel_results": "",
                    "itinerary": "",
                    "budget_analysis": "",
                    "budget": budget,
                    "llm_calls": 0
                },
                config=config,
                stream_mode="updates"
            ):
                # Each chunk yields a dict mapping node names to output
                for node_name, node_output in chunk.items():
                    # Accumulate llm_calls from each node's partial output
                    node_calls = node_output.get("llm_calls")
                    if node_calls is not None:
                        total_llm_calls += 1  # each node contributes 1 call

                    payload = {
                        "agent": node_name,
                        "output": {
                            "flight_results": node_output.get("flight_results"),
                            "hotel_results": node_output.get("hotel_results"),
                            "itinerary": node_output.get("itinerary"),
                            "budget_analysis": node_output.get("budget_analysis"),
                            # Send the running cumulative total so the frontend always has the correct count
                            "llm_calls": total_llm_calls
                        }
                    }
                    yield f"event: update\ndata: {json.dumps(payload)}\n\n"

            # Yield final completion with definitive total
            yield f"event: complete\ndata: {json.dumps({'thread_id': thread_id, 'llm_calls': total_llm_calls})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@api_app.get("/api/history")
def get_history(user_id: Optional[str] = None):
    try:
        thread_ids = db_manager.get_user_threads(user_id)
        
        history = []
        for tid in thread_ids:
            try:
                state = app.get_state({"configurable": {"thread_id": tid}})
                if state and state.values:
                    history.append({
                        "thread_id": tid,
                        "user_query": state.values.get("user_query", "Unknown Trip"),
                        "llm_calls": state.values.get("llm_calls", 0),
                        "has_itinerary": bool(state.values.get("itinerary")),
                        "budget": state.values.get("budget", 0.0)
                    })
            except Exception as inner_e:
                # Skip any thread state that fails to fetch or parse
                continue
                
        # Sort history to show most recent or alphabetically
        return {"history": history}
    except Exception as e:
        return {"error": str(e), "history": []}

@api_app.get("/api/plan/{thread_id}")
def get_plan(thread_id: str):
    try:
        state = app.get_state({"configurable": {"thread_id": thread_id}})
        if not state or not state.values:
            return {"error": "Trip plan not found"}
        
        # Format response data
        values = state.values
        return {
            "thread_id": thread_id,
            "user_query": values.get("user_query"),
            "flight_results": values.get("flight_results"),
            "hotel_results": values.get("hotel_results"),
            "itinerary": values.get("itinerary"),
            "budget_analysis": values.get("budget_analysis"),
            "budget": values.get("budget"),
            "llm_calls": values.get("llm_calls")
        }
    except Exception as e:
        return {"error": str(e)}

@api_app.delete("/api/plan/{thread_id}")
def delete_plan(thread_id: str):
    try:
        db_manager.delete_thread(thread_id)
        return {"success": True, "message": f"Trip plan {thread_id} deleted successfully."}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:api_app", host="127.0.0.1", port=8000, reload=True)
