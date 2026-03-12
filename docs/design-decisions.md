# Design Decisions

Key decisions made during implementation and the reasoning behind each.

---

## What I borrowed from agentic-seller

The [agentic-seller](https://github.com/romiluz13/agentic-seller) repository is a prompt-engineering
codebase — skills, memory layers, reasoning chains defined in markdown.
I treated it as a design spec and ported its logic into Python.

| Borrowed from | Used in |
|---|---|
| 4 Value Drivers (Make Money / Save Money / Go Fast / Be Safe) | `prompts/step1_analyze.txt` |
| Persona language rules (VP Eng → velocity, CxO → revenue) | `prompts/step1_analyze.txt` |
| 3 Whys framework (Why Anything / Why Product / Why Now) | `prompts/step2_painpoints.txt` |
| Pain-before-product rule | `prompts/step3_outreach.txt` |
| Banned phrases list | `prompts/step3_outreach.txt` |
| Message structure (Hook → Pain → Evidence → CTA) | `prompts/step3_outreach.txt` |
| 3-layer memory architecture (persistent / living / history) | `api/storage.py`, `agent/steps.py` |
| Skill-to-skill chain pattern (research → outreach) | `agent/pipeline.py` |

---

## Two models: SalesEventCreate vs SalesEvent

`SalesEventCreate` is what the client sends — no `id`, no `timestamp`.
`SalesEvent` is what the server returns — with both fields set server-side.

This makes the API contract explicit: the client never sets `id` or `timestamp`,
the server always does. One model with optional fields would work but would
allow invalid states — a retrieved event without an `id`, or a create request
with a forged timestamp.

---

## Storage layer isolation

All SQL is contained in `api/storage.py`. No other file writes SQL directly.

The motivation is the company's planned migration away from their current backend.
Swapping the storage layer requires changing one file — `get_connection()`,
`init_db()`, and column type mappings. The API routes, agent steps,
and Pydantic models are completely unaffected.

---

## Two events saved per run

Each pipeline run saves two events:

- `pain_points` — after Step 2
- `cold_outreach` — after Step 3

Saving pain points separately means future runs have access to what pains
were already identified — not just what messages were sent. This gives
Step 2 richer context to avoid repetition and go deeper on the next run.

---

## Graceful degradation when Memory API is down

Both Step 0 (memory lookup) and the save step catch all exceptions silently
and continue with empty context. The agent never fails because the API is unreachable.

This was a deliberate choice: the CLI should be runnable standalone
(`python run_agent.py`) without requiring the API server to be running first.
The Memory API is an enhancement, not a hard dependency.

---

## JSON mode for all Claude responses

Every step instructs Claude to return only JSON — no prose, no markdown fences.
Each response is parsed into a Pydantic model immediately.

This makes the chain reliable: each step receives a typed object, not a string
it needs to interpret. Pydantic validation catches malformed responses at the
boundary between steps rather than deep inside pipeline logic.

The prompt includes a fallback in `_call_claude()` that strips markdown fences
if Claude adds them despite instructions — a common failure mode.

---

## Content stored as JSON string in the database

The `content` column in `sales_events` stores the agent output as a JSON string
rather than separate columns per field.

This keeps the schema stable. If the agent output evolves — new fields added
to `OutreachMessage`, for example — no database migration is needed.
The `get_portfolio_summary()` function parses the JSON at read time,
so it always works with whatever structure was stored.

---

## Model selection

All steps use `claude-sonnet-4-5` — the best balance of reasoning quality
and response speed for a CLI tool where the user is waiting.

Following the agentic-seller model selection guidance:
- Haiku for simple formatting tasks
- Sonnet (default) for reasoning, writing, summarization
- Opus for deep research and complex synthesis

All steps here are reasoning + writing tasks — Sonnet is the right choice.
