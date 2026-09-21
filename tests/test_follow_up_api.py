from fastapi.testclient import TestClient

import app.api.follow_up as follow_up_module
from app.main import app


client = TestClient(app)


def test_due_follow_up_endpoint(monkeypatch):
    monkeypatch.setattr(
        follow_up_module,
        "list_due_follow_ups",
        lambda: [
            {
                "id": "lead-123",
                "full_name": "Taylor Morgan",
                "email": "taylor@example.com",
                "phone": None,
                "service_requested": "Kitchen remodel quote",
                "message": "Please send a quote.",
                "city": "Riverton",
                "created_at": "2026-09-20T03:00:00+00:00",
                "classification": "quote_request",
                "urgency": "normal",
                "status": "open",
                "ai_summary": "Customer requests a quote.",
                "follow_up_at": "2026-09-21T03:00:00+00:00",
            }
        ],
    )

    response = client.get("/follow-ups/due")

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "lead-123"


def test_process_follow_up_endpoint(monkeypatch):
    monkeypatch.setattr(
        follow_up_module,
        "process_due_follow_up",
        lambda lead_id: {
            "task_id": "task-123",
            "lead_id": lead_id,
            "customer_name": "Taylor Morgan",
            "email": "taylor@example.com",
            "classification": "quote_request",
            "urgency": "normal",
            "due_at": "2026-09-21T03:00:00+00:00",
            "staff_notification": "Quote follow-up due: Taylor Morgan",
            "customer_follow_up": "Hi Taylor Morgan, we're following up on your quote request.",
            "completed_at": "2026-09-21T04:00:00+00:00",
        },
    )

    response = client.post("/follow-ups/lead-123/process")

    assert response.status_code == 200
    assert response.json()["task_id"] == "task-123"
    assert response.json()["lead_id"] == "lead-123"


def test_process_follow_up_returns_404_for_missing_lead(monkeypatch):
    def raise_missing(_lead_id):
        raise LookupError("Lead not found: missing")

    monkeypatch.setattr(
        follow_up_module,
        "process_due_follow_up",
        raise_missing,
    )

    response = client.post("/follow-ups/missing/process")

    assert response.status_code == 404


def test_process_follow_up_returns_409_when_not_due(monkeypatch):
    def raise_not_due(_lead_id):
        raise ValueError("Follow-up is not due for lead: lead-123")

    monkeypatch.setattr(
        follow_up_module,
        "process_due_follow_up",
        raise_not_due,
    )

    response = client.post("/follow-ups/lead-123/process")

    assert response.status_code == 409
