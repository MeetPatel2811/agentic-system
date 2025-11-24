"""
Database Initialization Script
"""
import os
import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import DATA_DIR, LOG_DIR, DATABASE_PATH, CHROMA_PATH

def create_directories():
    print("Creating directories...")
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created\n")

def initialize_database():
    print("Initializing database...")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            response TEXT,
            quality_score REAL,
            claims_count INTEGER,
            evidence_count INTEGER,
            sources_count INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            claim_text TEXT NOT NULL,
            confidence REAL,
            evidence_text TEXT,
            FOREIGN KEY (query_id) REFERENCES queries (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            title TEXT,
            url TEXT,
            snippet TEXT,
            FOREIGN KEY (query_id) REFERENCES queries (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized\n")

def main():
    print("=" * 60)
    print("Research Assistant - Initialization")
    print("=" * 60)
    print()
    
    create_directories()
    initialize_database()
    
    print("=" * 60)
    print("✅ Setup Complete!")
    print()
    print("Next steps:")
    print("1. Add OPENAI_API_KEY to .env file")
    print("2. Run: python -m spacy download en_core_web_sm")
    print("3. Terminal 1: python api/main.py")
    print("4. Terminal 2: cd frontend && npm run dev")
    print("=" * 60)

if __name__ == "__main__":
    main()