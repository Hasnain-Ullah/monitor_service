# app/database.py

import sqlite3
from datetime import datetime

DB_NAME = "monitoring.db"


def get_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create all required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for individual checks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status_code INTEGER,
            response_time REAL,
            success INTEGER NOT NULL,
            state TEXT NOT NULL,
            error_message TEXT
        )
    ''')
    
    # Table for incidents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            incident_type TEXT NOT NULL,
            started_at TEXT NOT NULL,
            recovered_at TEXT,
            duration_seconds REAL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'active'
        )
    ''')
    
    conn.commit()
    conn.close()


def save_check(endpoint, timestamp, status_code, response_time, success, state, error_message=None):
    """Save a single check result."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO checks (endpoint, timestamp, status_code, response_time, success, state, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        endpoint,
        timestamp,
        status_code,
        response_time,
        1 if success else 0,
        state,
        error_message
    ))
    
    conn.commit()
    conn.close()


def create_incident(endpoint, incident_type, reason):
    """Create a new incident."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO incidents (endpoint, incident_type, started_at, reason, status)
        VALUES (?, ?, ?, ?, 'active')
    ''', (
        endpoint,
        incident_type,
        datetime.now().isoformat(),
        reason
    ))
    
    incident_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return incident_id


def resolve_incident(endpoint, incident_type):
    """Resolve an active incident."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Find the active incident
    cursor.execute('''
        SELECT id, started_at FROM incidents 
        WHERE endpoint = ? AND incident_type = ? AND status = 'active'
        ORDER BY id DESC LIMIT 1
    ''', (endpoint, incident_type))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    incident_id = row['id']
    started_at = datetime.fromisoformat(row['started_at'])
    recovered_at = datetime.now()
    duration = (recovered_at - started_at).total_seconds()
    
    cursor.execute('''
        UPDATE incidents 
        SET recovered_at = ?, duration_seconds = ?, status = 'resolved'
        WHERE id = ?
    ''', (
        recovered_at.isoformat(),
        duration,
        incident_id
    ))
    
    conn.commit()
    conn.close()
    
    return {
        'id': incident_id,
        'started_at': row['started_at'],
        'recovered_at': recovered_at.isoformat(),
        'duration': duration,
    }


def get_active_incidents():
    """Get all active incidents."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM incidents WHERE status = 'active' ORDER BY started_at DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_recent_checks(endpoint, limit=20):
    """Get recent checks for an endpoint."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM checks WHERE endpoint = ? ORDER BY id DESC LIMIT ?
    ''', (endpoint, limit))
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]