# Agent Reasoning

The agent runs 4 steps before writing a single word. Each step receives the output of the previous one.

---

## Why multiple steps?

A single prompt — "given Stripe, Head of Payments, and AI fraud detection, write outreach" — produces generic output. Claude has no forcing function to think before writing.

Multi-step forces: understand context → identify pain → write message grounded in both.

---

## Step 0 — Memory Lookup

Queries the Memory API for past events on this company before any reasoning starts.

```python
# Returns structured past context:
{
    "hooks_already_used": ["Series C hiring surge signal"],
    "pain_points_already_found": ["Schema migration bottleneck"],
    "prior_message_subjects": ["False positive rates climbing at Stripe?"],
    "last_contact": "2026-03-12T09:41:00"
}
```

Flows into Steps 1, 2, and 3. If the API is unreachable — continues with empty context, never crashes.

---

## Step 1 — Company & Persona Analysis

Establishes business context and picks the right value driver before identifying any pain.

**Prompt:** `prompts/step1_analyze.txt`

**Output — `PersonaAnalysis`:**
```json
{
  "company_type": "Global payments infrastructure",
  "company_stage": "Enterprise",
  "persona_priorities": ["fraud accuracy", "false positive rate", "review overhead"],
  "value_driver": "Be Safe",
  "business_context": "Stripe operates at a scale where..."
}
```

**Framework applied:** 4 Value Drivers from agentic-seller — Make Money / Save Money / Go Fast / Be Safe. Persona language rules: VP Eng → velocity, CxO → revenue, CISO → risk.

**Why before Step 2:** Pain is only meaningful in context. "Fraud detection pain" at a startup is different from the same pain at Stripe's scale.

---

## Step 2 — Pain Point Identification

Identifies 2–3 specific pain points grounded in Step 1. Avoids repeating pain already found in past context.

**Prompt:** `prompts/step2_painpoints.txt`

**Output — `PainPoints`:**
```json
{
  "pain_points": [
    {
      "title": "Fraud patterns evolving faster than detection rules",
      "description": "Rule-based systems require manual updates each time...",
      "urgency_signal": "Transaction volume growing while fraud team stays flat"
    }
  ],
  "top_pain": "Fraud patterns evolving faster than detection rules",
  "why_anything": "Every week without better detection is quantifiable loss"
}
```

**Framework applied:** 3 Whys from agentic-seller — `why_anything` answers "what breaks if they do nothing?"

---

## Step 3 — Outreach Message Generation

Writes the message. Grounded in Steps 1 and 2. Avoids hooks already used in past context.

**Prompt:** `prompts/step3_outreach.txt`

**Output — `OutreachMessage`:**
```json
{
  "subject_line": "False positive rates climbing at Stripe?",
  "message_body": "Hi [Name],\n\nPayments teams at Stripe's scale...",
  "hook_used": "Transaction volume outpacing fraud team capacity",
  "value_driver_mapped": "Be Safe"
}
```

**Framework applied:** Hook → Pain → Evidence → CTA structure. Banned phrases list. Subject line = pain question, never product name.

**How memory changes output:**
- Run 1: picks strongest hook freely
- Run 2: `hooks_already_used` in prompt → agent explicitly avoids prior angle → different message

---

## Step chain

```
Step 0 (past_context)
    ├──▶ Step 1 — enriches analysis
    │         └──▶ Step 2 — grounds pain points
    │                   └──▶ Step 3 — avoids prior hooks, builds on 1+2
    └─────────────────────────────────────────────────────▶ Step 3
```
