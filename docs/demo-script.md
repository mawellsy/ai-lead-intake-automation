# Two-Minute Portfolio Demo Script

This walkthrough is designed for an Upwork call, interview, or recorded portfolio demo. It uses only synthetic data.

## 0:00-0:20 - State the business problem

> A home-service company receives website leads that staff normally have to read, classify, record, prioritize, and remember to follow up. This project automates that workflow while keeping failure handling and audit history visible.

Show the architecture section in `README.md`.

Explain the responsibility split in one sentence:

> FastAPI owns deterministic validation and persistence, OpenAI performs constrained classification, and n8n orchestrates the business workflow.

## 0:20-0:55 - Show urgent lead intake

Open the Milestone 4 n8n workflow and use the committed screenshot if a live execution is not convenient:

`docs/screenshots/intake-urgent-workflow.png`

Use the synthetic urgent scenario:

```json
{
  "full_name": "Sofia Ramirez",
  "service_requested": "Electrical repair",
  "message": "There is smoke coming from the breaker box and the wall is hot."
}
```

Explain:

> The lead is validated and persisted first. AI classified it as `emergency_repair` with `critical` urgency. n8n then took the urgent branch, persisted a staff alert, returned an urgent customer acknowledgement, and logged the terminal workflow result.

Mention duplicate protection briefly:

> If the same logical request arrives again, the API returns the existing lead instead of creating duplicate downstream work.

## 0:55-1:15 - Show safe AI failure handling

Explain the synthetic Nina Patel test:

> I deliberately started the API without an OpenAI key. The lead was still saved, classification fields stayed empty, its status became `review`, and n8n persisted a manual-review staff alert.

Key sentence:

> AI failure changes the routing decision, not whether the customer request survives.

## 1:15-1:45 - Show automatic follow-up

Open:

`docs/screenshots/follow-up-workflow.png`

Explain:

> Quote requests receive a `follow_up_at` timestamp 24 hours after classification. An hourly n8n workflow asks FastAPI for due work. FastAPI atomically claims each due task, clears `follow_up_at`, prepares the staff and customer follow-up content, and writes a durable task record.

Point out that the second due query returned an empty list.

Key sentence:

> Clearing the schedule during the claim makes the follow-up idempotent, so the hourly workflow cannot process the same task repeatedly.

## 1:45-2:00 - Close with reliability evidence

Show:

```bash
pytest -q
```

and the result:

```text
43 passed
```

Close with:

> The portfolio goal was not just to make an AI demo. It was to build a repeatable business automation with validation, duplicate protection, human fallback, scheduled follow-up, and traceable execution history. The next production steps would be PostgreSQL, authentication, real notification providers, deployment, and monitoring.
