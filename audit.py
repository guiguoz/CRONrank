import sqlite3
import database
from datetime import datetime
import json

def init_audit_log():
    """Initialise la table d'audit pour l'historique des modifications."""
    conn = database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL,
        table_name TEXT NOT NULL,
        record_id INTEGER,
        old_values TEXT,
        new_values TEXT,
        user_info TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def _convert_to_native(obj):
    """Convertit les types numpy/pandas en types Python natifs pour JSON."""
    if hasattr(obj, 'item'):
        return obj.item()
    return obj

def log_modification(action, table_name, record_id=None, old_values=None, new_values=None, user_info="System"):
    """Enregistre une modification dans l'audit log."""
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Convertir les valeurs numpy en types natifs Python
    if old_values:
        old_values = {k: _convert_to_native(v) for k, v in old_values.items()}
    if new_values:
        new_values = {k: _convert_to_native(v) for k, v in new_values.items()}
    
    cursor.execute("""
    INSERT INTO audit_log (timestamp, action, table_name, record_id, old_values, new_values, user_info)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        action,
        table_name,
        int(record_id) if record_id is not None else None,
        json.dumps(old_values) if old_values else None,
        json.dumps(new_values) if new_values else None,
        user_info
    ))
    
    conn.commit()
    conn.close()

def get_recent_modifications(limit=50):
    """Récupère les modifications récentes."""
    query = """
    SELECT timestamp, action, table_name, record_id, old_values, new_values
    FROM audit_log
    ORDER BY timestamp DESC
    LIMIT ?
    """
    return database.run_query(query, (limit,))

def get_point_modifications():
    """Récupère spécifiquement les modifications de points."""
    query = """
    SELECT timestamp, action, record_id, old_values, new_values
    FROM audit_log
    WHERE table_name = 'resultats' AND action = 'UPDATE'
    ORDER BY timestamp DESC
    LIMIT 20
    """
    return database.run_query(query)