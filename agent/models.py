"""
Pydantic models for the AI Sales Agent pipeline.

Each model represents the structured output of one agent step.
The same SalesEvent model is shared between the agent pipeline
and the FastAPI storage layer — defined once, used everywhere.

Reasoning framework borrowed from agentic-seller/CLAUDE.md:
- 4 Value Drivers: Make Money / Save Money / Go Fast / Be Safe
- 3 Whys: Why Anything / Why Product / Why Now
- Pain-before-product rule
- Persona language (VP Eng = velocity, CxO = revenue)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Step 1 output ─────────────────────────────────────────────────────────────

class PersonaAnalysis(BaseModel):
    """
    Output of Step 1: Company & Persona Analysis.
    Captures what kind of company this is, what the persona cares about,
    and which value driver to lead with.
    """
    company_type: str               # e.g. "Global payments infrastructure"
    company_stage: str              # e.g. "Series B scale-up", "Enterprise"
    persona_priorities: list[str]   # e.g. ["fraud rate", "false positives"]
    value_driver: str               # Make Money | Save Money | Go Fast | Be Safe
    business_context: str           # 2-3 sentence summary of the business situation


# ── Step 2 output ─────────────────────────────────────────────────────────────

class PainPoint(BaseModel):
    """A single pain point with its urgency signal."""
    title: str          # e.g. "Increasing fraud pattern complexity"
    description: str    # 1-2 sentences explaining the pain
    urgency_signal: str # what makes this urgent right now


class PainPoints(BaseModel):
    """
    Output of Step 2: Pain Point Identification.
    2-3 pain points specific to the persona and company context.
    Includes the 'Why Anything' from the 3 Whys framework:
    what breaks if they do nothing.
    """
    pain_points: list[PainPoint]
    top_pain: str       # the single strongest pain to lead with
    why_anything: str   # cost of status quo — why doing nothing is worse


# ── Step 3 output ─────────────────────────────────────────────────────────────

class OutreachMessage(BaseModel):
    """
    Output of Step 3: Outreach Message Generation.
    A short personalized cold outreach message.
    Follows write-outreach skill rules: hook → pain → evidence → CTA.
    No product name in opener. No banned phrases.
    """
    subject_line: str       # pain hypothesis as a question, never product name
    message_body: str       # the full message
    hook_used: str          # which signal or angle was used as the opener
    value_driver_mapped: str # which of the 4 value drivers this maps to


# ── Shared: agent + API ────────────────────────────────────────────────────────

class SalesEvent(BaseModel):
    """
    A sales interaction event stored in the Agent Memory API.
    Shared between the agent pipeline (writes) and FastAPI (reads/writes).

    event_type options (from agentic-seller bonus spec):
      cold_outreach | pain_points | call_summary | follow_up_plan | portfolio_summary
    """
    id: Optional[int] = None
    company: str
    event_type: str
    content: str            # JSON-stringified output from the relevant agent step
    persona: str
    product_description: str
    timestamp: Optional[datetime] = None


class SalesEventCreate(BaseModel):
    """Input schema for POST /events — id and timestamp are set by the server."""
    company: str
    event_type: str
    content: str
    persona: str
    product_description: str


# ── Pipeline result ────────────────────────────────────────────────────────────

class AgentResult(BaseModel):
    """
    The complete output of one full pipeline run.
    Returned by pipeline.run() and displayed by the CLI.
    """
    company: str
    persona: str
    product_description: str
    analysis: PersonaAnalysis
    pain_points: PainPoints
    message: OutreachMessage
    used_past_context: bool         # True if Step 0 found prior events
    past_events_count: int          # how many past events were found
    saved_event_id: Optional[int] = None  # ID returned by the API after saving
