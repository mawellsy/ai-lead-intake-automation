# Portfolio Notes

## Case study summary

### Problem

A home-service company manually reviews website inquiries, identifies urgent requests, records leads, watches for duplicates, and remembers which quote requests still need follow-up.

### Solution

The project automates that workflow with FastAPI, n8n, SQLite, and structured LLM classification. Python owns deterministic validation and persistence. n8n owns visible orchestration, branching, scheduling, and integration steps. Failures are routed safely rather than hidden.

### Business value demonstrated

- urgent leads can be identified immediately instead of waiting in a shared inbox
- duplicate submissions do not create duplicate work
- routine leads are classified and queued consistently
- AI outages preserve the lead and create a manual-review path
- quote requests receive a scheduled 24-hour follow-up
- execution history makes each automated path traceable

## Skills demonstrated

- FastAPI API design
- Pydantic validation and structured outputs
- OpenAI API integration
- prompt design for bounded classification tasks
- SQLAlchemy and SQLite persistence
- database constraints and idempotency
- n8n webhook orchestration
- n8n scheduled workflows
- REST and JSON integration
- retry and failure-path design
- human-in-the-loop fallback
- durable execution logging
- pytest unit and API testing
- Git-based incremental development
- documentation and portfolio presentation

## Important architectural decisions

### Persist before AI classification

A new lead is stored before the model is called.

Why it matters: an OpenAI outage or malformed AI response can change routing, but it cannot erase the customer's request.

### Python owns deterministic business rules

Validation, duplicate keys, database writes, structured-output checks, follow-up timing, and one-time follow-up claiming live in Python.

Why it matters: these rules can be tested directly and do not depend on a visual workflow being configured perfectly.

### n8n owns orchestration

n8n receives webhook traffic, calls FastAPI, branches on stored state, prepares responses, persists staff alerts, logs terminal outcomes, and runs the hourly follow-up check.

Why it matters: the workflow remains easy to demonstrate and change without moving core correctness rules out of tested code.

### AI output is treated as untrusted input

The classifier accepts only the defined classification, urgency, and summary schema.

Why it matters: the workflow does not branch directly on arbitrary model prose.

### Duplicate handling is idempotent

A normalized fingerprint is protected by a unique database constraint.

Why it matters: retries and double submissions return the existing lead instead of creating duplicate downstream work.

### Follow-ups are claimed exactly once

A due quote request is processed with a conditional database update that clears `follow_up_at`.

Why it matters: the hourly scheduler cannot send the same lead through the follow-up workflow over and over.

### Execution logs are first-class data

Workflow outcomes are stored separately from lead records.

Why it matters: one lead can have intake, staff notification, review, and follow-up events while preserving a usable audit trail.

## Verified demo scenarios

| Synthetic scenario | Result |
| --- | --- |
| Sofia Ramirez, sparking electrical panel | urgent branch, `emergency_repair`, `critical`, staff alert persisted |
| Repeated Sofia submission | duplicate branch, existing lead returned |
| Marcus Lee, routine HVAC maintenance | normal queue, `maintenance`, `low` |
| Invalid email payload | API failure branch with HTTP 422 |
| Nina Patel with AI deliberately disabled | lead preserved, `status=review`, manual-review staff alert |
| Grace Kim through published production webhook | production webhook successfully queued maintenance lead |
| Daniel Foster quote request | 24-hour follow-up scheduled, manually fast-forwarded, processed once, staff alert and task logged |

## Test evidence

Current verified automated test result:

```text
43 passed
```

Coverage includes:

- lead input validation
- duplicate detection and persistence
- AI schema validation
- classifier retry/failure behavior
- OpenAI provider integration through mocked clients
- classification persistence
- orchestration API endpoints
- lead lookup
- due-follow-up selection
- one-time follow-up processing

## Portfolio screenshots

Committed screenshots:

- `docs/screenshots/intake-urgent-workflow.png`
- `docs/screenshots/follow-up-workflow.png`

Additional screenshots worth capturing if the portfolio needs a longer case study:

- FastAPI Swagger page showing the lead and follow-up endpoints
- execution-log JSON tying one lead to several workflow events
- manual-review n8n path
- published n8n intake workflow overview
- terminal output showing `43 passed`

## Illustrative business benefit

Use a transparent scenario instead of claiming unmeasured ROI.

Example:

```text
40 leads/day
× 3 minutes of manual triage and recording
× 80% handled automatically
= 96 minutes/day

96 minutes/day × 5 days = 8 hours/week
```

This is an illustrative model, not a measured production result. Real savings depend on lead volume, handling time, review rate, and integrations.

## Upwork proposal talking points

- I can automate lead intake from webhook through database persistence and response.
- I separate AI judgment from deterministic business rules so failures are easier to control.
- I build duplicate-safe and retry-safe workflows rather than assuming every webhook runs once.
- I add human review paths instead of allowing an AI failure to lose customer data.
- I can combine custom Python/FastAPI logic with n8n orchestration.
- I design scheduled follow-up workflows with idempotent processing.
- I leave behind tests, exported workflows, logs, and documentation rather than only a visual automation.

## Two-minute demo moments

1. Show the architecture and explain the Python/n8n split.
2. Submit or show the urgent synthetic lead and highlight the urgent branch.
3. Show the persisted staff alert and execution log.
4. Explain the AI-off manual-review path in one sentence.
5. Show the quote follow-up workflow and its successful manual demo execution.
6. End with `43 passed` and the one-time follow-up guarantee.

See `docs/demo-script.md` for the exact script.

## Limitations to state clearly

- local demo deployment
- SQLite rather than PostgreSQL
- no authentication or signed webhooks
- no real Slack/email/SMS notification provider
- prepared customer follow-up is logged but not actually sent
- no CRM integration
- no CI/CD or production monitoring yet

Being explicit about these limitations improves the portfolio. It shows the difference between a reliable prototype and a production deployment instead of pretending localhost is a data center with ambitions.
