"""
Pipeline orchestrator — runs all 4 agent steps in sequence.

Flow:
    Step 0 — Memory Lookup      : check Agent Memory API for prior company events
    Step 1 — Persona Analysis   : analyze company + persona + product context
    Step 2 — Pain Points        : identify 2-3 specific pain points
    Step 3 — Outreach Message   : generate personalized cold outreach message
    Save   — Auto-store results : POST both pain_points and cold_outreach to Memory API

Each step receives only what it needs.
Past context from Step 0 flows into Steps 1, 2, and 3.
"""

import json
import os

import httpx
from dotenv import load_dotenv

from agent.models import AgentResult, SalesEventCreate
from agent.steps import (
    step0_memory_lookup,
    step1_analyze,
    step2_identify_pains,
    step3_generate_outreach,
)

load_dotenv()

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"


# ── Save results to Memory API ─────────────────────────────────────────────────

def _save_event(company: str, persona: str, product: str, event_type: str, content: dict) -> int | None:
    """
    POST a sales event to the Agent Memory API.
    Returns the saved event id, or None if the API is unreachable.
    """
    try:
        payload = SalesEventCreate(
            company=company,
            event_type=event_type,
            content=json.dumps(content),
            persona=persona,
            product_description=product,
        )
        response = httpx.post(
            f"{API_BASE_URL}/events",
            json=payload.model_dump(),
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json().get("id")
    except Exception:
        return None


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run(company: str, persona: str, product: str) -> AgentResult:
    """
    Run the full agent pipeline for a given company, persona, and product.

    Returns an AgentResult containing:
    - PersonaAnalysis   (Step 1 output)
    - PainPoints        (Step 2 output)
    - OutreachMessage   (Step 3 output)
    - Memory metadata   (whether past context was found and used)
    - saved_event_id    (ID of the cold_outreach event stored in Memory API)
    """

    # ── Step 0 — Memory Lookup ─────────────────────────────────────────────────
    past_events, past_context = step0_memory_lookup(company)

    # ── Step 1 — Company & Persona Analysis ───────────────────────────────────
    analysis = step1_analyze(
        company=company,
        persona=persona,
        product=product,
        past_context=past_context if past_context else None,
    )

    # ── Step 2 — Pain Point Identification ────────────────────────────────────
    pain_points = step2_identify_pains(
        company=company,
        persona=persona,
        product=product,
        analysis=analysis,
        past_context=past_context if past_context else None,
    )

    # ── Step 3 — Outreach Message Generation ──────────────────────────────────
    message = step3_generate_outreach(
        company=company,
        persona=persona,
        product=product,
        analysis=analysis,
        pain_points=pain_points,
        past_context=past_context if past_context else None,
    )

    # ── Save — Store results in Memory API ────────────────────────────────────
    # Save pain points as a separate event so future runs can avoid repeating them
    _save_event(
        company=company,
        persona=persona,
        product=product,
        event_type="pain_points",
        content=pain_points.model_dump(),
    )

    # Save the outreach message — this is the primary event for memory retrieval
    saved_event_id = _save_event(
        company=company,
        persona=persona,
        product=product,
        event_type="cold_outreach",
        content=message.model_dump(),
    )

    return AgentResult(
        company=company,
        persona=persona,
        product_description=product,
        analysis=analysis,
        pain_points=pain_points,
        message=message,
        used_past_context=bool(past_context),
        past_events_count=len(past_events),
        saved_event_id=saved_event_id,
    )
