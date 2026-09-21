# Learning Notes

These notes summarize the concepts I should be able to explain without relying on the code or an AI assistant.

## 1. Orchestration vs business logic

**Orchestration** coordinates steps: receive a trigger, call a service, branch on a result, send a notification, schedule later work, and record the outcome.

**Business logic** defines deterministic rules: whether input is valid, how duplicates are detected, whether an AI response matches the allowed schema, when a quote follow-up becomes due, and whether a task has already been processed.

In this project:

```text
n8n = orchestration
Python/FastAPI = deterministic business logic and API boundary
SQLite = durable state
OpenAI = constrained classification
```

This separation makes the system easier to test and easier to demonstrate.

## 2. Why validate at system boundaries

A boundary is where data enters from something the application does not fully control:

- website or webhook payload
- external API
- LLM response
- workflow integration

The useful pattern is:

```text
untrusted input -> validation -> normalized internal data -> business logic
```

The model is not a trusted component just because the application asked it a question. Its output still requires schema validation.

## 3. Validation vs normalization

**Validation** answers whether input is acceptable.

Examples:

- email must have a valid shape
- required fields cannot be missing
- AI classification must be one of the allowed enum values

**Normalization** makes equivalent inputs consistent.

Examples:

- lowercase email
- strip surrounding whitespace
- remove formatting characters when comparing phone numbers
- normalize message text before hashing

Both matter because reliable duplicate detection requires consistent input, not merely valid input.

## 4. Idempotency and duplicate detection

Webhooks can retry. Users can double-click. Networks can time out after a server has already completed the request.

An idempotent workflow allows the same logical request to arrive again without creating repeated side effects.

This project builds a deterministic `dedup_key` from normalized lead attributes and stores it under a unique database constraint.

The important lesson is that application code alone is not enough. Two requests can race. The database uniqueness rule is the final protection.

## 5. Persist before calling AI

The lead is written to the database before classification.

This ordering matters:

```text
receive lead
-> validate
-> persist
-> call AI
-> update classification
```

If the model provider is unavailable after persistence, the system can mark the existing lead for manual review. The customer request is still retained.

A less reliable ordering would call AI first and only persist afterward. A provider failure could then lose the lead entirely.

## 6. Structured LLM output

The model is asked to return a constrained structure:

```text
classification
urgency
ai_summary
```

The allowed classifications and urgency values are enums.

Benefits:

- downstream code receives predictable types
- unexpected fields can be rejected
- workflow branches do not depend on parsing prose
- malformed responses can be retried or routed safely

The model still makes a probabilistic judgment. The schema controls the shape of that judgment, not whether the judgment is always correct.

## 7. Retry vs fallback

Retries are appropriate for failures that may be temporary or malformed responses that may succeed on another attempt.

Retries should be bounded. Infinite retries create a different failure mode.

After the retry budget is exhausted, this project uses a manual-review fallback:

```text
AI failure -> keep lead -> status=review -> staff alert
```

The business process continues even though automation confidence has ended.

## 8. Why execution logs are separate from leads

A lead is business data. An execution log is process history.

One lead can produce multiple events:

```text
Lead
 ├─ intake workflow
 ├─ staff notification
 ├─ manual-review event
 └─ follow-up task
```

Keeping those records separate preserves a one-to-many audit history instead of overwriting the lead every time the workflow does something.

## 9. Why n8n does not own the database rules

Visual workflow tools are excellent for orchestration and integrations, but important correctness rules are easier to unit test in code.

For example, the hourly follow-up workflow asks FastAPI for due work. FastAPI decides which leads qualify and atomically claims a task.

That prevents a workflow edit from accidentally changing the definition of a due lead or processing the same task twice.

## 10. Scheduled follow-up and time-based state

For `quote_request` leads, classification sets:

```text
follow_up_at = classification_time + 24 hours
```

The scheduler does not sleep for 24 hours per lead. Instead, n8n checks periodically:

```text
hourly trigger
-> GET due follow-ups
-> process each due lead
```

This polling design is simple, observable, and survives restarts because the schedule lives in database state.

## 11. Claim-once processing

Selecting a due task is not enough. Two workers could select the same task before either finishes.

The processing step therefore uses a conditional update. It succeeds only while the lead is still open, still a quote request, and still has a due `follow_up_at`.

After success, `follow_up_at` is cleared.

Conceptually:

```text
read due task
-> UPDATE ... WHERE task is still due
-> if one row changed: I claimed it
-> if zero rows changed: someone else already did
```

This is a lightweight concurrency-control pattern.

## 12. Internal notifications vs external delivery

The project currently persists a staff notification event rather than requiring Slack, Teams, SMTP, or SMS credentials.

That choice keeps the demo reproducible while preserving a clear integration boundary.

In production, the n8n node that persists the alert could be followed or replaced by a real delivery integration. The core lead and follow-up rules would not need to change.

## 13. Environment variables and secrets

API keys and deployment-specific values should not be committed to Git.

`.env.example` documents required configuration. The real `.env` remains local and ignored.

Exported n8n workflows should also be inspected before committing so credentials or tokens are not accidentally embedded in JSON.

## 14. What the automated tests are proving

The current suite has 43 passing tests.

The important goal is not the number itself. The suite protects behavior that would be expensive to discover manually:

- malformed lead rejection
- duplicate handling
- AI schema enforcement
- AI provider failures
- classification persistence
- manual-review fallback
- orchestration API behavior
- due-follow-up selection
- follow-up idempotence

A portfolio project is stronger when the demo is backed by reproducible tests rather than only successful screenshots.

## 15. Production gaps I should understand

Before describing this as production-ready, I should understand how I would add:

- PostgreSQL and migrations
- API authentication
- signed webhook verification
- rate limiting
- queues and background workers
- deployment and reverse proxies
- centralized secrets
- CI/CD
- metrics, alerts, and log retention
- privacy and data-retention policies
- real email/SMS/Slack delivery
- CRM integration

The useful interview answer is not "the project already has everything." It is being able to explain what is implemented, why it is reliable within its scope, and what would change for a real client deployment.
