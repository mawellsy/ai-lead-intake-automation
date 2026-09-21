import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.ai.schemas import LeadClassification
from app.db.follow_up_repository import (
    list_due_follow_ups,
    process_due_follow_up,
)
from app.db.lead_repository import update_lead_classification


@pytest.fixture
def test_engine(tmp_path):
    database_path = tmp_path / "test_follow_up.db"
    schema_path = Path(__file__).resolve().parents[1] / "app" / "db" / "schema.sql"

    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))

    return create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )


def insert_lead(
    test_engine,
    *,
    lead_id: str,
    classification: str | None,
    status: str,
    follow_up_at: str | None,
):
    now = datetime.now(timezone.utc).isoformat()

    with test_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO leads (
                    id,
                    full_name,
                    email,
                    service_requested,
                    message,
                    created_at,
                    classification,
                    urgency,
                    status,
                    source,
                    follow_up_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :full_name,
                    :email,
                    :service_requested,
                    :message,
                    :created_at,
                    :classification,
                    :urgency,
                    :status,
                    :source,
                    :follow_up_at,
                    :updated_at
                )
                """
            ),
            {
                "id": lead_id,
                "full_name": "Taylor Morgan",
                "email": f"{lead_id}@example.com",
                "service_requested": "Kitchen remodel quote",
                "message": "Please send a quote for the work.",
                "created_at": now,
                "classification": classification,
                "urgency": "normal",
                "status": status,
                "source": "website",
                "follow_up_at": follow_up_at,
                "updated_at": now,
            },
        )


def test_quote_request_classification_schedules_follow_up(test_engine):
    insert_lead(
        test_engine,
        lead_id="lead-quote",
        classification=None,
        status="new",
        follow_up_at=None,
    )

    before = datetime.now(timezone.utc)
    update_lead_classification(
        "lead-quote",
        LeadClassification(
            classification="quote_request",
            urgency="normal",
            ai_summary="Customer requests a project quote.",
        ),
        db_engine=test_engine,
    )

    with test_engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT status, follow_up_at
                FROM leads
                WHERE id = 'lead-quote'
                """
            )
        ).mappings().one()

    scheduled_at = datetime.fromisoformat(row["follow_up_at"])
    assert row["status"] == "open"
    assert before + timedelta(hours=23, minutes=59) <= scheduled_at
    assert scheduled_at <= datetime.now(timezone.utc) + timedelta(hours=24, minutes=1)


def test_due_follow_ups_filters_future_non_quote_and_closed_leads(test_engine):
    now = datetime.now(timezone.utc)
    due_at = (now - timedelta(minutes=1)).isoformat()
    future_at = (now + timedelta(hours=1)).isoformat()

    insert_lead(
        test_engine,
        lead_id="due",
        classification="quote_request",
        status="open",
        follow_up_at=due_at,
    )
    insert_lead(
        test_engine,
        lead_id="future",
        classification="quote_request",
        status="open",
        follow_up_at=future_at,
    )
    insert_lead(
        test_engine,
        lead_id="maintenance",
        classification="maintenance",
        status="open",
        follow_up_at=due_at,
    )
    insert_lead(
        test_engine,
        lead_id="closed",
        classification="quote_request",
        status="closed",
        follow_up_at=due_at,
    )

    due = list_due_follow_ups(
        as_of=now,
        db_engine=test_engine,
    )

    assert [lead["id"] for lead in due] == ["due"]


def test_processing_follow_up_is_idempotent_and_creates_task_event(test_engine):
    now = datetime.now(timezone.utc)
    due_at = (now - timedelta(hours=1)).isoformat()

    insert_lead(
        test_engine,
        lead_id="due",
        classification="quote_request",
        status="open",
        follow_up_at=due_at,
    )

    result = process_due_follow_up(
        "due",
        as_of=now,
        db_engine=test_engine,
    )

    assert result["lead_id"] == "due"
    assert result["classification"] == "quote_request"
    assert result["due_at"] == due_at
    assert "following up on your quote request" in result["customer_follow_up"]

    with test_engine.connect() as connection:
        lead = connection.execute(
            text("SELECT follow_up_at FROM leads WHERE id = 'due'")
        ).mappings().one()
        event = connection.execute(
            text(
                """
                SELECT workflow_name, outcome, metadata_json
                FROM execution_logs
                WHERE id = :task_id
                """
            ),
            {"task_id": result["task_id"]},
        ).mappings().one()

    assert lead["follow_up_at"] is None
    assert event["workflow_name"] == "follow_up_task"
    assert event["outcome"] == "success"
    assert json.loads(event["metadata_json"])["kind"] == "follow_up_task"

    with pytest.raises(ValueError, match="Follow-up is not due"):
        process_due_follow_up(
            "due",
            as_of=now,
            db_engine=test_engine,
        )
