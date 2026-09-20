# Learning Notes

## 1. Orchestration vs business logic

**Orchestration** coordinates steps: receive a trigger, call a service, branch on a result, send a notification, and schedule later work.

**Business logic** decides what the data means and what rules apply: whether an email is valid, how a duplicate key is formed, whether an AI response matches the allowed schema, or whether a lead should be marked urgent.

In this project, n8n will mainly orchestrate. Python will mainly own business logic that should be deterministic and testable.

## 2. Why validate at system boundaries

A system boundary is where data enters from something the application does not fully control, such as a browser form, webhook, API, or LLM.

Boundary validation prevents bad input from spreading into later steps. A useful mental model is:

```text
untrusted input -> validate -> normalized internal data -> business logic
```

The LLM is also an untrusted external system. Its response must be validated just like a webhook payload.

## 3. Why duplicate protection matters

Webhooks are often retried. Users also double-click submit buttons. A reliable workflow therefore cannot assume one real-world event produces exactly one request.

A later milestone will derive a deterministic `dedup_key` from normalized lead attributes and a time/business rule. The database enforces uniqueness so duplicate protection does not depend only on application code.

## 4. Why execution logs are separate from leads

A lead is business data. An execution log is process history.

One lead may be processed more than once because of retries, manual review, or follow-up tasks. Keeping execution history separate preserves that one-to-many relationship:

```text
Lead 1 ----< many ExecutionLogs
```

## 5. Why environment variables are used

API keys and deployment-specific settings should not be committed to Git. `.env.example` documents required variables, while the real `.env` stays local and is ignored by Git.

## Study next

Before Milestone 2, understand:

- HTTP POST requests and JSON bodies
- Pydantic models and validation
- normalization vs validation
- database primary keys, unique constraints, and indexes
- idempotency and duplicate detection
