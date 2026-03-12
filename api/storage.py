"""
Storage layer — SQLite backend for the Agent Memory API.

Intentionally isolated behind simple functions so the database
backend can be swapped (e.g. to PostgreSQL) by changing this
file only. The API server and agent pipeline never touch SQL directly.

Schema:
    sales_events
        id               INTEGER PRIMARY KEY AUTOINCREMENT
        company          TEXT NOT NULL
        event_type       TEXT NOT NULL
        content          TEXT NOT NULL  -- JSON-stringified agent output
        persona          TEXT NOT NULL
        product_description TEXT NOT NULL
        timestamp        TEXT NOT NULL  -- ISO 8601
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from agent.models import SalesEvent, SalesEventCreate

DB_PATH = "sales_events.db"


# ── Setup ──────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create the events table if it doesn't exist. Called on API startup."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_events (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                company             TEXT NOT NULL,
                event_type          TEXT NOT NULL,
                content             TEXT NOT NULL,
                persona             TEXT NOT NULL,
                product_description TEXT NOT NULL,
                timestamp           TEXT NOT NULL
            )
        """)
        conn.commit()


# ── Write ──────────────────────────────────────────────────────────────────────

def save_event(event: SalesEventCreate) -> SalesEvent:
    """
    Insert a new sales event. Returns the saved event with id + timestamp.
    Timestamp is always set server-side in UTC.
    """
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO sales_events
                (company, event_type, content, persona, product_description, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.company,
                event.event_type,
                event.content,
                event.persona,
                event.product_description,
                now,
            ),
        )
        conn.commit()
        event_id = cursor.lastrowid

    return SalesEvent(
        id=event_id,
        company=event.company,
        event_type=event.event_type,
        content=event.content,
        persona=event.persona,
        product_description=event.product_description,
        timestamp=datetime.fromisoformat(now),
    )


# ── Read ───────────────────────────────────────────────────────────────────────

def _row_to_event(row: sqlite3.Row) -> SalesEvent:
    return SalesEvent(
        id=row["id"],
        company=row["company"],
        event_type=row["event_type"],
        content=row["content"],
        persona=row["persona"],
        product_description=row["product_description"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
    )


def get_events(
    company: Optional[str] = None,
    event_type: Optional[str] = None,
) -> list[SalesEvent]:
    """
    Retrieve events with optional filters.
    Supports: company only, event_type only, or both combined.
    Results ordered newest first.
    """
    query = "SELECT * FROM sales_events WHERE 1=1"
    params: list = []

    if company:
        query += " AND LOWER(company) = LOWER(?)"
        params.append(company)

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    query += " ORDER BY timestamp DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [_row_to_event(row) for row in rows]


def get_portfolio_summary(company: str) -> dict:
    """
    Aggregate all events for a company into a structured summary.
    Designed for agent-to-agent use: a second agent (e.g. call prep)
    can query this endpoint to get a full history brief without
    reading raw events.
    """
    events = get_events(company=company)

    if not events:
        return {
            "company": company,
            "total_events": 0,
            "event_types": [],
            "pain_points_discovered": [],
            "messages_sent": [],
            "hooks_used": [],
            "last_contact": None,
        }

    pain_points: list[str] = []
    messages_sent: list[str] = []
    hooks_used: list[str] = []

    for event in events:
        try:
            data = json.loads(event.content)
        except (json.JSONDecodeError, TypeError):
            continue

        if event.event_type == "pain_points":
            for pp in data.get("pain_points", []):
                pain_points.append(pp.get("title", ""))

        if event.event_type == "cold_outreach":
            messages_sent.append(data.get("subject_line", ""))
            hook = data.get("hook_used", "")
            if hook:
                hooks_used.append(hook)

    event_types = list({e.event_type for e in events})
    last_contact = events[0].timestamp.isoformat() if events else None

    return {
        "company": company,
        "total_events": len(events),
        "event_types": event_types,
        "pain_points_discovered": [p for p in pain_points if p],
        "messages_sent": [m for m in messages_sent if m],
        "hooks_used": [h for h in hooks_used if h],
        "last_contact": last_contact,
    }
