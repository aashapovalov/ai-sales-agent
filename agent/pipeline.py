"""
Pipeline orchestrator — runs all 4 agent steps in sequence.
Prints each step's result immediately as it completes.

Flow:
    Step 0 — Memory Lookup      : check Agent Memory API for prior company events
    Step 1 — Persona Analysis   : analyze company + persona + product context
    Step 2 — Pain Points        : identify 2-3 specific pain points
    Step 3 — Outreach Message   : generate personalized cold outreach message
    Save   — Auto-store results : POST both pain_points and cold_outreach to Memory API
"""

import json
import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from rich.console import Console

from agent.display import (
    display_saved,
    display_step0,
    display_step1,
    display_step2,
    display_step3,
)
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

def run(company: str, persona: str, product: str, console: Optional[Console] = None) -> AgentResult:
    """
    Run the full agent pipeline for a given company, persona, and product.
    Prints each step's result immediately as it completes.
    """
    if console is None:
        console = Console()

    # ── Step 0 — Memory Lookup ─────────────────────────────────────────────────
    console.print("\n  [dim]Step 0 — checking memory...[/dim]")
    past_events, past_context = step0_memory_lookup(company)
    display_step0(console, len(past_events), company)

    # ── Step 1 — Company & Persona Analysis ───────────────────────────────────
    console.print("\n  [dim]Step 1 — analyzing company and persona...[/dim]")
    analysis = step1_analyze(
        company=company,
        persona=persona,
        product=product,
        past_context=past_context if past_context else None,
    )
    display_step1(console, analysis)

    # ── Step 2 — Pain Point Identification ────────────────────────────────────
    console.print("\n  [dim]Step 2 — identifying pain points...[/dim]")
    pain_points = step2_identify_pains(
        company=company,
        persona=persona,
        product=product,
        analysis=analysis,
        past_context=past_context if past_context else None,
    )
    display_step2(console, pain_points)

    # ── Step 3 — Outreach Message Generation ──────────────────────────────────
    console.print("\n  [dim]Step 3 — generating outreach message...[/dim]")
    message = step3_generate_outreach(
        company=company,
        persona=persona,
        product=product,
        analysis=analysis,
        pain_points=pain_points,
        past_context=past_context if past_context else None,
    )
    display_step3(console, message)

    # ── Save — Store results in Memory API ────────────────────────────────────
    _save_event(
        company=company,
        persona=persona,
        product=product,
        event_type="pain_points",
        content=pain_points.model_dump(),
    )
    saved_event_id = _save_event(
        company=company,
        persona=persona,
        product=product,
        event_type="cold_outreach",
        content=message.model_dump(),
    )
    display_saved(console, saved_event_id, company)

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
