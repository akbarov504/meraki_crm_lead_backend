import sqlite3

DB_NAME = "leads.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                crm_id INTEGER,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def is_processed(lead_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM leads WHERE lead_id = ?",
            (lead_id,)
        ).fetchone()

        return row is not None and row["status"] == "success"

def save_lead_status(lead_id, status, crm_id=None, error=None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO leads (lead_id, status, crm_id, error)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(lead_id) DO UPDATE SET
                status = excluded.status,
                crm_id = excluded.crm_id,
                error = excluded.error,
                updated_at = CURRENT_TIMESTAMP
        """, (lead_id, status, crm_id, error))

        conn.commit()
