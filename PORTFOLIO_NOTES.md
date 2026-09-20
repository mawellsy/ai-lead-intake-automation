# Portfolio Notes

## Problems solved

- Establishes a clear architecture for automating website lead intake.
- Separates deterministic validation/business logic from workflow orchestration.
- Plans for duplicate protection, failure routing, and execution traceability from the start.

## Skills demonstrated

- workflow architecture
- Python project organization
- environment-based configuration
- relational database design
- SQLite schema design with a path toward PostgreSQL
- Mermaid architecture documentation
- reliability-oriented system design

## Important architectural decisions

### Python + n8n split

Python will own logic that should be deterministic and unit-testable. n8n will own visible orchestration and integrations.

Reason: this creates a portfolio project that demonstrates both software engineering and practical automation without introducing unnecessary services.

### SQLite first

SQLite minimizes demo setup. Database access will later be placed behind a clean persistence layer so PostgreSQL can replace SQLite without changing business rules.

### Execution logs are first-class data

Lead processing must be traceable. The database therefore includes an `execution_logs` table from the beginning instead of treating logging as an afterthought.

## Measurable business benefits to quantify later

- average manual triage time saved per lead
- reduction in response delay for urgent leads
- percentage of leads classified without manual review
- duplicate submissions prevented
- follow-ups generated automatically

## Screenshots / demo moments to capture later

- n8n workflow overview
- successful urgent lead execution
- duplicate lead route
- malformed AI response routed safely to review
- database record and execution log for the same lead
- customer acknowledgement output

## Potential Upwork proposal talking points

- automation of repetitive intake workflows
- reliable AI integration with schema validation
- webhook/API integration
- duplicate-safe processing
- human-review fallback instead of silent failure
- observable workflows with execution history
