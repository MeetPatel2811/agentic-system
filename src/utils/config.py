"""
Configuration Module with Pydantic Validation
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

class OpenAIConfig(BaseModel):
    api_key: str = Field(..., min_length=20)
    model_name: str = Field("gpt-4")
    temperature: float = Field(0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(2000, ge=100, le=4000)
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v.startswith('sk-'):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v
    
    class Config:
        frozen = True

class APIConfig(BaseModel):
    host: str = Field("localhost")
    port: int = Field(8000, ge=1024, le=65535)
    reload: bool = Field(True)
    workers: int = Field(1, ge=1, le=8)
    
    class Config:
        frozen = True

class MemoryConfig(BaseModel):
    short_term_max: int = Field(20, ge=5, le=100)
    sqlite_path: Path
    chroma_path: Path
    
    class Config:
        frozen = True

class CrewConfig(BaseModel):
    verbose: bool = Field(True)
    max_rpm: int = Field(10, ge=1, le=100)
    max_iter: int = Field(15, ge=5, le=50)
    timeout: int = Field(120, ge=30, le=300)
    
    class Config:
        frozen = True

class ToolConfig(BaseModel):
    max_search_results: int = Field(5, ge=1, le=10)
    summary_max_length: int = Field(500, ge=100, le=2000)
    claim_confidence_threshold: float = Field(0.5, ge=0.0, le=1.0)
    
    class Config:
        frozen = True

class LoggingConfig(BaseModel):
    level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    file_path: Path
    
    class Config:
        frozen = True

class Settings(BaseModel):
    openai: OpenAIConfig
    api: APIConfig
    memory: MemoryConfig
    crew: CrewConfig
    tools: ToolConfig
    logging: LoggingConfig
    
    class Config:
        frozen = True
        
    def validate_all(self) -> None:
        if not self.openai.api_key:
            raise ValueError("OPENAI_API_KEY not found")

def load_settings() -> Settings:
    try:
        settings = Settings(
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model_name=os.getenv("MODEL_NAME", "gpt-4"),
                temperature=float(os.getenv("TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("MAX_TOKENS", "2000"))
            ),
            api=APIConfig(
                host=os.getenv("API_HOST", "localhost"),
                port=int(os.getenv("API_PORT", "8000")),
                reload=os.getenv("API_RELOAD", "true").lower() == "true",
                workers=int(os.getenv("API_WORKERS", "1"))
            ),
            memory=MemoryConfig(
                short_term_max=int(os.getenv("SHORT_TERM_MAX", "20")),
                sqlite_path=Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "memory.db"))),
                chroma_path=Path(os.getenv("CHROMA_PATH", str(DATA_DIR / "chroma")))
            ),
            crew=CrewConfig(
                verbose=os.getenv("CREW_VERBOSE", "true").lower() == "true",
                max_rpm=int(os.getenv("CREW_MAX_RPM", "10")),
                max_iter=int(os.getenv("CREW_MAX_ITER", "15")),
                timeout=int(os.getenv("CREW_TIMEOUT", "120"))
            ),
            tools=ToolConfig(
                max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", "5")),
                summary_max_length=int(os.getenv("SUMMARY_MAX_LENGTH", "500")),
                claim_confidence_threshold=float(os.getenv("CLAIM_THRESHOLD", "0.5"))
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                file_path=LOG_DIR / "app.log"
            )
        )
        settings.validate_all()
        return settings
    except Exception as e:
        raise ValueError(f"Configuration error: {e}")

settings = load_settings()

# Export for backward compatibility
OPENAI_API_KEY = settings.openai.api_key
MODEL_NAME = settings.openai.model_name
TEMPERATURE = settings.openai.temperature
MAX_TOKENS = settings.openai.max_tokens
API_HOST = settings.api.host
API_PORT = settings.api.port
DATABASE_PATH = str(settings.memory.sqlite_path)
CHROMA_PATH = str(settings.memory.chroma_path)
LOG_LEVEL = settings.logging.level
LOG_FILE = settings.logging.file_path

MEMORY_CONFIG = {
    "short_term_max": settings.memory.short_term_max,
    "sqlite_path": DATABASE_PATH,
    "chroma_path": CHROMA_PATH
}

CREW_CONFIG = {
    "verbose": settings.crew.verbose,
    "max_rpm": settings.crew.max_rpm,
    "max_iter": settings.crew.max_iter
}

TOOL_CONFIG = {
    "max_search_results": settings.tools.max_search_results,
    "summary_max_length": settings.tools.summary_max_length,
    "claim_confidence_threshold": settings.tools.claim_confidence_threshold
}

def validate_config() -> bool:
    settings.validate_all()
    return True

def get_settings() -> Settings:
    return settings