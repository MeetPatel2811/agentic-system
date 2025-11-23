# ---------------------------------------------------------
# This file defines the FastAPI application.
# - Exposes POST /query endpoint for the frontend.
# - For each query, builds a CrewAI crew and runs it.
# - Saves the (query, response) into SQLite history memory.
# ---------------------------------------------------------
import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel

# --- This block ensures the backend root is on sys.path so imports work ---
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from crew.crew_runner import build_crew  # noqa: E402
from memory.sqlite_history import save_history  # noqa: E402

app = FastAPI(title="Agentic Research Assistant (CrewAI + Vector Memory)")


# --- This block defines the request body schema for /query ---
class QueryInput(BaseModel):
    query: str


# --- This block defines the main endpoint used by Streamlit frontend ---
@app.post("/query")
async def run_query(payload: QueryInput):
    """
    This endpoint receives a research query from the frontend,
    runs the CrewAI pipeline, saves the result to SQLite,
    and returns the final Markdown response.
    """
    crew = build_crew()
    # Kick off the crew with the query as input for the tasks.
    result = crew.kickoff(inputs={"query": payload.query})
    response_text = str(result)

    # Save to long-term SQLite history.
    save_history(payload.query, response_text)

    return {"response": response_text}
