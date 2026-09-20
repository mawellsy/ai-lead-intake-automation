import pytest
from pydantic import ValidationError

from app.schemas import LeadCreate


VALID_LEAD = {
    "full_name": "Maya Chen",
    "email": "maya.chen@example.com",
    "phone": "+1-555-0101",
    "service_requested": "Plumbing repair",
    "message": "A pipe under the kitchen sink burst.",
    "city": "Riverton",
}


def test_valid_lead_is_accepted_and_normalized():
    lead = LeadCreate(
        **{
            **VALID_LEAD,
            "full_name": "  Maya Chen  ",
            "email": "MAYA.CHEN@example.com",
        }
    )

    assert lead.full_name == "Maya Chen"
    assert str(lead.email) == "maya.chen@example.com"
    assert lead.source == "website"


def test_invalid_email_is_rejected():
    with pytest.raises(ValidationError):
        LeadCreate(
            **{
                **VALID_LEAD,
                "email": "not-an-email",
            }
        )


def test_blank_required_field_is_rejected():
    with pytest.raises(ValidationError):
        LeadCreate(
            **{
                **VALID_LEAD,
                "message": "   ",
            }
        )


def test_unexpected_field_is_rejected():
    with pytest.raises(ValidationError):
        LeadCreate(
            **VALID_LEAD,
            admin=True,
        )