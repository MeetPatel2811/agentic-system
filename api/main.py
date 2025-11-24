"""
FastAPI Backend - Compatible with existing Streamlit frontend
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
import sys
from pathlib import Path
import sqlite3

sys.path.append(str(Path(__file__).parent.parent))

from src.orchestration.crew_manager import ResearchAssistantCrew
from src.memory.memory_system import MemorySystem
from src.utils.config import validate_config, API_HOST, API_PORT, DATABASE_PATH
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Research Assistant API",
    description="Agentic AI Research Assistant powered by CrewAI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

crew_system: Optional[ResearchAssistantCrew] = None
memory_system = MemorySystem()
app_start_time = datetime.now()

# Database path for frontend compatibility
FRONTEND_DB_PATH = Path(__file__).parent.parent / "db" / "history.db"

class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    include_history: bool = Field(False)
    max_sources: int = Field(5, ge=1, le=10)
    
    @validator('query')
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty')
        return v

class QueryRequest(BaseModel):
    """Request model for /query endpoint (frontend compatibility)"""
    query: str

class ResearchResponse(BaseModel):
    success: bool
    query: str
    report: str
    metadata: Dict
    timestamp: str
    query_id: Optional[int] = None

def init_frontend_db():
    """Initialize the SQLite database for frontend history"""
    FRONTEND_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FRONTEND_DB_PATH))
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    global crew_system
    try:
        validate_config()
        crew_system = ResearchAssistantCrew()
        init_frontend_db()  # Initialize frontend database
        logger.info(" Research Assistant API started")
    except Exception as e:
        logger.critical(f" Failed to start: {e}")
        raise

@app.get("/")
async def root():
    return {
        "service": "Research Assistant API",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if crew_system else "degraded",
        "crew_initialized": crew_system is not None,
        "uptime_seconds": (datetime.now() - app_start_time).total_seconds(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """
    FRONTEND COMPATIBILITY ENDPOINT
    This endpoint matches what your existing Streamlit frontend expects
    """
    if not crew_system:
        raise HTTPException(status_code=503, detail="Crew not initialized")
    
    try:
        logger.info(f"Processing query from frontend: {request.query}")
        
        # Execute research using our CrewAI system
        result = crew_system.run(query=request.query, include_history=False)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        # Extract the report
        report = result['report']
        metadata = result['metadata']
        
        # Store in frontend database for history
        try:
            conn = sqlite3.connect(str(FRONTEND_DB_PATH))
            c = conn.cursor()
            c.execute(
                "INSERT INTO history (query, response, timestamp) VALUES (?, ?, ?)",
                (request.query, report, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not save to frontend DB: {e}")
        
        # Return in the format your frontend expects
        return {
            "response": report,  # Frontend expects "response" key
            "metadata": metadata,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            "response": f"Error: {str(e)}",
            "success": False
        }

@app.post("/research", response_model=ResearchResponse)
async def conduct_research(request: ResearchRequest):
    """
    Standard research endpoint (for other clients)
    """
    if not crew_system:
        raise HTTPException(status_code=503, detail="Crew not initialized")
    
    try:
        logger.info(f"Processing: {request.query}")
        result = crew_system.run(query=request.query, include_history=request.include_history)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        return ResearchResponse(
            success=True,
            query=request.query,
            report=result['report'],
            metadata=result['metadata'],
            timestamp=datetime.now().isoformat(),
            query_id=result['metadata'].get('query_id')
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history(limit: int = 10):
    """Get query history from backend database"""
    try:
        history = memory_system.get_query_history(limit=limit)
        return {"success": True, "history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory statistics"""
    try:
        return memory_system.get_memory_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)