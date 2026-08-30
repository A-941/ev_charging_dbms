"""
Database connection and helper layer for the EV Charging Station DBMS.
Provides unified query execution, transaction management, and connection pooling.
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "ev_charging.db"

def get_connection():
    """Returns an active SQLite connection with Foreign Keys enabled."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def execute_query(query: str, params=()) -> pd.DataFrame:
    """Executes a SQL query and returns results as a pandas DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()

def execute_non_query(query: str, params=()) -> int:
    """Executes an INSERT, UPDATE, or DELETE command and commits changes."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

def get_db_stats():
    """Returns total record counts across all 11 tables."""
    tables = [
        "OPERATORS", "STATIONS", "PORTS", "PRICES", "USERS",
        "VEHICLES", "BOOKINGS", "CHARGING_SESSIONS", "PAYMENTS",
        "REVIEWS", "COMPLAINTS"
    ]
    conn = get_connection()
    stats = {}
    try:
        for t in tables:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            stats[t] = cnt
    finally:
        conn.close()
    return stats
