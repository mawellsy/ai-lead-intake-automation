from fastapi.testclient import TestClient

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


def test_create_valid_lead():
    response = client.post("/leads", json=VALID_LEAD)

    assert response.status_code == 201

    body = response.json()

    assert body["message"] == "Lead accepted"
    assert body["lead"]["email"] == "maya.chen@example.com"
    assert body["lead"]["source"] == "website"


def test_create_lead_rejects_invalid_email():
    invalid_lead = {
        **VALID_LEAD,
        "email": "definitely-not-an-email",
    }

    response = client.post("/leads", json=invalid_lead)

    assert response.status_code == 422