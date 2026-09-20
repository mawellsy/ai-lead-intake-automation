import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.db.lead_repository import build_dedup_key, save_lead
from app.schemas import LeadCreate


@pytest.fixture
def test_engine(tmp_path):
    database_path = tmp_path / "test_leads.db"

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


def test_dedup_key_is_stable():
    first = LeadCreate(
        full_name="Maya Chen",
        email="MAYA.CHEN@example.com",
        phone="+1-555-0101",
        service_requested="Plumbing repair",
        message="A pipe under the kitchen sink burst.",
        city="Riverton",
    )

    second = LeadCreate(
        full_name="Maya Chen",
        email="maya.chen@example.com",
        phone="1 555 0101",
        service_requested="  Plumbing   repair ",
        message="A pipe under the kitchen sink burst.",
        city="Riverton",
    )

    assert build_dedup_key(first) == build_dedup_key(second)


def test_new_lead_is_saved(test_engine, lead):
    result = save_lead(lead, test_engine)

    assert result.created is True

    with test_engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM leads")
        ).scalar_one()

    assert count == 1


def test_duplicate_lead_is_not_saved_twice(test_engine, lead):
    first = save_lead(lead, test_engine)
    second = save_lead(lead, test_engine)

    assert first.created is True
    assert second.created is False
    assert second.lead_id == first.lead_id

    with test_engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM leads")
        ).scalar_one()

    assert count == 1