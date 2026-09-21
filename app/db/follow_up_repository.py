import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.database import engine


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def list_due_follow_ups(
    *,
    as_of: datetime | None = None,
    db_engine: Engine = engine,
) -> list[dict]:
    """Return open quote requests whose scheduled follow-up time has arrived."""

    cutoff = (as_of or _utc_now()).isoformat()

    with db_engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    id,
                    full_name,
                    email,
                    phone,
                    service_requested,
                    message,
                    city,
                    created_at,
                    classification,
                    urgency,
                    status,
                    ai_summary,
                    follow_up_at
                FROM leads
                WHERE classification = 'quote_request'
                  AND status = 'open'
                  AND follow_up_at IS NOT NULL
                  AND follow_up_at <= :cutoff
                ORDER BY follow_up_at ASC, id ASC
                """
            ),
            {"cutoff": cutoff},
        ).mappings().all()

    return [dict(row) for row in rows]


def process_due_follow_up(
    lead_id: str,
    *,
    as_of: datetime | None = None,
    db_engine: Engine = engine,
) -> dict:
    """
    Claim one due follow-up exactly once and persist a durable task event.

    Clearing ``follow_up_at`` prevents the hourly scheduler from processing the
    same lead again. The conditional UPDATE protects against a second worker
    claiming the same lead after it has already been processed.
    """

    now_value = as_of or _utc_now()
    now = now_value.isoformat()
    task_id = str(uuid4())

    with db_engine.begin() as connection:
        lead = connection.execute(
            text(
                """
                SELECT
                    id,
                    full_name,
                    email,
                    classification,
                    urgency,
                    status,
                    ai_summary,
                    follow_up_at
                FROM leads
                WHERE id = :lead_id
                """
            ),
            {"lead_id": lead_id},
        ).mappings().first()

        if lead is None:
            raise LookupError(f"Lead not found: {lead_id}")

        if (
            lead["classification"] != "quote_request"
            or lead["status"] != "open"
            or lead["follow_up_at"] is None
            or lead["follow_up_at"] > now
        ):
            raise ValueError(f"Follow-up is not due for lead: {lead_id}")

        update_result = connection.execute(
            text(
                """
                UPDATE leads
                SET
                    follow_up_at = NULL,
                    updated_at = :updated_at
                WHERE id = :lead_id
                  AND classification = 'quote_request'
                  AND status = 'open'
                  AND follow_up_at IS NOT NULL
                  AND follow_up_at <= :cutoff
                """
            ),
            {
                "lead_id": lead_id,
                "updated_at": now,
                "cutoff": now,
            },
        )

        if update_result.rowcount != 1:
            raise ValueError(f"Follow-up was already processed for lead: {lead_id}")

        staff_notification = (
            "Quote follow-up due: "
            f"{lead['full_name']} | {lead['email']} | "
            f"scheduled for {lead['follow_up_at']}"
        )
        customer_follow_up = (
            f"Hi {lead['full_name']}, we're following up on your quote request. "
            "If you'd like to continue, reply and our team will help with next steps."
        )

        metadata = {
            "kind": "follow_up_task",
            "task_id": task_id,
            "lead_id": lead_id,
            "customer_name": lead["full_name"],
            "email": lead["email"],
            "classification": lead["classification"],
            "urgency": lead["urgency"],
            "due_at": lead["follow_up_at"],
            "staff_notification": staff_notification,
            "customer_follow_up": customer_follow_up,
        }

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
                    NULL,
                    NULL,
                    :metadata_json
                )
                """
            ),
            {
                "id": task_id,
                "lead_id": lead_id,
                "workflow_name": "follow_up_task",
                "started_at": now,
                "finished_at": now,
                "outcome": "success",
                "metadata_json": json.dumps(metadata, sort_keys=True),
            },
        )

    return {
        "task_id": task_id,
        "lead_id": lead_id,
        "customer_name": lead["full_name"],
        "email": lead["email"],
        "classification": lead["classification"],
        "urgency": lead["urgency"],
        "due_at": lead["follow_up_at"],
        "staff_notification": staff_notification,
        "customer_follow_up": customer_follow_up,
        "completed_at": now,
    }
