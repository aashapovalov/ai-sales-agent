# Memory API

The Agent Memory API stores and retrieves sales interaction events.
It acts as a shared knowledge base — the outreach agent writes to it,
and any other agent can read from it before generating new content.

Start the server:
```bash
python start_api.py
# Running at http://127.0.0.1:8000
# Interactive docs at http://127.0.0.1:8000/docs
```

---

## Endpoints

### `POST /events` — store a sales event

```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Stripe",
    "event_type": "cold_outreach",
    "content": "{\"subject_line\": \"False positive rates climbing?\", \"hook_used\": \"volume signal\"}",
    "persona": "Head of Payments",
    "product_description": "AI fraud detection platform"
  }'
```

**Response:**
```json
{
  "id": 1,
  "company": "Stripe",
  "event_type": "cold_outreach",
  "content": "...",
  "persona": "Head of Payments",
  "product_description": "AI fraud detection platform",
  "timestamp": "2026-03-12T09:41:00+00:00"
}
```

Called automatically by the agent after each run. Can also be called manually
to seed the knowledge base with prior interactions.

---

### `GET /events` — retrieve events

```bash
# All events
curl http://127.0.0.1:8000/events

# Filter by company (case-insensitive)
curl http://127.0.0.1:8000/events?company=Stripe

# Filter by event type
curl http://127.0.0.1:8000/events?type=cold_outreach

# Combined filter
curl http://127.0.0.1:8000/events?company=Stripe&type=cold_outreach
```

Returns a list of `SalesEvent` objects ordered newest first.

---

### `GET /portfolio-summary` — aggregated company history

Designed for agent-to-agent use. Returns a structured brief without
requiring the caller to parse raw events.

```bash
curl http://127.0.0.1:8000/portfolio-summary?company=Stripe
```

**Response:**
```json
{
  "company": "Stripe",
  "total_events": 4,
  "event_types": ["cold_outreach", "pain_points"],
  "pain_points_discovered": [
    "Fraud patterns evolving faster than detection rules",
    "Manual review overhead scaling with volume"
  ],
  "messages_sent": [
    "False positive rates climbing at Stripe?",
    "Manual review queue backing up before peak season?"
  ],
  "hooks_used": [
    "Transaction volume outpacing fraud team capacity",
    "Holiday season review backlog signal"
  ],
  "last_contact": "2026-03-12T09:41:00+00:00"
}
```

---

### `GET /health` — health check

```bash
curl http://127.0.0.1:8000/health
# {"status": "ok"}
```

---

## Event types

| Type | Written by | Contains |
|---|---|---|
| `cold_outreach` | Agent (automatic) | Subject line, message body, hook used, value driver |
| `pain_points` | Agent (automatic) | 2–3 pain points with descriptions and urgency signals |
| `call_summary` | Human or call agent | Notes from a discovery call |
| `follow_up_plan` | Human or follow-up agent | Next steps after an interaction |
| `portfolio_summary` | Human or summary agent | Aggregated company brief |

The first two are written automatically on every agent run.
The rest can be added manually via `POST /events` to seed the knowledge base
with prior interactions that happened outside this system.

---

## Interactive docs

FastAPI auto-generates a full interactive API explorer at:

```
http://127.0.0.1:8000/docs
```

All endpoints can be tested there without writing any curl commands.
