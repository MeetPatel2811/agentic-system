"""
Multi-Level Memory System
"""
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
import hashlib
from pathlib import Path
from ..utils.config import MEMORY_CONFIG
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class MemorySystem:
    def __init__(self, db_path: Optional[str] = None, chroma_path: Optional[str] = None):
        self.db_path = db_path or MEMORY_CONFIG['sqlite_path']
        self.chroma_path = chroma_path or MEMORY_CONFIG['chroma_path']
        
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        
        self.short_term_memory = {
            'current_session': [],
            'agent_notes': {},
            'max_entries': MEMORY_CONFIG['short_term_max']
        }
        
        self.init_longterm_db()
        self.init_vector_store()
        logger.info("Memory system initialized")
    
    def init_longterm_db(self):
        conn = sqlite3.connect(self.db_path)
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
    
    def init_vector_store(self):
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        self.docs_collection = self.chroma_client.get_or_create_collection(
            name="research_documents",
            embedding_function=self.embedding_fn
        )
    
    def add_to_session(self, entry: Dict):
        self.short_term_memory['current_session'].append({
            'timestamp': datetime.now().isoformat(),
            'entry': entry
        })
        if len(self.short_term_memory['current_session']) > self.short_term_memory['max_entries']:
            self.short_term_memory['current_session'].pop(0)
    
    def clear_session(self):
        self.short_term_memory['current_session'] = []
        self.short_term_memory['agent_notes'] = {}
    
    def store_query_result(self, query: str, response: str, metadata: Dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO queries 
            (query_text, response, quality_score, claims_count, evidence_count, sources_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            query, response,
            metadata.get('quality_score', 0.0),
            metadata.get('claims_count', 0),
            metadata.get('evidence_count', 0),
            metadata.get('sources_count', 0)
        ))
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return query_id
    
    def get_query_history(self, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, query_text, timestamp, quality_score
            FROM queries ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'query': r[1], 'timestamp': r[2], 'quality_score': r[3]} for r in results]
    
    def search_past_queries(self, search_term: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, query_text, timestamp, response
            FROM queries WHERE query_text LIKE ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (f'%{search_term}%', limit))
        results = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'query': r[1], 'timestamp': r[2], 'response': r[3]} for r in results]
    
    def add_document_embedding(self, doc_text: str, metadata: Dict):
        doc_id = hashlib.md5(doc_text.encode()).hexdigest()
        try:
            self.docs_collection.add(documents=[doc_text], metadatas=[metadata], ids=[doc_id])
        except Exception as e:
            logger.error(f"Error adding document: {e}")
    
    def semantic_search_documents(self, query: str, n_results: int = 5) -> List[Dict]:
        try:
            results = self.docs_collection.query(query_texts=[query], n_results=n_results)
            return [
                {'text': doc, 'metadata': meta, 'distance': dist}
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )
            ]
        except:
            return []
    
    def get_memory_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM queries')
        total_queries = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM claims')
        total_claims = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM sources')
        total_sources = cursor.fetchone()[0]
        conn.close()
        
        return {
            'long_term': {
                'total_queries': total_queries,
                'total_claims': total_claims,
                'total_sources': total_sources
            },
            'vector_store': {
                'documents': self.docs_collection.count(),
                'claims': 0
            },
            'short_term': {
                'session_entries': len(self.short_term_memory['current_session']),
                'agent_notes': len(self.short_term_memory['agent_notes'])
            }
        }