from fastapi.testclient import TestClient

import app.api.orchestration as orchestration_module
from app.main import app


client = TestClient(app)


def test_execution_log_endpoint_echoes_passthrough(monkeypatch):
    monkeypatch.setattr(
        orchestration_module,
        "record_execution_event",
        lambda **kwargs: {
            "id": "log-123",
            "lead_id": kwargs["lead_id"],
            "workflow_name": kwargs["workflow_name"],
            "started_at": "2026-09-21T03:00:00+00:00",
            "finished_at": "2026-09-21T03:00:00+00:00",
            "outcome": kwargs["outcome"],
            "error_type": kwargs["error_type"],
            "error_message": kwargs["error_message"],
            "metadata": kwargs["metadata"],
        },
    )

    response = client.post(
        "/execution-logs",
        json={
            "lead_id": "lead-123",
            "workflow_name": "AI Lead Intake - Milestone 4 Orchestration",
            "outcome": "success",
            "metadata": {"branch": "urgent"},
            "passthrough": {"result": "urgent"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["log"]["id"] == "log-123"
    assert body["passthrough"] == {"result": "urgent"}


def test_staff_notification_endpoint(monkeypatch):
    monkeypatch.setattr(
        orchestration_module,
        "create_staff_notification",
        lambda **kwargs: {
            "notification_id": "notification-123",
            "lead_id": kwargs["lead_id"],
            "customer_name": kwargs["customer_name"],
            "urgency": kwargs["urgency"],
            "classification": kwargs["classification"],
            "message": kwargs["message"],
            "created_at": "2026-09-21T03:00:00+00:00",
        },
    )

    response = client.post(
        "/staff-notifications",
        json={
            "lead_id": "lead-123",
            "customer_name": "Jordan Blake",
            "urgency": "critical",
            "classification": "emergency_repair",
            "message": "URGENT lead requires immediate attention.",
        },
    )

    assert response.status_code == 201
    assert response.json()["notification_id"] == "notification-123"
