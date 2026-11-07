import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def hash_password(password: str) -> str:
    """Standard SHA256 hashing for password authentication"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Complaints Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            reporter_type TEXT DEFAULT 'Citizen',
            reporter_name TEXT,
            reporter_contact TEXT,
            image_filename TEXT NOT NULL,
            image_path TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            location_address TEXT,
            landmark TEXT,
            description TEXT,
            categories TEXT, -- JSON Array of categories
            primary_category TEXT,
            severity TEXT DEFAULT 'Medium', -- Low, Medium, High, Critical
            risk_assessment TEXT,
            confidence_score REAL DEFAULT 0.85,
            recommended_action TEXT,
            environmental_impact TEXT,
            status TEXT DEFAULT 'New', 
            -- Statuses: New, Assigned, Acknowledged, Inspection Pending, Verified, Action Taken, Closed, Overdue, Escalated, Rejected
            assigned_department TEXT DEFAULT 'Municipal Solid Waste Management',
            assigned_officer TEXT DEFAULT 'Officer S. Sharma (Zone 4)',
            escalation_level INTEGER DEFAULT 0, -- 0: Normal, 1: Overdue Reminder, 2: Escalated to Zonal Head, 3: Escalated to Commissioner
            escalated_to TEXT,
            inspection_notes TEXT,
            action_taken_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sla_ack_deadline TIMESTAMP,
            sla_escalation_deadline TIMESTAMP,
            acknowledged_at TIMESTAMP,
            closed_at TIMESTAMP
        )
    """)

    # Check and add 'description' column if table was created previously without it
    cursor.execute("PRAGMA table_info(complaints)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "description" not in columns:
        try:
            cursor.execute("ALTER TABLE complaints ADD COLUMN description TEXT")
        except Exception:
            pass

    # Users / Officers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'officer', -- 'officer', 'admin', 'field_officer'
            department TEXT DEFAULT 'Municipal Solid Waste Management',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Audit Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            action TEXT NOT NULL,
            performed_by TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
        )
    """)

    # Hotspot Cluster Cache Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotspot_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_name TEXT,
            center_lat REAL,
            center_lng REAL,
            report_count INTEGER DEFAULT 1,
            dominant_category TEXT,
            risk_level TEXT,
            last_reported TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    # Seed default officer accounts
    init_default_users()

def init_default_users():
    conn = get_connection()
    cursor = conn.cursor()

    default_users = [
        {
            "email": "officer@ecoguard.ai",
            "password": "officer123",
            "full_name": "Inspector S. Sharma",
            "role": "officer",
            "department": "Municipal Solid Waste Management (Ward 104)"
        },
        {
            "email": "admin@ecoguard.ai",
            "password": "admin123",
            "full_name": "Dr. V. Murthy",
            "role": "admin",
            "department": "State Pollution Control Board & Zonal Magistrate"
        },
        {
            "email": "inspector@ecoguard.ai",
            "password": "officer123",
            "full_name": "Inspector S. Mehta",
            "role": "officer",
            "department": "Town Planning & Enforcement Squad"
        }
    ]

    for u in default_users:
        cursor.execute("SELECT id FROM users WHERE email = ?", (u["email"],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role, department)
                VALUES (?, ?, ?, ?, ?)
            """, (u["email"], hash_password(u["password"]), u["full_name"], u["role"], u["department"]))

    conn.commit()
    conn.close()

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("SELECT id, email, full_name, role, department FROM users WHERE email = ? AND password_hash = ?", (email, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, role, department FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def log_audit(complaint_id: str, action: str, performed_by: str, details: str = "", conn: Optional[sqlite3.Connection] = None):
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (complaint_id, action, performed_by, details, timestamp)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (complaint_id, action, performed_by, details))
    if should_close:
        conn.commit()
        conn.close()

def get_complaint_by_id(complaint_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    if data.get("categories"):
        try:
            data["categories"] = json.loads(data["categories"])
        except:
            data["categories"] = [data["categories"]]
    return data

def get_all_complaints(status: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    if category and category != "All":
        query += " AND primary_category = ?"
        params.append(category)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        if d.get("categories"):
            try:
                d["categories"] = json.loads(d["categories"])
            except:
                d["categories"] = [d["categories"]]
        result.append(d)
    return result

def get_audit_trail(complaint_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM audit_logs 
        WHERE complaint_id = ? 
        ORDER BY id ASC
    """, (complaint_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
