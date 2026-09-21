import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

import app.main as main_module
from app.db.lead_repository import get_lead, save_lead
from app.main import app
from app.schemas import LeadCreate


client = TestClient(app)


@pytest.fixture
def test_engine(tmp_path):
    database_path = tmp_path / "test_lead_lookup.db"

    project_root = Path(__file__).resolve().parents[1]
    schema_path = project_root / "app" / "db" / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema)

    return create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )


def test_get_lead_returns_saved_record(test_engine):
    lead = LeadCreate(
        full_name="Maya Chen",
        email="maya.chen@example.com",
        phone="+1-555-0101",
        service_requested="Plumbing repair",
        message="A pipe under the kitchen sink burst.",
        city="Riverton",
    )

    saved = save_lead(lead, test_engine)
    stored = get_lead(saved.lead_id, test_engine)

    assert stored is not None
    assert stored["id"] == saved.lead_id
    assert stored["email"] == "maya.chen@example.com"
    assert stored["status"] == "new"


def test_get_lead_endpoint_returns_processed_record(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "get_lead",
        lambda lead_id: {
            "id": lead_id,
            "full_name": "Elena Torres",
            "email": "elena.torres@example.com",
            "phone": "+1-555-0314",
            "service_requested": "Electrical repair",
            "message": "Sparks are coming from an outlet.",
            "city": "Riverton",
            "created_at": "2026-09-21T03:00:00+00:00",
            "classification": "emergency_repair",
            "urgency": "critical",
            "status": "open",
            "source": "website",
            "ai_summary": "Electrical fault requires urgent repair.",
            "follow_up_at": None,
            "updated_at": "2026-09-21T03:00:01+00:00",
        },
    )

    response = client.get("/leads/lead-123")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "lead-123"
    assert body["urgency"] == "critical"
    assert body["status"] == "open"


def test_get_lead_endpoint_returns_404(monkeypatch):
    monkeypatch.setattr(main_module, "get_lead", lambda lead_id: None)

    response = client.get("/leads/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Lead not found"}
