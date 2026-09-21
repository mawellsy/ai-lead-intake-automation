import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.ai.schemas import LeadClassification
from app.db.lead_repository import (
    mark_lead_for_review,
    save_lead,
    update_lead_classification,
)
from app.schemas import LeadCreate


@pytest.fixture
def test_engine(tmp_path):
    database_path = tmp_path / "test_ai_persistence.db"

    project_root = Path(__file__).resolve().parents[1]
    schema_path = project_root / "app" / "db" / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema)

    return create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )


@pytest.fixture
def lead():
    return LeadCreate(
        full_name="Maya Chen",
        email="maya.chen@example.com",
        phone="+1-555-0101",
        service_requested="Plumbing repair",
        message="A pipe under the kitchen sink burst.",
        city="Riverton",
    )


def test_classification_is_persisted(test_engine, lead):
    saved = save_lead(lead, test_engine)

    classification = LeadClassification(
        classification="emergency_repair",
        urgency="critical",
        ai_summary="Active water leak requires immediate attention.",
    )

    update_lead_classification(
        saved.lead_id,
        classification,
        test_engine,
    )

    with test_engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT classification, urgency, ai_summary, status
                FROM leads
                WHERE id = :lead_id
                """
            ),
            {"lead_id": saved.lead_id},
        ).mappings().one()

    assert row["classification"] == "emergency_repair"
    assert row["urgency"] == "critical"
    assert row["ai_summary"] == (
        "Active water leak requires immediate attention."
    )
    assert row["status"] == "open"


def test_failed_classification_routes_to_review(test_engine, lead):
    saved = save_lead(lead, test_engine)

    mark_lead_for_review(
        saved.lead_id,
        test_engine,
    )

    with test_engine.connect() as connection:
        status_value = connection.execute(
            text(
                """
                SELECT status
                FROM leads
                WHERE id = :lead_id
                """
            ),
            {"lead_id": saved.lead_id},
        ).scalar_one()

    assert status_value == "review"
