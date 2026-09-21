import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.db.orchestration_repository import (
    create_staff_notification,
    list_execution_events,
    list_staff_notifications,
    record_execution_event,
)


@pytest.fixture
def test_engine(tmp_path):
    database_path = tmp_path / "test_orchestration.db"

    project_root = Path(__file__).resolve().parents[1]
    schema_path = project_root / "app" / "db" / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema)

    return create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )


def test_execution_event_is_persisted_with_metadata(test_engine):
    event = record_execution_event(
        lead_id=None,
        workflow_name="AI Lead Intake - Milestone 4 Orchestration",
        outcome="failed",
        metadata={"branch": "api_error"},
        error_type="HTTPError",
        error_message="Lead API failed",
        db_engine=test_engine,
    )

    stored = list_execution_events(
        db_engine=test_engine,
    )

    assert len(stored) == 1
    assert stored[0]["id"] == event["id"]
    assert stored[0]["outcome"] == "failed"
    assert stored[0]["metadata"] == {"branch": "api_error"}


def test_staff_notification_is_persisted_and_listed(test_engine):
    created = create_staff_notification(
        lead_id="lead-123",
        customer_name="Jordan Blake",
        urgency="critical",
        classification="emergency_repair",
        message="URGENT lead requires immediate attention.",
        db_engine=test_engine,
    )

    notifications = list_staff_notifications(
        db_engine=test_engine,
    )

    assert len(notifications) == 1
    assert notifications[0]["notification_id"] == created["notification_id"]
    assert notifications[0]["lead_id"] == "lead-123"
    assert notifications[0]["urgency"] == "critical"
    assert notifications[0]["message"] == (
        "URGENT lead requires immediate attention."
    )
