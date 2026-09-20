import pytest
from pydantic import ValidationError

from app.ai.schemas import LeadCategory, LeadClassification, LeadUrgency


def test_valid_ai_classification_is_accepted():
    result = LeadClassification(
        classification="emergency_repair",
        urgency="critical",
        ai_summary="Active water leak requires immediate attention.",
    )

    assert result.classification == LeadCategory.EMERGENCY_REPAIR
    assert result.urgency == LeadUrgency.CRITICAL
    assert result.ai_summary == "Active water leak requires immediate attention."


def test_invalid_classification_is_rejected():
    with pytest.raises(ValidationError):
        LeadClassification(
            classification="super_important_customer",
            urgency="high",
            ai_summary="Customer wants priority service.",
        )


def test_invalid_urgency_is_rejected():
    with pytest.raises(ValidationError):
        LeadClassification(
            classification="standard_repair",
            urgency="immediately",
            ai_summary="Repair request.",
        )


def test_extra_ai_fields_are_rejected():
    with pytest.raises(ValidationError):
        LeadClassification(
            classification="quote_request",
            urgency="normal",
            ai_summary="Customer requested a quote.",
            invented_discount="50%",
        )


def test_blank_summary_is_rejected():
    with pytest.raises(ValidationError):
        LeadClassification(
            classification="maintenance",
            urgency="low",
            ai_summary="   ",
        )
