import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.database import engine


def _deserialize_metadata(value: str | None) -> dict:
    if not value:
        return {}

    return json.loads(value)


def record_execution_event(
    *,
    lead_id: str | None,
    workflow_name: str,
    outcome: str,
    metadata: dict | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    db_engine: Engine = engine,
) -> dict:
    """Persist one completed workflow event."""

    log_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    with db_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO execution_logs (
                    id,
                    lead_id,
                    workflow_name,
                    started_at,
                    finished_at,
                    outcome,
                    error_type,
                    error_message,
                    metadata_json
                )
                VALUES (
                    :id,
                    :lead_id,
                    :workflow_name,
                    :started_at,
                    :finished_at,
                    :outcome,
                    :error_type,
                    :error_message,
                    :metadata_json
                )
                """
            ),
            {
                "id": log_id,
                "lead_id": lead_id,
                "workflow_name": workflow_name,
                "started_at": now,
                "finished_at": now,
                "outcome": outcome,
                "error_type": error_type,
                "error_message": error_message,
                "metadata_json": json.dumps(metadata or {}, sort_keys=True),
            },
        )

    return {
        "id": log_id,
        "lead_id": lead_id,
        "workflow_name": workflow_name,
        "started_at": now,
        "finished_at": now,
        "outcome": outcome,
        "error_type": error_type,
        "error_message": error_message,
        "metadata": metadata or {},
    }


def list_execution_events(
    *,
    lead_id: str | None = None,
    workflow_name: str | None = None,
    db_engine: Engine = engine,
) -> list[dict]:
    """Return workflow events, newest first."""

    clauses = []
    parameters = {}

    if lead_id is not None:
        clauses.append("lead_id = :lead_id")
        parameters["lead_id"] = lead_id

    if workflow_name is not None:
        clauses.append("workflow_name = :workflow_name")
        parameters["workflow_name"] = workflow_name

    where_clause = ""
    if clauses:
        where_clause = "WHERE " + " AND ".join(clauses)

    query = text(
        f"""
        SELECT
            id,
            lead_id,
            workflow_name,
            started_at,
            finished_at,
            outcome,
            error_type,
            error_message,
            metadata_json
        FROM execution_logs
        {where_clause}
        ORDER BY started_at DESC
        """
    )

    with db_engine.connect() as connection:
        rows = connection.execute(
            query,
            parameters,
        ).mappings().all()

    return [
        {
            "id": row["id"],
            "lead_id": row["lead_id"],
            "workflow_name": row["workflow_name"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "outcome": row["outcome"],
            "error_type": row["error_type"],
            "error_message": row["error_message"],
            "metadata": _deserialize_metadata(row["metadata_json"]),
        }
        for row in rows
    ]


def create_staff_notification(
    *,
    lead_id: str,
    customer_name: str,
    urgency: str | None,
    classification: str | None,
    message: str,
    db_engine: Engine = engine,
) -> dict:
    """Persist an internal staff notification using the execution event log."""

    metadata = {
        "kind": "staff_notification",
        "customer_name": customer_name,
        "urgency": urgency,
        "classification": classification,
        "message": message,
    }

    event = record_execution_event(
        lead_id=lead_id,
        workflow_name="staff_notification",
        outcome="success",
        metadata=metadata,
        db_engine=db_engine,
    )

    return {
        "notification_id": event["id"],
        "lead_id": lead_id,
        "customer_name": customer_name,
        "urgency": urgency,
        "classification": classification,
        "message": message,
        "created_at": event["started_at"],
    }


def list_staff_notifications(
    *,
    db_engine: Engine = engine,
) -> list[dict]:
    """Return persisted staff notifications, newest first."""

    events = list_execution_events(
        workflow_name="staff_notification",
        db_engine=db_engine,
    )

    notifications = []

    for event in events:
        metadata = event["metadata"]
        notifications.append(
            {
                "notification_id": event["id"],
                "lead_id": event["lead_id"],
                "customer_name": metadata.get("customer_name", ""),
                "urgency": metadata.get("urgency"),
                "classification": metadata.get("classification"),
                "message": metadata.get("message", ""),
                "created_at": event["started_at"],
            }
        )

    return notifications
