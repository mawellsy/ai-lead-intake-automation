from fastapi.testclient import TestClient

import app.main as main_module
from app.db.lead_repository import SaveLeadResult
from app.main import app


client = TestClient(app)


VALID_LEAD = {
    "full_name": "Maya Chen",
    "email": "maya.chen@example.com",
    "phone": "+1-555-0101",
    "service_requested": "Plumbing repair",
    "message": "A pipe under the kitchen sink burst.",
    "city": "Riverton",
}


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_valid_lead(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "save_lead",
        lambda lead: SaveLeadResult(
            lead_id="lead-123",
            created=True,
        ),
    )

    response = client.post("/leads", json=VALID_LEAD)

    assert response.status_code == 201

    body = response.json()

    assert body["message"] == "Lead created"
    assert body["lead_id"] == "lead-123"
    assert body["created"] is True
    assert body["lead"]["email"] == "maya.chen@example.com"
    assert body["lead"]["source"] == "website"


def test_duplicate_lead_returns_existing_id(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "save_lead",
        lambda lead: SaveLeadResult(
            lead_id="existing-lead-123",
            created=False,
        ),
    )

    response = client.post("/leads", json=VALID_LEAD)

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == "Duplicate lead ignored"
    assert body["lead_id"] == "existing-lead-123"
    assert body["created"] is False


def test_create_lead_rejects_invalid_email():
    invalid_lead = {
        **VALID_LEAD,
        "email": "definitely-not-an-email",
    }

    response = client.post("/leads", json=invalid_lead)

    assert response.status_code == 422
