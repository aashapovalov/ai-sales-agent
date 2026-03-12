# AI Sales Agent

A multi-step AI agent that generates personalized cold outreach messages.
Built as a standalone Python CLI with a persistent Agent Memory API.

Inspired by the [agentic-seller](https://github.com/romiluz13/agentic-seller) framework —
its reasoning methodology, persona logic, and outreach rules informed the agent's prompt architecture.

---

## What it does

Give it a company, a target persona, and your product. It reasons in three steps before writing a single word:

1. **Analyzes** the company and persona — stage, priorities, value driver
2. **Identifies** 2–3 specific pain points for that persona
3. **Generates** a personalized cold outreach message based on steps 1 and 2

Each step's result is displayed immediately as it completes — no waiting for everything at once.

On subsequent runs for the same company, it **retrieves past interactions** from the Agent Memory API
and adjusts — avoiding hooks already used, building on pain points already discovered.

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/your-username/ai-sales-agent
cd ai-sales-agent
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Add your Anthropic API key to .env
```

### 3. Start the Agent Memory API (recommended)

```bash
python start_api.py
```

Runs at `http://127.0.0.1:8000` — interactive docs at `http://127.0.0.1:8000/docs`

### 4. Run the agent

In a new terminal:

```bash
python run_agent.py
```

---

## Example

```
  Company name:        Stripe
  Target persona:      Head of Payments
  Product description: AI fraud detection platform

  Step 0 — checking memory...
  ◦ Memory: No prior events found for Stripe — fresh start

  ── Step 1 — Company & Persona Analysis ──────────────────
  Company type:   Global payments infrastructure
  Stage:          Enterprise
  Value driver:   Be Safe
  Persona priorities:
    • fraud detection accuracy
    • false positive rate
    • manual review overhead

  Step 2 — identifying pain points...

  ── Step 2 — Pain Point Identification ───────────────────
  Top pain: Increasing fraud complexity outpacing rule-based systems
  1. Fraud pattern complexity growing faster than detection rules
  2. Manual investigation overhead scaling with transaction volume
  3. Early detection gap in high-velocity transaction windows

  Step 3 — generating outreach message...

  ── Step 3 — Outreach Message ────────────────────────────
  ┌──────────────────────────────────────────────────────┐
  │ Subject: False positive rates climbing at Stripe?    │
  │                                                      │
  │ Payments teams at Stripe's scale find that fraud     │
  │ patterns evolve faster than the rules written to     │
  │ catch them...                                        │
  └──────────────────────────────────────────────────────┘
  ✓ Saved to memory as event #1
```

---

## Requirements

- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com))

---

## Documentation

| Document | What it covers |
|---|---|
| [Architecture](docs/architecture.md) | System design, components, data flow |
| [Agent Reasoning](docs/agent-reasoning.md) | The 4-step pipeline explained |
| [Memory API](docs/memory-api.md) | API endpoints, curl examples |
| [Design Decisions](docs/design-decisions.md) | Why these choices were made |

---

## Project structure

```
ai-sales-agent/
├── run_agent.py          ← CLI entry point
├── start_api.py          ← starts the Memory API server
├── agent/
│   ├── models.py         ← Pydantic schemas for all steps
│   ├── steps.py          ← 4 reasoning step functions
│   ├── pipeline.py       ← orchestrates the full run
│   └── display.py        ← all Rich terminal output
├── api/
│   ├── server.py         ← FastAPI routes
│   └── storage.py        ← SQLite storage layer
├── prompts/
│   ├── step1_analyze.txt
│   ├── step2_painpoints.txt
│   └── step3_outreach.txt
└── docs/
    ├── architecture.md
    ├── agent-reasoning.md
    ├── memory-api.md
    └── design-decisions.md
```
