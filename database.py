import sqlite3
from datetime import datetime, timedelta, timezone

DB_NAME = "leads.db"

def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=30
    )

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

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_status
            ON leads(status)
        """)

        conn.commit()

def claim_lead(lead_id):
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            """
            SELECT status, updated_at
            FROM leads
            WHERE lead_id = ?
            """,
            (lead_id,)
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO leads (lead_id, status)
                VALUES (?, 'processing')
                """,
                (lead_id,)
            )

            conn.commit()
            return True

        status = row["status"]

        if status == "success":
            conn.commit()
            return False

        if status == "processing":
            try:
                updated_at = datetime.fromisoformat(
                    row["updated_at"]
                )

                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(
                        tzinfo=timezone.utc
                    )

                if datetime.now(timezone.utc) - updated_at < timedelta(
                    minutes=10
                ):
                    conn.commit()
                    return False

            except (ValueError, TypeError):
                conn.commit()
                return False

        conn.execute(
            """
            UPDATE leads
            SET status = 'processing',
                error = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE lead_id = ?
            """,
            (lead_id,)
        )

        conn.commit()
        return True

def is_processed(lead_id):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status
            FROM leads
            WHERE lead_id = ?
            """,
            (lead_id,)
        ).fetchone()

        return row is not None and row["status"] == "success"

def save_lead_status(
    lead_id,
    status,
    crm_id=None,
    error=None
):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO leads (
                lead_id,
                status,
                crm_id,
                error
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(lead_id) DO UPDATE SET
                status = excluded.status,
                crm_id = excluded.crm_id,
                error = excluded.error,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                lead_id,
                status,
                crm_id,
                error
            )
        )

        conn.commit()
