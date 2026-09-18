import sqlite3
import json

DB_PATH = "data/audit.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS screening_log (
                audit_id TEXT PRIMARY KEY,
                timestamp TEXT,
                query_name TEXT,
                query_country TEXT,
                risk_level TEXT,
                top_match_entity_id TEXT,
                top_match_combined_score REAL,
                full_result_json TEXT,
                processing_time_ms REAL
            )
        """)

def log_screening(result):
    top_match_id = result.matches[0].entity_id if result.matches else None
    top_score = result.matches[0].combined_score if result.matches else 0.0
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO screening_log 
            (audit_id, timestamp, query_name, query_country, risk_level, 
             top_match_entity_id, top_match_combined_score, full_result_json, processing_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.audit_id, result.screened_at.isoformat(), result.query_name,
            result.query_country, result.risk_level, top_match_id, top_score,
            result.model_dump_json(), result.processing_time_ms
        ))