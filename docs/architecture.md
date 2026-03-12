# Architecture

## Overview

The system has two independent processes that work together:

```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│      run_agent.py           │     │      start_api.py           │
│      CLI Agent              │     │      Memory API             │
│                             │     │                             │
│  Collects user input        │     │  FastAPI + SQLite           │
│  Runs 4-step pipeline       │────▶│  Stores sales events        │
│  Displays results           │◀────│  Serves past context        │
│                             │     │                             │
│  Runs once, then exits      │     │  Runs continuously          │
└─────────────────────────────┘     └─────────────────────────────┘
       Terminal 1                          Terminal 2
```

Both processes are optional to run together — the agent degrades gracefully
if the Memory API is not running, skipping memory lookup and save steps.

---

## Component map

```
ai-sales-agent/
│
├── run_agent.py              CLI entry point
│     └── agent/pipeline.py  Orchestrates all 4 steps
│           ├── agent/steps.py        Step functions (Claude API calls)
│           │     └── prompts/*.txt   Prompt templates per step
│           └── agent/models.py       Pydantic schemas (shared)
│
├── start_api.py              API server entry point
│     └── api/server.py       FastAPI route definitions
│           ├── api/storage.py        SQLite read/write layer
│           └── agent/models.py       Pydantic schemas (shared)
│
└── sales_events.db           SQLite database (auto-created on first run)
```

`agent/models.py` is the only file used by both processes —
it defines the shared data contracts between the agent and the API.

---

## Data flow — single run

```
User input
(company, persona, product)
        │
        ▼
┌───────────────────┐
│     Step 0        │  GET /events?company={company}
│  Memory Lookup    │──────────────────────────────▶ Memory API
│                   │◀────────────────────────────── past events[]
└────────┬──────────┘
         │ past_context{}
         ▼
┌───────────────────┐
│     Step 1        │  Prompt: step1_analyze.txt
│  Persona Analysis │──────────────────────────────▶ Claude API
│                   │◀────────────────────────────── PersonaAnalysis{}
└────────┬──────────┘
         │ analysis{}
         ▼
┌───────────────────┐
│     Step 2        │  Prompt: step2_painpoints.txt
│  Pain Points      │──────────────────────────────▶ Claude API
│                   │◀────────────────────────────── PainPoints{}
└────────┬──────────┘
         │ pain_points{}
         ▼
┌───────────────────┐
│     Step 3        │  Prompt: step3_outreach.txt
│  Outreach Message │──────────────────────────────▶ Claude API
│                   │◀────────────────────────────── OutreachMessage{}
└────────┬──────────┘
         │ message{}
         ▼
┌───────────────────┐
│     Save          │  POST /events (pain_points)
│  Memory API       │  POST /events (cold_outreach)
└────────┬──────────┘
         │ AgentResult{}
         ▼
    CLI Display
```

---

## Data flow — second run for the same company

On a subsequent run, Step 0 finds prior events and extracts:

```
past_context = {
    "total_prior_events": 2,
    "last_contact": "2026-03-12T09:41:00",
    "hooks_already_used": ["Series C hiring surge signal"],
    "pain_points_already_found": ["Schema migration bottleneck"],
    "prior_message_subjects": ["False positive rates climbing at Stripe?"]
}
```

This flows into:
- **Step 1** — enriches company analysis with prior knowledge
- **Step 2** — avoids repeating pain points already discovered
- **Step 3** — avoids repeating hooks already used in prior messages

The agent's output is demonstrably different on the second run.

---

## Database schema

```sql
CREATE TABLE sales_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company             TEXT NOT NULL,
    event_type          TEXT NOT NULL,
    content             TEXT NOT NULL,   -- JSON string
    persona             TEXT NOT NULL,
    product_description TEXT NOT NULL,
    timestamp           TEXT NOT NULL    -- ISO 8601 UTC
);
```

`content` stores the JSON-serialized output of the relevant agent step.
Keeping it as a text field makes the schema stable regardless of
what the agent produces — new fields in the output don't require
a schema migration.

---

## Storage layer isolation

The entire database interaction is contained in `api/storage.py`.
`api/server.py` and `agent/steps.py` never write SQL directly.

Swapping SQLite for PostgreSQL or any other backend requires
changes in `api/storage.py` only — specifically:

- `get_connection()` — replace with a Postgres connection
- `init_db()` — replace `CREATE TABLE` with your migration tool
- Column types — `INTEGER`, `TEXT` map directly to Postgres equivalents

No other file needs to change.
