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
    classification_calls = []

    monkeypatch.setattr(
        main_module,
        "save_lead",
        lambda lead: SaveLeadResult(
            lead_id="lead-123",
            created=True,
        ),
    )

    monkeypatch.setattr(
        main_module,
        "classify_new_lead",
        lambda lead_id, lead: classification_calls.append(
            (lead_id, str(lead.email))
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
    assert classification_calls == [
        ("lead-123", "maya.chen@example.com")
    ]


def test_duplicate_lead_returns_existing_id(monkeypatch):
    classification_calls = []
    monkeypatch.setattr(
        main_module,
        "save_lead",
        lambda lead: SaveLeadResult(
            lead_id="existing-lead-123",
            created=False,
        ),
    )

    monkeypatch.setattr(
        main_module,
        "classify_new_lead",
        lambda lead_id, lead: classification_calls.append(
            (lead_id, str(lead.email))
        ),
    )

    response = client.post("/leads", json=VALID_LEAD)

    assert response.status_code == 200

    body = response.json()

    assert body["message"] == "Duplicate lead ignored"
    assert body["lead_id"] == "existing-lead-123"
    assert body["created"] is False
    assert classification_calls == []


def test_create_lead_rejects_invalid_email():
    invalid_lead = {
        **VALID_LEAD,
        "email": "definitely-not-an-email",
    }

    response = client.post("/leads", json=invalid_lead)

    assert response.status_code == 422


def test_openapi_documents_duplicate_response():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    responses = response.json()["paths"]["/leads"]["post"]["responses"]

    assert "200" in responses
    assert "201" in responses
    assert responses["200"]["description"] == "Duplicate lead already exists"
