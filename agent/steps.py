"""
Agent reasoning steps — each step calls the Claude API with a structured prompt.

Step 0 — Memory Lookup      : query the Memory API for past events on this company
Step 1 — Persona Analysis   : analyze company + persona + product context
Step 2 — Pain Points        : identify 2-3 specific pain points
Step 3 — Outreach Message   : generate personalized cold outreach message

Each step receives the output of the previous step as input.
Steps 1-3 call Claude API and return validated Pydantic models.
Step 0 calls the Memory API via HTTP and returns raw event data.
"""

import json
import os
from pathlib import Path
from typing import Optional

import anthropic
import httpx
from dotenv import load_dotenv

from agent.models import OutreachMessage, PainPoints, PersonaAnalysis, SalesEvent

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
MODEL = "claude-sonnet-4-5"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = Path(__file__).parent.parent / "prompts" / filename
    return path.read_text(encoding="utf-8")


def _call_claude(system_prompt: str, user_message: str) -> dict:
    """
    Call Claude API and return parsed JSON.
    All steps use JSON mode — Claude is instructed to return only JSON.
    Raises ValueError if the response cannot be parsed.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if Claude adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\nRaw response:\n{raw}")


def _format_past_context(events: list[SalesEvent]) -> dict:
    """
    Extract structured context from past events for use in prompts.
    Surfaces hooks already used, pain points already found, and last contact date.
    This is what makes Step 3 behave differently when memory exists.
    """
    if not events:
        return {}

    hooks_used: list[str] = []
    pain_points_found: list[str] = []
    prior_messages: list[str] = []
    last_contact = events[0].timestamp.isoformat() if events[0].timestamp else None

    for event in events:
        try:
            data = json.loads(event.content)
        except (json.JSONDecodeError, TypeError):
            continue

        if event.event_type == "cold_outreach":
            hook = data.get("hook_used", "")
            subject = data.get("subject_line", "")
            if hook:
                hooks_used.append(hook)
            if subject:
                prior_messages.append(subject)

        if event.event_type == "pain_points":
            for pp in data.get("pain_points", []):
                title = pp.get("title", "")
                if title:
                    pain_points_found.append(title)

    return {
        "total_prior_events": len(events),
        "last_contact": last_contact,
        "hooks_already_used": hooks_used,
        "pain_points_already_found": pain_points_found,
        "prior_message_subjects": prior_messages,
    }


# ── Step 0 — Memory Lookup ─────────────────────────────────────────────────────

def step0_memory_lookup(company: str) -> tuple[list[SalesEvent], dict]:
    """
    Query the Agent Memory API for past events related to this company.
    Returns (raw events list, formatted context dict).

    If the API is unreachable, returns empty results and continues —
    the agent degrades gracefully without memory rather than failing.
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/events",
            params={"company": company},
            timeout=5.0,
        )
        response.raise_for_status()
        raw_events = response.json()
        events = [SalesEvent(**e) for e in raw_events]
        past_context = _format_past_context(events)
        return events, past_context

    except httpx.ConnectError:
        # API not running — degrade gracefully
        return [], {}
    except Exception as e:
        # Any other error — degrade gracefully
        print(f"  ⚠ Memory API unavailable: {e}")
        return [], {}


# ── Step 1 — Company & Persona Analysis ────────────────────────────────────────

def step1_analyze(
    company: str,
    persona: str,
    product: str,
    past_context: Optional[dict] = None,
) -> PersonaAnalysis:
    """
    Analyze the company and persona to establish business context
    and identify the right value driver to lead with.
    """
    system_prompt = _load_prompt("step1_analyze.txt")

    user_message = f"""
Company: {company}
Target Persona: {persona}
Product Being Sold: {product}
Past Context: {json.dumps(past_context) if past_context else "None — first time contacting this company"}
"""

    data = _call_claude(system_prompt, user_message)
    return PersonaAnalysis(**data)


# ── Step 2 — Pain Point Identification ─────────────────────────────────────────

def step2_identify_pains(
    company: str,
    persona: str,
    product: str,
    analysis: PersonaAnalysis,
    past_context: Optional[dict] = None,
) -> PainPoints:
    """
    Identify 2-3 specific pain points this persona likely experiences.
    Builds on the PersonaAnalysis from Step 1.
    Avoids repeating pain points already found in past context.
    """
    system_prompt = _load_prompt("step2_painpoints.txt")

    user_message = f"""
Company: {company}
Target Persona: {persona}
Product Being Sold: {product}

Step 1 Analysis:
{analysis.model_dump_json(indent=2)}

Past Context: {json.dumps(past_context) if past_context else "None"}
"""

    data = _call_claude(system_prompt, user_message)
    return PainPoints(**data)


# ── Step 3 — Outreach Message Generation ───────────────────────────────────────

def step3_generate_outreach(
    company: str,
    persona: str,
    product: str,
    analysis: PersonaAnalysis,
    pain_points: PainPoints,
    past_context: Optional[dict] = None,
) -> OutreachMessage:
    """
    Generate a personalized cold outreach message.
    Builds on Steps 1 and 2. Uses past context to avoid repeating
    hooks and angles already used in prior outreach to this company.
    """
    system_prompt = _load_prompt("step3_outreach.txt")

    user_message = f"""
Company: {company}
Target Persona: {persona}
Product Being Sold: {product}

Step 1 — Persona Analysis:
{analysis.model_dump_json(indent=2)}

Step 2 — Pain Points:
{pain_points.model_dump_json(indent=2)}

Past Context (memory from prior interactions):
{json.dumps(past_context, indent=2) if past_context else "None — this is the first outreach to this company"}
"""

    data = _call_claude(system_prompt, user_message)
    return OutreachMessage(**data)
