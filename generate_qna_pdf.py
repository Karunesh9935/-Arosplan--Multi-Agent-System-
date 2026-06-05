import os
import sys
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Ensure output stream uses UTF-8 to avoid encoding errors with emojis or symbols
if sys.stdout and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class QnAPDF(FPDF):
    def header(self):
        # Header banner
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(100, 116, 139)  # Slate-500
        self.cell(0, 8, 'AEROSPLAN - AI Multi-Agent Travel Planner Handout', new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
        self.cell(0, 8, 'Technical Interview & Presentation Prep', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        self.set_draw_color(226, 232, 240)  # Border gray
        self.line(15, 18, 195, 18)
        self.ln(6)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)  # Slate-400
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')

    def add_section_header(self, title):
        self.ln(4)
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(15, 23, 42)  # Slate-900
        
        # Add light background band
        self.set_fill_color(241, 245, 249)  # Slate-100
        self.cell(0, 10, f"  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L', fill=True)
        self.ln(4)

    def add_qa(self, number, question, answer):
        # Question paragraph
        self.set_font('helvetica', 'B', 11)
        self.set_text_color(79, 70, 229)  # Brand Indigo-600
        
        # Bullet indicator + Question text
        q_text = f"Q{number}: {question}"
        # Multi_cell handles text wrapping automatically
        self.multi_cell(0, 6, q_text)
        self.ln(1.5)
        
        # Answer paragraph
        self.set_font('helvetica', '', 10)
        self.set_text_color(51, 65, 85)  # Slate-700
        self.multi_cell(0, 5.5, answer)
        self.ln(4.5)

def main():
    pdf = QnAPDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.set_margins(15, 20, 15)
    pdf.add_page()
    
    # --- Title Page Cover Header ---
    pdf.set_fill_color(79, 70, 229)  # Brand Indigo-600
    pdf.rect(0, 0, 210, 12, 'F')
    
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 24)
    pdf.set_text_color(15, 23, 42)  # Slate-900
    pdf.cell(0, 12, "AEROSPLAN Handbook", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(100, 116, 139)  # Slate-500
    pdf.cell(0, 6, "AI Multi-Agent Travel Planning System Architecture & Implementation Q&A", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(8)
    
    # Section 1: Core Concept & Multi-Agent Value Proposition
    pdf.add_section_header("1. Core Concept & Multi-Agent Philosophy")
    
    pdf.add_qa(
        1, 
        "What is the core problem this project solves and what is the target audience?",
        "Planning a vacation requires travelers to manually check multiple portals for flights, hotels, daily activities, and budget constraints, then copy everything into a document. Aerosplan consolidates this experience into a unified dashboard. By typing a simple natural language prompt (e.g., 'A 4-day trip to Goa next week under 50k'), the system orchestrates multiple specialized AI agents to search the web, calculate costs, draft a personalized day-by-day itinerary, check budget constraints, and display a fully comprehensive, interactive travel plan."
    )
    
    pdf.add_qa(
        2,
        "Why did you build this as a Multi-Agent system rather than using a single LLM prompt with system instructions?",
        "A single LLM prompt suffers from context pollution, high hallucination rates, and struggles when executing multiple tools sequentially. Splitting the process into a multi-agent system provides: \n"
        "1. Focus & Specialization: Each agent (Flight, Hotel, Itinerary, Budget) has a dedicated system instruction and limited tool scope.\n"
        "2. Deterministic Routing: If Flights or Hotels fail to yield API results, conditional routing redirects to specific fallback nodes instead of failing the entire session.\n"
        "3. Controlled State Sharing: Agents pass structured updates through a shared State schema, ensuring clear data boundaries and reducing prompt length.\n"
        "4. Cost & Performance Optimization: Heavy math is offloaded to a standard Python calculator (Budget Tool) instead of forcing the LLM to do arithmetic, which it frequently fails at."
    )
    
    # Section 2: LangGraph & Orchestration
    pdf.add_section_header("2. LangGraph Graph Architecture & Orchestration")
    
    pdf.add_qa(
        3,
        "Why did you choose LangGraph over other frameworks like CrewAI or AutoGen?",
        "LangGraph (by the LangChain team) was chosen because it focuses on graph-based state machines. While frameworks like CrewAI and AutoGen are highly autonomous (making them hard to predict and expensive due to infinite reasoning loops), LangGraph gives the developer fine-grained control. It allows us to explicitly define graph nodes (agents), edges (flow paths), and conditional routing functions. This ensures the workflow is predictable, fast, and structured, while supporting cycles and database persistence."
    )
    
    pdf.add_qa(
        4,
        "Explain the graph structure of Aerosplan. What are the nodes and how is state managed?",
        "The graph is managed via a shared 'TravelState' defined using Python's TypedDict. The state persists fields like 'messages' (which uses a reducer operator.add to append chat history), 'user_query', 'flight_results', 'hotel_results', 'itinerary', 'budget_analysis', 'budget' limit, and 'llm_calls' count.\n\n"
        "The nodes of the graph are:\n"
        "- Flight Agent -> Queries the flights tool.\n"
        "- Hotel Agent -> Queries the Tavily Search API for accommodations.\n"
        "- Itinerary Agent -> Combines flights + hotels to construct the daily schedule.\n"
        "- Budget Agent -> Computes total cost and suggests saving/upgrade recommendations.\n"
        "- Final Response Agent -> Formats the complete package into clean Markdown layout.\n"
        "- Fallback Agents -> Run if flight or hotel search returns zero matches."
    )
    
    pdf.add_qa(
        5,
        "How does conditional routing and fallback handling work in your graph implementation?",
        "Conditional routing is implemented using 'graph.add_conditional_edges'. After the Flight Agent runs, a router function 'route_after_flights' checks the 'flight_results' field in the state. If it detects failure keywords (like 'unavailable' or 'no flights'), it returns the string 'no_flight_fallback'. The graph engine routes control to the 'no_flight_fallback' agent, which suggests backup transit (trains, buses, nearby airports) and then rejoins the main flow at the Hotel Agent. The same pattern is used for the Hotel Agent with a 'no_hotel_fallback' route."
    )

    pdf.add_page()  # Page break to keep it organized

    # Section 3: FastAPI Backend & Real-time Streaming
    pdf.add_section_header("3. Backend, SSE Streaming, and API Design")
    
    pdf.add_qa(
        6,
        "How is real-time progress update streaming implemented between the FastAPI server and React client?",
        "We use Server-Sent Events (SSE) via FastAPI's 'StreamingResponse' returning 'text/event-stream'. \n"
        "1. Backend: When a user hits '/api/plan', FastAPI triggers LangGraph using 'app.stream(..., stream_mode=\"updates\")'. This generator streams state changes node-by-node. As each agent completes, we yield a structured event containing the agent name and its specific output (e.g. 'event: update\\ndata: {...}\\n\\n').\n"
        "2. Frontend: The React client uses the Fetch API's 'ReadableStream' reader to listen to the HTTP stream. A buffer parses the stream line-by-line, extracting the event type (start, update, complete, error). React updates its state variables in real-time, allowing the UI to render active agent progress (e.g., highlighting which agent is running) and stream text step-by-step."
    )
    
    pdf.add_qa(
        7,
        "Why did you choose Server-Sent Events (SSE) over WebSockets or long polling?",
        "1. SSE vs. WebSockets: WebSockets are bidirectional and complex, requiring separate handshakes and connection management. Since our application only needs to stream data from the server to the client (one-way), SSE is lightweight, operates over standard HTTP, and automatically handles client disconnections/reconnections.\n"
        "2. SSE vs. Polling: Polling is highly inefficient because the client must constantly send requests to check if the plan is ready. SSE pushes data instantly, reducing network latency and database queries."
    )
    
    pdf.add_qa(
        8,
        "How did you optimize the streaming payload to prevent performance lag or browser memory issues?",
        "Instead of returning the entire LangGraph state structure (which contains nested message history, raw metadata, and large object trees), we map each node update to a clean, lightweight payload in 'api.py'. The payload only contains keys that the frontend needs (like 'flight_results', 'hotel_results', 'itinerary', or 'budget_analysis'). This reduces bandwidth by over 90% and prevents frontend parsing overhead."
    )

    # Section 4: Database & State Persistence
    pdf.add_section_header("4. Database & State Persistence (Memory)")
    
    pdf.add_qa(
        9,
        "How does the session memory work in Aerosplan? Where is it stored?",
        "Aerosplan uses LangGraph's checkpointer mechanism with a 'PostgresSaver'. This Saver is backed by a PostgreSQL database and a connection pool ('psycopg_pool.ConnectionPool'). By compiling the graph with a checkpointer, LangGraph automatically saves state variables at every graph node step using a unique 'thread_id'. This allows a user to refresh their browser, close the app, or fetch their history, and retrieve their exact plan history using their 'thread_id' from the database."
    )
    
    pdf.add_qa(
        10,
        "Explain your connection pooling strategy and why it is critical here.",
        "We use 'psycopg_pool.ConnectionPool(DATABASE_URL)' to manage database connections. Instead of establishing a new TCP connection for every single query (which takes time and limits scale), the pool maintains active, recycled connections. If multiple users hit the API concurrently, the pool assigns connections instantly. This prevents database lockups, handles concurrent requests smoothly, and provides robust performance."
    )
    
    pdf.add_qa(
        11,
        "How does deleting a trip work on the database level?",
        "FastAPI exposes a DELETE endpoint: '/api/plan/{thread_id}'. To cleanly remove a plan, the API connects to PostgreSQL and runs three SQL deletes on the LangGraph system tables using the 'thread_id':\n"
        "1. DELETE FROM checkpoints WHERE thread_id = %s;\n"
        "2. DELETE FROM checkpoint_blobs WHERE thread_id = %s;\n"
        "3. DELETE FROM checkpoint_writes WHERE thread_id = %s;\n"
        "This ensures there are no orphan data records in the database, preserving clean storage."
    )

    pdf.add_page()  # Page break

    # Section 5: LLMs & Custom Tool Logic
    pdf.add_section_header("5. LLM Integration & Custom Tools")
    
    pdf.add_qa(
        12,
        "Why did you use Groq (Llama 3.3 70B) as your LLM instead of GPT-4 or Claude?",
        "1. Extreme Speed: Groq runs open-source models using custom LPU (Language Processing Unit) hardware, delivering speeds of over 200 tokens/sec. This is crucial for multi-agent loops where several LLM steps run sequentially. Standard models would take 30-40 seconds, while Groq takes 10-15 seconds for the entire graph.\n"
        "2. Cost Efficiency: Utilizing Llama 3.3 70B through Groq is highly cost-effective compared to commercial closed-source APIs.\n"
        "3. Reasoning Power: Llama 3.3 70B features a 128k context window and is highly capable of parsing structured text, organizing itineraries, and analyzing budgets."
    )
    
    pdf.add_qa(
        13,
        "Explain how the budget calculation tool works. Why is it a hybrid of regex and LLM and how does it scale for multiple travelers?",
        "LLMs are notoriously poor at math. To solve this, we implemented a hybrid model:\n"
        "1. Regex & Scaling (Budget Tool): We extract the target budget from the user's query. Next, the tool parses the number of travelers from the query (e.g. '3 people' or 'couple' -> 2).\n"
        "   - Flight scaling: Takes the lowest flight price and multiplies it by the traveler count.\n"
        "   - Hotel scaling: Calculates rooms needed (1 room per 2 guests using math.ceil) and multiplies the per-room cost by the room count.\n"
        "   - The tool then adds the scaled flight and hotel costs together.\n"
        "2. LLM (Budget Agent): These exact numbers (e.g. estimated total: Rs. 33,000, limit: Rs. 50,000, status: under, travelers: 3, rooms: 2) are sent to the LLM. The LLM then writes the user-friendly description and recommends upgrades (if under budget) or cost-saving swaps (if over budget). This guarantees mathematical accuracy while maintaining natural language flexibility."
    )

    # Section 6: Frontend Design & UX
    pdf.add_section_header("6. Frontend Engineering & Design System")
    
    pdf.add_qa(
        14,
        "What is the design style and typography choices of the React application?",
        "The frontend uses a premium, responsive glassmorphic dashboard styled with Tailwind CSS.\n"
        "1. Typography: Google Fonts Outfit for headings (contemporary, bold structure) and Plus Jakarta Sans for body text (highly readable at smaller screen sizes).\n"
        "2. Styling: Uses a curated slate/indigo palette. Includes custom CSS helper classes for glassmorphic cards (e.g., 'glass-panel' and 'glass-card' using backdrop-filter: blur) and a subtle background radial gradient that moves fluidly on screen sizes.\n"
        "3. Real-time Indicators: Features a custom stepper indicator that lights up in real-time depending on which agent (Flight, Hotel, Itinerary, Budget) is executing."
    )
    
    pdf.add_qa(
        15,
        "How is the history sidebar integrated with the state?",
        "On page load, React fetches the trip history (thread IDs, queries, budgets, and completed statuses) and renders them in a collapsible sidebar using Lucide-react icons. Clicking any past trip queries the GET '/api/plan/{thread_id}' endpoint. The backend retrieves the compiled state values from database checkpointer tables, and React updates its local state to render the saved itinerary, budget analysis, and flight details instantly, without triggering new agent executions or LLM costs."
    )

    # Section 7: Session Management & DB Portability
    pdf.add_section_header("7. Session Management & Database Portability")

    pdf.add_qa(
        16,
        "How does Aerosplan handle user sessions and keep history segmented per user without standard email/password authentication?",
        "For lightweight portability and convenience in self-hosted and presentation environments, Aerosplan implements a client-persisted UUID mapping pattern:\n"
        "1. Frontend UUID Generation: On initial page load, the React client checks localStorage for 'aerosplan_user_id'. If not present, it generates a unique random alphanumeric identifier and saves it.\n"
        "2. Session Thread Mapping: Every trip planning request (/api/plan) sends this user_id alongside the search query. The backend records the mapping in a 'user_trips' junction table.\n"
        "3. Filtered History Retrieves: When loading the history sidebar, the client calls GET /api/history?user_id=usr_... . The backend filters the database checkpoints to return only the thread_id records that belong to that specific user_id."
    )

    pdf.add_qa(
        17,
        "How does the backend prevent connection crashes if a developer running Aerosplan does not have a PostgreSQL database server set up?",
        "We implemented an automatic database connection fallback mechanism in main.py:\n"
        "1. Connection Test: Upon backend initialization, the system tries to establish a brief test connection to the PostgreSQL URL (configured in .env) with a short 2-second timeout.\n"
        "2. SQLite Fallback: If the connection fails (e.g., PostgreSQL server is offline or not installed), the system gracefully catches the error and instantiates a local, persistent SQLite database (aerosplan_memory.db) using LangGraph's native SqliteSaver checkpointer.\n"
        "3. Unified Interface: We encapsulate these database differences within a custom DatabaseManager class, exposing uniform methods like get_user_threads(), record_user_thread(), and delete_thread(). This allows the API code to run without modification regardless of the database technology, preventing startup crashes and 'fetch errors'."
    )

    # --- Save PDF ---
    output_filename = "Aerosplan_Interview_QnA.pdf"
    pdf.output(output_filename)
    print(f"Successfully generated PDF: {output_filename}")

if __name__ == "__main__":
    main()
