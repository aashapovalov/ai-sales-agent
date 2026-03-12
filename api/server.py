"""
Agent Memory API — FastAPI server.

Endpoints:
    POST /events                        Store a new sales event
    GET  /events?company=X&type=Y       Retrieve events with optional filters
    GET  /portfolio-summary?company=X   Aggregated company history for agent use

Designed for agent-to-agent use: the outreach agent writes events after
each run, and any other agent (call prep, follow-up, etc.) can read them
as a knowledge base before generating new content.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from typing import Optional

from agent.models import SalesEvent, SalesEventCreate
from api.storage import get_events, get_portfolio_summary, init_db, save_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    init_db()
    yield


app = FastAPI(
    title="AI Sales Agent — Memory API",
    description=(
        "Stores and retrieves sales interaction events. "
        "Acts as a shared knowledge base for AI sales agents."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# ── Events ─────────────────────────────────────────────────────────────────────

@app.post("/events", response_model=SalesEvent, status_code=201)
def create_event(event: SalesEventCreate) -> SalesEvent:
    """
    Store a new sales event.

    Called automatically by the agent after generating an outreach message.
    Can also be called manually to seed the knowledge base with prior
    interactions — call summaries, pain points discovered, follow-up notes.

    event_type options:
        cold_outreach | pain_points | call_summary | follow_up_plan | portfolio_summary
    """
    return save_event(event)


@app.get("/events", response_model=list[SalesEvent])
def list_events(
    company: Optional[str] = Query(default=None, description="Filter by company name (case-insensitive)"),
    type: Optional[str] = Query(default=None, description="Filter by event type"),
) -> list[SalesEvent]:
    """
    Retrieve sales events with optional filters.

    Examples:
        GET /events                          → all events
        GET /events?company=Stripe           → all Stripe events
        GET /events?type=cold_outreach       → all cold outreach events
        GET /events?company=Stripe&type=cold_outreach → combined filter
    """
    return get_events(company=company, event_type=type)


# ── Portfolio summary ──────────────────────────────────────────────────────────

@app.get("/portfolio-summary")
def portfolio_summary(
    company: str = Query(description="Company name to summarize"),
) -> dict:
    """
    Aggregated history for a company — designed for agent-to-agent use.

    A second agent (e.g. call prep, follow-up generator) can query this
    endpoint to get a structured brief without reading raw events.

    Returns:
        total_events, event_types, pain_points_discovered,
        messages_sent, hooks_used, last_contact
    """
    if not company:
        raise HTTPException(status_code=400, detail="company parameter is required")

    return get_portfolio_summary(company=company)
